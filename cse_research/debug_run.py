import os
import sys
import tempfile
import shutil

PROJECT_DIR = r"d:\SLIIT\YEAR 04\Research\NEW Dev\cse_research"
os.chdir(PROJECT_DIR)
sys.path.insert(0, os.path.join(PROJECT_DIR, "src"))

mpl_dir = os.path.join(PROJECT_DIR, ".matplotlib")
os.makedirs(mpl_dir, exist_ok=True)
os.environ["MPLCONFIGDIR"] = mpl_dir

from datetime import datetime
from cse.market.schema import MarketSnapshot, MarketStatus, MarketStatusType, FreshnessState, SourceHealth, COLOMBO_TZ
from cse_live.config import IngestionConfig
from cse_live.storage import LatestSnapshotStore

scratch_dir = os.path.join(PROJECT_DIR, "tests", "_test_scratch")
os.makedirs(scratch_dir, exist_ok=True)
temp_dir = tempfile.mkdtemp(dir=scratch_dir)
persist_file = os.path.join(temp_dir, "last_snapshot.json")
config = IngestionConfig(persistence_file_path=persist_file)

print("Step 1: Instantiating store1...")
store1 = LatestSnapshotStore(config)
print("Step 1 done")

now_colombo = datetime.now(COLOMBO_TZ)
snap = MarketSnapshot(
    aspi_value=22624.31,
    aspi_change=177.58,
    aspi_percent_change=0.7917,
    aspi_previous_close=22446.73,
    sp20_value=6157.38,
    sp20_change=45.80,
    sp20_percent_change=0.75,
    sp20_previous_close=6111.58,
    market_turnover=9309760000.0,
    shares_traded=245620000,
    total_trades=18450,
    market_status=MarketStatus(
        raw_status="Regular Trading",
        status=MarketStatusType.REGULAR_TRADING,
        is_open=True,
        timestamp=now_colombo,
    ),
    freshness=FreshnessState.LIVE,
    source_timestamp=now_colombo,
    source="rest_api",
    health=SourceHealth(
        source_name="rest_api",
        is_healthy=True,
        latency_ms=120.5,
    ),
)

print("Step 2: store1.save()...")
store1.save(snap)
print("Step 2 done")

print("Step 3: store1.get()...")
in_mem = store1.get()
print("Step 3 done:", in_mem.aspi_value)

print("Step 4: Instantiating store2...")
store2 = LatestSnapshotStore(config)
print("Step 4 done")

print("Step 5: store2.get()...")
restarted = store2.get()
print("Step 5 done:", restarted.aspi_value)

shutil.rmtree(temp_dir)
print("ALL DONE SUCCESSFULLY!")
