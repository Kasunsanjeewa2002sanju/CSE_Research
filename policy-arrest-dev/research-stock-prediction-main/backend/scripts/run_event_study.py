import sys
from pathlib import Path

# Add project root to path
base_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(base_dir))

from backend.app.data.event_loader import EventDataLoader

def main():
    print("==================================================")
    print("POLITITRADE LK — RUNNING FULL HISTORICAL EVENT STUDY")
    print("==================================================")
    
    loader = EventDataLoader()
    study_df = loader.get_event_study_results(force_recompute=True)
    
    print(f"\n[OK] Event study completed successfully for {len(study_df)} events.")
    print("\nSummary Statistics by Event Family:")
    for fam, group in study_df.groupby("event_family"):
        print(f"\n--- {fam} (N = {len(group)}) ---")
        print(f"  Mean CAR[0, +1]:  {group['car_0_1'].mean()*100:+.2f}%")
        print(f"  Mean CAR[0, +5]:  {group['car_0_5'].mean()*100:+.2f}%")
        print(f"  Mean CAR[0, +20]: {group['car_0_20'].mean()*100:+.2f}%")
        print(f"  Impact Direction: {dict(group['impact_direction'].value_counts())}")

    print("\nTop 5 Largest Positive Reactions (CAR 5d):")
    for _, r in study_df.sort_values("car_0_5", ascending=False).head(5).iterrows():
        print(f"  {r['aligned_date']} | {r['event_id']} | {r['title'][:40]} | CAR 5d: {r['car_0_5']*100:+.2f}%")

    print("\nTop 5 Largest Negative Reactions (CAR 5d):")
    for _, r in study_df.sort_values("car_0_5", ascending=True).head(5).iterrows():
        print(f"  {r['aligned_date']} | {r['event_id']} | {r['title'][:40]} | CAR 5d: {r['car_0_5']*100:+.2f}%")

if __name__ == "__main__":
    main()
