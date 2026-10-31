"""Historical News and CAR SQLite Database Module for Colombo Stock Exchange.

Provides storage, schema initialization, and query interfaces for:
- news_history: Historical news headlines with event classification and CAR returns
- aspi_prices: Daily ASPI closing prices and 1-day percentage returns
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from cse.utils.config import find_project_root


def get_default_db_path() -> Path:
    """Resolve default SQLite database path in <project_root>/data/cse_history.db."""
    root = find_project_root()
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "cse_history.db"


def get_db_connection(db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
    """Create or return an SQLite connection configured with Row factory."""
    target_path = Path(db_path) if db_path is not None else get_default_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Union[str, Path]] = None) -> Path:
    """Initialize database tables and indexes if they do not exist.
    
    Tables created:
    - news_history: id, headline, published_at, source, event_category, stage,
                    car_1d, car_2d, car_5d, car_10d, aspi_return_1d, aspi_return_5d
    - aspi_prices: date, close, return_1d
    """
    target_path = Path(db_path) if db_path is not None else get_default_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    conn = get_db_connection(target_path)
    try:
        cursor = conn.cursor()

        # 1. News History Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS news_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                headline TEXT NOT NULL,
                published_at TEXT NOT NULL,
                source TEXT,
                event_category TEXT,
                stage TEXT,
                car_1d REAL,
                car_2d REAL,
                car_5d REAL,
                car_10d REAL,
                aspi_return_1d REAL,
                aspi_return_5d REAL
            )
            """
        )

        # 2. ASPI Prices Table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS aspi_prices (
                date TEXT PRIMARY KEY,
                close REAL NOT NULL,
                return_1d REAL
            )
            """
        )

        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_published_at ON news_history(published_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_event_category ON news_history(event_category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_aspi_prices_date ON aspi_prices(date)")

        conn.commit()
    finally:
        conn.close()

    return target_path


def insert_news(
    news: Union[Dict[str, Any], List[Dict[str, Any]], pd.DataFrame],
    db_path: Optional[Union[str, Path]] = None,
) -> int:
    """Insert one or multiple news records into the news_history table.
    
    Parameters
    ----------
    news : Dict, List[Dict], or pd.DataFrame
        Record(s) containing fields:
        headline, published_at, source, event_category, stage,
        car_1d, car_2d, car_5d, car_10d, aspi_return_1d, aspi_return_5d
    db_path : Optional[str | Path]
        Path to SQLite database file.

    Returns
    -------
    int
        Number of rows inserted.
    """
    init_db(db_path)

    if isinstance(news, pd.DataFrame):
        records = news.to_dict(orient="records")
    elif isinstance(news, dict):
        records = [news]
    else:
        records = list(news)

    if not records:
        return 0

    rows_to_insert = []
    for r in records:
        rows_to_insert.append(
            (
                r.get("headline"),
                str(r.get("published_at")),
                r.get("source"),
                r.get("event_category"),
                r.get("stage"),
                r.get("car_1d"),
                r.get("car_2d"),
                r.get("car_5d"),
                r.get("car_10d"),
                r.get("aspi_return_1d"),
                r.get("aspi_return_5d"),
            )
        )

    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT INTO news_history (
                headline, published_at, source, event_category, stage,
                car_1d, car_2d, car_5d, car_10d, aspi_return_1d, aspi_return_5d
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows_to_insert,
        )
        conn.commit()
    finally:
        conn.close()

    return len(rows_to_insert)


def get_all_news(
    db_path: Optional[Union[str, Path]] = None,
    as_dataframe: bool = False,
) -> Union[List[Dict[str, Any]], pd.DataFrame]:
    """Retrieve all news records from news_history table.
    
    Parameters
    ----------
    db_path : Optional[str | Path]
        Path to SQLite database file.
    as_dataframe : bool
        If True, returns pandas DataFrame; else returns list of dictionaries.

    Returns
    -------
    List[Dict[str, Any]] or pd.DataFrame
    """
    init_db(db_path)

    conn = get_db_connection(db_path)
    try:
        if as_dataframe:
            return pd.read_sql_query("SELECT * FROM news_history ORDER BY id ASC", conn)
        else:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM news_history ORDER BY id ASC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()


def insert_aspi_prices(
    prices: Union[List[Dict[str, Any]], pd.DataFrame],
    db_path: Optional[Union[str, Path]] = None,
) -> int:
    """Insert or replace daily ASPI prices in aspi_prices table.
    
    Parameters
    ----------
    prices : List[Dict] or pd.DataFrame
        Rows with 'date', 'close', and optional 'return_1d'.
    db_path : Optional[str | Path]
        Path to SQLite database.

    Returns
    -------
    int
        Number of rows upserted.
    """
    init_db(db_path)

    if isinstance(prices, pd.DataFrame):
        records = prices.to_dict(orient="records")
    else:
        records = list(prices)

    if not records:
        return 0

    rows_to_insert = []
    for r in records:
        d = str(r["date"])[:10]  # format YYYY-MM-DD
        c = float(r["close"])
        ret = r.get("return_1d")
        ret_val = float(ret) if ret is not None and not pd.isna(ret) else None
        rows_to_insert.append((d, c, ret_val))

    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.executemany(
            """
            INSERT OR REPLACE INTO aspi_prices (date, close, return_1d)
            VALUES (?, ?, ?)
            """,
            rows_to_insert,
        )
        conn.commit()
    finally:
        conn.close()

    return len(rows_to_insert)


def get_aspi_range(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db_path: Optional[Union[str, Path]] = None,
    as_dataframe: bool = False,
) -> Union[List[Dict[str, Any]], pd.DataFrame]:
    """Retrieve ASPI daily prices within an optional date range.
    
    Parameters
    ----------
    start_date : Optional[str]
        Start date (inclusive) in 'YYYY-MM-DD' format.
    end_date : Optional[str]
        End date (inclusive) in 'YYYY-MM-DD' format.
    db_path : Optional[str | Path]
        Path to SQLite database.
    as_dataframe : bool
        If True, returns pandas DataFrame; else returns list of dictionaries.

    Returns
    -------
    List[Dict[str, Any]] or pd.DataFrame
    """
    init_db(db_path)

    query = "SELECT date, close, return_1d FROM aspi_prices WHERE 1=1"
    params: List[Any] = []

    if start_date is not None:
        query += " AND date >= ?"
        params.append(str(start_date)[:10])

    if end_date is not None:
        query += " AND date <= ?"
        params.append(str(end_date)[:10])

    query += " ORDER BY date ASC"

    conn = get_db_connection(db_path)
    try:
        if as_dataframe:
            return pd.read_sql_query(query, conn, params=params)
        else:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()
