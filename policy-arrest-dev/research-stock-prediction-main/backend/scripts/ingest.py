import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(base_dir))

from backend.app.news.ingestion import NewsIngestionService

def main():
    print("==================================================")
    print("POLITITRADE LK — RUNNING NEWS INGESTION POLL")
    print("==================================================")
    service = NewsIngestionService()
    inserted = service.run_ingestion()
    print(f"[OK] Ingestion run completed. {inserted} new articles processed and stored.")

if __name__ == "__main__":
    main()
