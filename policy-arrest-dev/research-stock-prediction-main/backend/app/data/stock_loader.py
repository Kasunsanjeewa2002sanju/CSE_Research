import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.data.trading_calendar import TradingCalendar

class StockDataLoader:
    """Loads, cleans, validates, and manages CSE historical market datasets."""
    
    def __init__(self, stock_dir: Optional[Path] = None):
        self.stock_dir = stock_dir or settings.STOCK_DATASET_DIR
        self.artifacts_dir = settings.ARTIFACT_DIR / "clean"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_path = self.artifacts_dir / "cleaned_stock_data.parquet"
        self.csv_fallback_path = settings.DATA_PROCESSED_DIR / "cleaned_stock_data.csv"
        self._df: Optional[pd.DataFrame] = None
        self._calendar: Optional[TradingCalendar] = None

    def load_stock_data(self, force_reload: bool = False) -> pd.DataFrame:
        """Loads cleaned stock dataset from Parquet/CSV or processes from raw files."""
        if self._df is not None and not force_reload:
            return self._df

        # 1. Check if clean parquet exists
        if not force_reload and self.parquet_path.exists():
            try:
                logger.info(f"Loading cleaned stock dataset from {self.parquet_path}")
                self._df = pd.read_parquet(self.parquet_path)
                self._df["Date"] = pd.to_datetime(self._df["Date"]).dt.strftime("%Y-%m-%d")
                self._calendar = TradingCalendar(self._df["Date"].tolist())
                return self._df
            except Exception as e:
                logger.warning(f"Failed to read parquet ({e}), attempting fallback...")

        # 2. Check if clean CSV fallback exists
        if not force_reload and self.csv_fallback_path.exists():
            try:
                logger.info(f"Loading cleaned stock dataset from {self.csv_fallback_path}")
                self._df = pd.read_csv(self.csv_fallback_path)
                self._df["Date"] = pd.to_datetime(self._df["Date"]).dt.strftime("%Y-%m-%d")
                # Save to parquet for fast subsequent loads
                self.save_cleaned_data(self._df)
                self._calendar = TradingCalendar(self._df["Date"].tolist())
                return self._df
            except Exception as e:
                logger.warning(f"Failed to read processed CSV ({e}), processing raw...")

        # 3. Process raw Excel datasets
        self._df = self.process_raw_stock_data()
        self.save_cleaned_data(self._df)
        self._calendar = TradingCalendar(self._df["Date"].tolist())
        return self._df

    def process_raw_stock_data(self) -> pd.DataFrame:
        """Process raw CSE Excel indices and market statistics files."""
        stock_indices_path = self.stock_dir / "07Market Indices - Daily.xls"
        stock_stats_path = self.stock_dir / "11Market Statistics-Daily.xls"

        logger.info(f"Parsing raw market indices from {stock_indices_path}")
        df_raw = pd.read_excel(stock_indices_path, sheet_name="Index", header=None)
        
        row3 = list(df_raw.iloc[3])
        row4 = list(df_raw.iloc[4])
        
        col_names = ["Date", "ASPI", "MPI", "SP_SL20"]
        for idx in range(4, df_raw.shape[1]):
            s_name = row3[idx] if pd.notnull(row3[idx]) else row4[idx]
            if pd.isnull(s_name) or str(s_name).strip() == "" or str(s_name) == "nan":
                s_name = f"Sector_Col_{idx}"
            else:
                s_name = str(s_name).strip().replace(" ", "_").replace("&", "and").replace(",", "")
            col_names.append(s_name)
            
        df_market = df_raw.iloc[5:].copy()
        df_market.columns = col_names[:df_market.shape[1]]
        
        # Clean Date
        df_market["Date"] = pd.to_datetime(df_market["Date"], errors="coerce")
        df_market = df_market.dropna(subset=["Date"]).copy()
        df_market["Date"] = df_market["Date"].dt.strftime("%Y-%m-%d")
        
        # Numeric conversions
        for col in [c for c in df_market.columns if c != "Date"]:
            df_market[col] = pd.to_numeric(df_market[col], errors="coerce")
            
        # Sort and deduplicate
        df_market = df_market.sort_values("Date").drop_duplicates(subset=["Date"]).reset_index(drop=True)
        
        # Clean Statistics (Turnover, Volume, Trades, Market Cap)
        if stock_stats_path.exists():
            logger.info(f"Merging statistics from {stock_stats_path}")
            df_stats_raw = pd.read_excel(stock_stats_path, sheet_name=0, header=None)
            stats_df = pd.DataFrame({
                "Date": pd.to_datetime(df_stats_raw.iloc[5:, 0], errors="coerce").dt.strftime("%Y-%m-%d"),
                "Turnover_Equity_Mn": pd.to_numeric(df_stats_raw.iloc[5:, 4].astype(str).str.replace(",", "").str.replace(" ", "").replace("-", np.nan), errors="coerce"),
                "Shares_Traded_Thousand": pd.to_numeric(df_stats_raw.iloc[5:, 8].astype(str).str.replace(",", "").str.replace(" ", "").replace("-", np.nan), errors="coerce"),
                "Trades_Count": pd.to_numeric(df_stats_raw.iloc[5:, 9].astype(str).str.replace(",", "").str.replace(" ", "").replace("-", np.nan), errors="coerce"),
                "Market_Cap_Mn": pd.to_numeric(df_stats_raw.iloc[5:, 10].astype(str).str.replace(",", "").str.replace(" ", "").replace("-", np.nan), errors="coerce"),
            }).dropna(subset=["Date"]).drop_duplicates(subset=["Date"])
            
            df_market = pd.merge(df_market, stats_df, on="Date", how="left")

        # Returns
        df_market["ASPI_Daily_Return"] = df_market["ASPI"].pct_change()
        if "SP_SL20" in df_market.columns:
            df_market["SP_SL20_Daily_Return"] = df_market["SP_SL20"].pct_change()

        return df_market

    def save_cleaned_data(self, df: pd.DataFrame) -> None:
        """Persist cleaned data to Parquet and CSV."""
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        try:
            df.to_parquet(self.parquet_path, index=False)
            logger.info(f"Saved Parquet artifact to {self.parquet_path}")
        except Exception as e:
            logger.error(f"Failed to write parquet: {e}")
            
        settings.DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        try:
            df.to_csv(self.csv_fallback_path, index=False)
            logger.info(f"Saved CSV fallback to {self.csv_fallback_path}")
        except Exception as e:
            logger.error(f"Failed to write CSV: {e}")

    def get_trading_calendar(self) -> TradingCalendar:
        """Get trading calendar instance for date operations."""
        if self._calendar is None:
            df = self.load_stock_data()
            self._calendar = TradingCalendar(df["Date"].tolist())
        return self._calendar

    def get_inventory_report(self) -> Dict[str, Any]:
        """Produce inventory report for historical market datasets."""
        df = self.load_stock_data()
        aspi_valid = df["ASPI"].dropna()
        sp20_valid = df["SP_SL20"].dropna() if "SP_SL20" in df.columns else pd.Series([], dtype=float)
        
        sectors = [c for c in df.columns if c not in ["Date", "ASPI", "MPI", "SP_SL20", "Turnover_Equity_Mn", "Shares_Traded_Thousand", "Trades_Count", "Market_Cap_Mn", "ASPI_Daily_Return", "SP_SL20_Daily_Return"] and not c.startswith("Sector_Col")]

        return {
            "total_trading_days": len(df),
            "date_range": {
                "start": df["Date"].min(),
                "end": df["Date"].max()
            },
            "primary_index": {
                "symbol": "ASPI",
                "name": "All Share Price Index",
                "valid_observations": len(aspi_valid),
                "missing_values": int(df["ASPI"].isna().sum()),
                "earliest_date": df.dropna(subset=["ASPI"])["Date"].min(),
                "latest_date": df.dropna(subset=["ASPI"])["Date"].max(),
                "latest_close": float(aspi_valid.iloc[-1]) if len(aspi_valid) > 0 else None
            },
            "secondary_index": {
                "symbol": "SP_SL20",
                "name": "S&P Sri Lanka 20",
                "valid_observations": len(sp20_valid),
                "earliest_date": df.dropna(subset=["SP_SL20"])["Date"].min() if len(sp20_valid) > 0 else None,
                "latest_date": df.dropna(subset=["SP_SL20"])["Date"].max() if len(sp20_valid) > 0 else None,
                "latest_close": float(sp20_valid.iloc[-1]) if len(sp20_valid) > 0 else None
            },
            "available_sectors": sectors,
            "has_turnover_data": bool("Turnover_Equity_Mn" in df.columns and (df["Turnover_Equity_Mn"].notna().sum() > 0)),
            "data_quality_warnings": [
                "Early years (pre-2000) have sparser sector coverage.",
                "Turnover data is tracked primarily from 2001 onward.",
                "S&P SL20 begins from 2012 onward."
            ]
        }
