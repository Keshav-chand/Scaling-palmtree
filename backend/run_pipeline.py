import json
from pipeline.ingest import fetch_all
from pipeline.clean import clean_and_group
from analysis.feature import compute_all_features
from analysis.repetition import compute_all_repetition
from analysis.flags import compute_all_flags
from analysis.scoring import rank_conversations, top_per_brand
from analysis.aggregation import aggregate_by_brand
from llm.intent import batch_classify
from llm.insights import batch_insights
from config import PROCESSED_DATA_PATH
import os

def run():
    # 1. Load processed data (already built)
    print("Loading processed data...")
    with open(PROCESSED_DATA_PATH) as f:
        structured = json.load(f)
    print(f"Loaded {len(structured)} conversations")

    # 2. Features
    print("\nComputing features...")
    features = compute_all_features(structured)

    # 3. Repetition
    print("\nComputing repetition scores...")
    rep_scores = compute_all_repetition(structured)

    # 4. Flags
    print("\nComputing flags...")
    flags = compute_all_flags(structured, features, rep_scores)

    # 5. Scoring + ranking
    print("\nScoring conversations...")
    scored = rank_conversations(flags, features)
    top15 = top_per_brand(scored, n=15)

    # 6. Aggregation
    print("\nAggregating brand metrics...")
    brand_metrics = aggregate_by_brand(flags, features)

    # 7. Intent classification
    print("\nClassifying intents...")
    intents = batch_classify(structured)

    # 8. LLM insights (only top 15)
    print("\nGenerating LLM insights...")
    insights = batch_insights(top15, structured)

    # 9. Save everything
    os.makedirs("data", exist_ok=True)

    with open("data/scored.json", "w") as f:
        json.dump(scored, f, indent=2)

    with open("data/brand_metrics.json", "w") as f:
        json.dump(brand_metrics, f, indent=2)

    with open("data/intents.json", "w") as f:
        json.dump(intents, f, indent=2)

    print("\n✅ Pipeline complete. All data saved to data/")
    print(f"  Brands: {list(brand_metrics.keys())}")
    for wid, metrics in brand_metrics.items():
        print(f"  {wid}: {metrics['total_conversations']} convs, "
              f"{metrics['frustration_pct']}% frustrated, "
              f"{metrics['drop_off_pct']}% drop-off")

if __name__ == "__main__":
    run()