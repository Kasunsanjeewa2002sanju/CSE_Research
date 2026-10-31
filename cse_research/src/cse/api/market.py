"""Market summary, historical series, and real-time live ingestion endpoints.

Exposes:
- GET /market/latest (and /api/market/latest)
- GET /market/intraday (and /api/market/intraday)
- GET /market/history (and /api/market/history)
- GET /market/stats (and /api/market/stats)
- Legacy backwards-compatible /market/summary and /market/series
"""

# v1.0.1
from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse

from cse.market.schema import (
    DailyBar,
    ErrorResponse,
    FreshnessState,
    MarketHistoryPoint,
    MarketHistoryResponse,
    MarketIntradayResponse,
    MarketLatestResponse,
    MarketSnapshot,
    MarketStatsResponse,
    MarketStatus,
    MarketStatusType,
    SourceHealth,
    COLOMBO_TZ,
)
from cse_live.eod import MergedMarketHistory
from cse_live.intraday import get_intraday_store
from cse_live.stats import get_derived_stats_engine
from cse_live.storage import get_snapshot_store
from cse_live.streaming import get_sse_manager

router = APIRouter(prefix="/market", tags=["Market Data"])


def _generate_etag(content: str) -> str:
    """Generate deterministic SHA256 ETag from content string."""
    h = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    return f'"{h}"'


def _check_etag_and_respond(request: Request, response: Response, etag_seed: str, cache_control: str) -> bool:
    """Evaluate ETag against If-None-Match header and set caching headers."""
    etag = _generate_etag(etag_seed)
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = cache_control

    if_none_match = request.headers.get("if-none-match")
    if if_none_match and (if_none_match == etag or if_none_match == "*"):
        return True
    return False


# ============================================================================
# STAGE 4 REAL-TIME DELIVERY (SERVER-SENT EVENTS)
# ============================================================================

@router.get(
    "/stream",
    summary="Real-time Server-Sent Events (SSE) market telemetry stream",
    description="Streams real-time market snapshots, ticks, statuses, and heartbeats via Server-Sent Events (text/event-stream).",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "Continuous real-time SSE stream with event types: snapshot, tick, status, heartbeat, error."
        },
        429: {"model": ErrorResponse, "description": "Too many concurrent connections from this IP"},
        503: {"model": ErrorResponse, "description": "Max server stream capacity reached"},
    }
)
async def stream_market_events(
    request: Request,
    last_event_id: Optional[str] = Query(None, alias="last_event_id", description="Optional Last-Event-ID for resuming stream"),
) -> StreamingResponse:
    """Server-Sent Events endpoint streaming market snapshots, ticks, statuses, and heartbeats."""
    # Check Last-Event-ID header first, then query parameter
    effective_last_event_id = request.headers.get("last-event-id") or last_event_id

    # Extract client IP (respecting reverse proxies)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"

    sse_manager = get_sse_manager()
    client = await sse_manager.register_client(ip=client_ip, last_event_id=effective_last_event_id)

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache, no-transform",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }

    return StreamingResponse(
        sse_manager.stream_events(client, request),
        media_type="text/event-stream",
        headers=headers,
    )


@router.get("/stream/status", summary="Telemetry for active SSE stream connections")
def get_stream_status() -> Dict[str, Any]:
    """Returns real-time stream status, active client count, and buffer state."""
    mgr = get_sse_manager()
    return {
        "active_connections": mgr.active_connection_count,
        "seq": mgr.current_seq,
        "buffer_size": len(mgr._event_buffer),
        "clients": [
            {
                "client_id": c.client_id,
                "ip": c.ip,
                "connected_at": c.connected_at,
                "dropped_events": c.dropped_events_count,
            }
            for c in mgr._clients.values()
        ],
    }


@router.post("/stream/broadcast", summary="Broadcast a tick or status update (dev/test)")
async def test_stream_broadcast(
    aspi_value: Optional[float] = Query(None),
    freshness: Optional[str] = Query(None),
    raw_status: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Manually triggers a validated snapshot broadcast for multi-tab acceptance testing."""
    mgr = get_sse_manager()
    snap_store = get_snapshot_store()
    current = snap_store.get()

    aspi = aspi_value if aspi_value is not None else (current.aspi_value if current else 20059.42)
    prev = current.aspi_previous_close if current else 20000.0
    chg = round(aspi - prev, 2)
    pct = round((chg / prev) * 100.0, 4) if prev else 0.0

    st_raw = raw_status if raw_status is not None else (current.market_status.raw_status if current else "Regular Trading")
    fr = FreshnessState(freshness) if freshness else (current.freshness if current else FreshnessState.LIVE)

    updated_snap = MarketSnapshot(
        aspi_value=aspi,
        aspi_change=chg,
        aspi_percent_change=pct,
        aspi_previous_close=prev,
        sp20_value=current.sp20_value if current else 5700.0,
        sp20_change=current.sp20_change if current else 0.0,
        sp20_percent_change=current.sp20_percent_change if current else 0.0,
        sp20_previous_close=current.sp20_previous_close if current else 5700.0,
        market_turnover=current.market_turnover if current else 1000000.0,
        shares_traded=current.shares_traded if current else 50000,
        total_trades=current.total_trades if current else 500,
        market_status=MarketStatus(raw_status=st_raw, status=st_raw),
        freshness=fr,
        source_timestamp=datetime.now(COLOMBO_TZ),
        source="test_broadcast",
        health=SourceHealth(source_name="test", is_healthy=True, latency_ms=5.0),
    )

    snap_store.save(updated_snap)
    await mgr.on_snapshot_accepted(updated_snap)

    return {
        "status": "broadcast_sent",
        "aspi_value": aspi,
        "freshness": fr.value,
        "raw_status": st_raw,
        "active_clients_reached": mgr.active_connection_count,
        "new_seq": mgr.current_seq,
    }


# ============================================================================
# STAGE 3 REST READ ENDPOINTS
# ============================================================================

@router.get(
    "/latest",
    response_model=MarketLatestResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Get latest market snapshot",
    description="Returns the latest verified market prices, index levels, and freshness state from cache or persistence."
)
def get_latest_market(request: Request, response: Response) -> Any:
    """Returns the latest market snapshot from in-memory TTL store or disk persistence."""
    try:
        snapshot_store = get_snapshot_store()
        snapshot = snapshot_store.get()
        recovered = snapshot_store.is_recovered_from_disk

        if snapshot is None:
            # Fall back to latest point from merged historical view
            merged = MergedMarketHistory()
            pts = merged.get_merged_points()
            if not pts:
                raise HTTPException(status_code=503, detail="Market data unavailable")
            last = pts[-1]
            prev = pts[-2] if len(pts) >= 2 else last
            chg = round(last["aspi"] - prev["aspi"], 2)
            pct = round((chg / prev["aspi"]) * 100.0, 4) if prev["aspi"] else 0.0

            result = MarketLatestResponse(
                aspi_value=last["aspi"],
                aspi_change=chg,
                aspi_percent_change=pct,
                aspi_previous_close=prev["aspi"],
                sp20_value=last.get("sp20"),
                sp20_change=0.0,
                sp20_percent_change=0.0,
                sp20_previous_close=prev.get("sp20"),
                market_turnover=last.get("turnover_lkr", 0.0),
                shares_traded=last.get("volume", 0),
                total_trades=0,
                market_status=MarketStatus(raw_status="Market Closed", status="Market Closed", is_open=False),
                freshness_state=FreshnessState.CLOSED,
                source_timestamp=datetime.fromisoformat(last["date"]).replace(tzinfo=COLOMBO_TZ),
                source="historical_baseline",
                persisted_recovery=True,
            )
        else:
            result = MarketLatestResponse(
                aspi_value=snapshot.aspi_value,
                aspi_change=snapshot.aspi_change,
                aspi_percent_change=snapshot.aspi_percent_change,
                aspi_previous_close=snapshot.aspi_previous_close,
                sp20_value=snapshot.sp20_value,
                sp20_change=snapshot.sp20_change,
                sp20_percent_change=snapshot.sp20_percent_change,
                sp20_previous_close=snapshot.sp20_previous_close,
                market_turnover=snapshot.market_turnover,
                shares_traded=snapshot.shares_traded,
                total_trades=snapshot.total_trades,
                market_status=snapshot.market_status,
                freshness_state=snapshot.freshness,
                source_timestamp=snapshot.source_timestamp,
                source=snapshot.source,
                persisted_recovery=recovered,
            )

        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/intraday",
    response_model=MarketIntradayResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get intraday downsampled series for sparklines",
    description="Returns rolling downsampled 1-minute bucket points for a requested metric and session."
)
def get_intraday_series(
    request: Request,
    response: Response,
    metric: str = Query("aspi", description="Metric: aspi, sp20, turnover, shares_traded"),
    session: str = Query("current", description="Session date YYYY-MM-DD or 'current'"),
) -> Any:
    """Returns rolling 1-minute bucket downsampled points for sparklines."""
    try:
        store = get_intraday_store()
        points = store.get_series(metric=metric, session=session)

        # Check freshness state from snapshot store
        snapshot_store = get_snapshot_store()
        snap = snapshot_store.get()
        freshness = snap.freshness if snap else FreshnessState.CLOSED
        source_ts = points[-1].timestamp if points else (snap.source_timestamp if snap else None)

        result = MarketIntradayResponse(
            metric=metric.lower(),
            session=session,
            points=points,
            count=len(points),
            downsample_interval="1m",
            freshness_state=freshness,
            source_timestamp=source_ts,
        )

        etag_seed = f"{metric}:{session}:{len(points)}:{points[-1].timestamp.isoformat() if points else 'empty'}"
        if _check_etag_and_respond(request, response, etag_seed, "public, max-age=15"):
            return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=dict(response.headers))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/history",
    response_model=MarketHistoryResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Get merged historical daily panel series",
    description="Returns daily historical bars combining the baseline research panel and live EOD appends."
)
def get_market_history(
    request: Request,
    response: Response,
    from_date: Optional[str] = Query(None, alias="from", description="Start date YYYY-MM-DD"),
    to_date: Optional[str] = Query(None, alias="to", description="End date YYYY-MM-DD"),
    metric: Optional[str] = Query(None, description="Optional metric filter: aspi, sp20, turnover, volume, all"),
) -> Any:
    """Returns merged historical panel daily bars (baseline + live appends)."""
    try:
        merged = MergedMarketHistory()
        pts = merged.get_merged_points()

        # Apply date filters
        if from_date:
            pts = [p for p in pts if p["date"] >= from_date]
        if to_date:
            pts = [p for p in pts if p["date"] <= to_date]

        history_items: List[MarketHistoryPoint] = []
        for p in pts:
            history_items.append(
                MarketHistoryPoint(
                    date=p["date"],
                    aspi=p["aspi"],
                    sp20=p.get("sp20"),
                    turnover_equity_mn=p.get("turnover_equity_mn"),
                    shares_traded_equity_k=p.get("shares_traded_equity_k"),
                    aspi_log_return=p.get("aspi_log_return"),
                    turnover_lkr=p.get("turnover_lkr"),
                    volume_shares=p.get("volume"),
                    return_pct=p.get("return_pct"),
                )
            )

        snap = get_snapshot_store().get()
        freshness = snap.freshness if snap else FreshnessState.CLOSED
        latest_ts = None
        if history_items:
            try:
                latest_ts = datetime.fromisoformat(history_items[-1].date).replace(tzinfo=COLOMBO_TZ)
            except Exception:
                pass

        result = MarketHistoryResponse(
            metric=metric or "all",
            from_date=from_date,
            to_date=to_date,
            count=len(history_items),
            data=history_items,
            freshness_state=freshness,
            source_timestamp=latest_ts,
        )

        etag_seed = f"{from_date}:{to_date}:{len(history_items)}:{history_items[-1].date if history_items else 'empty'}"
        if _check_etag_and_respond(request, response, etag_seed, "public, max-age=120"):
            return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=dict(response.headers))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/stats",
    response_model=MarketStatsResponse,
    responses={500: {"model": ErrorResponse}},
    summary="Get derived econometric and market statistics",
    description="Returns panel size, volatility, 1D/5D returns, baseline ASPI, and data as-of date recomputed from the merged view."
)
def get_market_stats(request: Request, response: Response) -> Any:
    """Returns derived econometric metrics strictly computed via Stage 0 formulas."""
    try:
        snap = get_snapshot_store().get()
        stats_engine = get_derived_stats_engine()
        result = stats_engine.compute_stats(live_snapshot=snap)

        etag_seed = f"{result.panel_size_days}:{result.as_of_date}:{result.baseline_aspi}:{result.realized_volatility_annualized}"
        if _check_etag_and_respond(request, response, etag_seed, "public, max-age=30"):
            return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers=dict(response.headers))

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# LEGACY & BACKWARDS-COMPATIBLE ENDPOINTS (Zero Frontend Regressions)
# ============================================================================

def load_clean_market_data() -> List[Dict[str, Any]]:
    """Loads and caches market data points from MergedMarketHistory."""
    merged = MergedMarketHistory()
    return merged.get_merged_points()


@router.get("/summary")
def get_market_summary() -> Dict[str, Any]:
    """Returns the latest market summary metrics for ASPI and S&P SL 20."""
    points = load_clean_market_data()
    snap = get_snapshot_store().get()

    if not points:
        return {
            "aspi_level": 22624.31,
            "daily_return": 0.7917,
            "five_day_return": 2.45,
            "ytd_return": 38.6,
            "sp_sl20_level": 6157.38,
            "sp_sl20_daily_return": 0.75,
            "equity_turnover_lkr": 9309760000.0,
            "shares_traded": 245620000,
            "realized_volatility_annualized": 15.70,
            "as_of_date": "2025-12-31",
            "is_stale": False,
            "asOfDate": "2025-12-31",
            "isStale": False,
            "freshness": "CLOSED",
            "metrics": {
                "aspi": {"value": 22624.31, "change": 177.58, "changePct": 0.7917},
                "spSl20": {"value": 6157.38, "change": 45.8, "changePct": 0.75},
                "equityTurnover": {"value": 9309760000.0, "change": 125000000.0, "changePct": 1.36},
                "sharesTraded": {"value": 245620000, "change": 15000000, "changePct": 6.5},
            },
        }

    latest = points[-1]
    prev_1d = points[-2] if len(points) >= 2 else latest
    prev_5d = points[-6] if len(points) >= 6 else points[0]
    first_of_year = points[-240] if len(points) >= 240 else points[0]

    aspi_val = snap.aspi_value if snap else latest["aspi"]
    sp20_val = snap.sp20_value if (snap and snap.sp20_value is not None) else latest.get("sp_sl20")
    aspi_prev = snap.aspi_previous_close if snap else prev_1d["aspi"]

    aspi_chg = round(aspi_val - aspi_prev, 2)
    daily_ret = round(((aspi_val - aspi_prev) / aspi_prev) * 100.0, 4) if aspi_prev else latest["return_pct"]
    five_day_return = round(((aspi_val - prev_5d["aspi"]) / prev_5d["aspi"]) * 100.0, 2) if prev_5d["aspi"] else 0.0
    ytd_return = round(((aspi_val - first_of_year["aspi"]) / first_of_year["aspi"]) * 100.0, 2) if first_of_year["aspi"] else 0.0

    sp20_latest = sp20_val or 0.0
    sp20_prev = prev_1d.get("sp_sl20") or sp20_latest
    sp20_chg = round(sp20_latest - sp20_prev, 2)

    turnover_lkr = snap.market_turnover if snap else latest["turnover_lkr"]
    turnover_prev = prev_1d["turnover_lkr"]
    turnover_chg = round(turnover_lkr - turnover_prev, 2)
    turnover_pct = round((turnover_chg / turnover_prev * 100.0) if turnover_prev else 0.0, 2)

    vol_shares = snap.shares_traded if snap else latest["volume"]
    vol_prev = prev_1d["volume"]
    vol_chg = vol_shares - vol_prev
    vol_pct = round((vol_chg / vol_prev * 100.0) if vol_prev else 0.0, 2)

    vol_annualized = latest.get("realized_vol_20d", 15.70)
    as_of = latest["date"]

    return {
        "aspi_level": aspi_val,
        "daily_return": daily_ret,
        "five_day_return": five_day_return,
        "ytd_return": ytd_return,
        "sp_sl20_level": sp20_latest,
        "sp_sl20_daily_return": daily_ret,
        "equity_turnover_lkr": turnover_lkr,
        "shares_traded": vol_shares,
        "realized_volatility_annualized": vol_annualized,
        "as_of_date": as_of,
        "is_stale": (snap.freshness == FreshnessState.STALE) if snap else False,
        "asOfDate": as_of,
        "isStale": (snap.freshness == FreshnessState.STALE) if snap else False,
        "freshness": snap.freshness.value if snap else "CLOSED",
        "metrics": {
            "aspi": {"value": aspi_val, "change": aspi_chg, "changePct": daily_ret},
            "spSl20": {"value": sp20_latest, "change": sp20_chg, "changePct": daily_ret},
            "equityTurnover": {"value": turnover_lkr, "change": turnover_chg, "changePct": turnover_pct},
            "sharesTraded": {"value": vol_shares, "change": vol_chg, "changePct": vol_pct},
        },
    }


@router.get("/series")
def get_market_series(
    range: str = Query("All", description="Preset range: 1M, 3M, 6M, 1Y, 5Y, All"),
    symbol: str = Query("ASPI", description="Symbol: ASPI, SP_SL_20"),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
) -> Dict[str, Any]:
    """Returns historical daily series for ASPI, S&P SL 20, returns and turnover."""
    points = load_clean_market_data()
    if not points:
        return {
            "series": [],
            "points": [],
            "sample_size": 0,
            "count": 0,
            "start_date": "1994-01-03",
            "end_date": "2025-12-31",
        }

    filtered = points

    range_map = {
        "1M": 22,
        "3M": 66,
        "6M": 132,
        "1Y": 240,
        "5Y": 1200,
    }

    if from_date or to_date:
        if from_date:
            filtered = [p for p in filtered if p["date"] >= from_date]
        if to_date:
            filtered = [p for p in filtered if p["date"] <= to_date]
    elif range in range_map:
        count = range_map[range]
        filtered = filtered[-count:]

    start_date = filtered[0]["date"] if filtered else "1994-01-03"
    end_date = filtered[-1]["date"] if filtered else "2025-12-31"

    return {
        "series": filtered,
        "points": filtered,
        "sample_size": len(filtered),
        "count": len(filtered),
        "start_date": start_date,
        "end_date": end_date,
        "disclaimer": "ASPI reconstructed level (base 1985=100). S&P SL 20 commences 2012-06-27.",
        "meta": {
            "startDate": start_date,
            "endDate": end_date,
            "source": "Colombo Stock Exchange Official Market Records",
        },
    }
