import json
import os
from analysis.feature import compute_all_features
from analysis.scoring import rank_conversations, top_per_brand
from analysis.aggregation import aggregate_by_brand
from llm.conversation_analyzer import batch_analyze
from llm.intent import batch_classify
from llm.insights import batch_insights
from config import PROCESSED_DATA_PATH


def run():
    print("Loading processed data...")
    with open(PROCESSED_DATA_PATH) as f:
        structured = json.load(f)
    print(f"Loaded {len(structured)} conversations")

    # Assign message_id = index to every message
    for conv in structured:
        for i, msg in enumerate(conv.get("messages", [])):
            msg["message_id"] = i

    print("\nComputing features...")
    features = compute_all_features(structured)

    # LLM analyzer replaces all keyword flag logic
    # Delete data/llm_flags.json to force a re-run
    print("\nRunning LLM conversation analyzer...")
    llm_flags = batch_analyze(structured)

    print("\nScoring conversations...")
    scored = rank_conversations(llm_flags)
    top15 = top_per_brand(scored, n=15)

    print("\nAggregating brand metrics...")
    brand_metrics = aggregate_by_brand(llm_flags, features)

    print("\nClassifying intents...")
    intents = batch_classify(structured)

    print("\nGenerating LLM insights...")
    insights = batch_insights(top15, structured)

    os.makedirs("data", exist_ok=True)

    with open("data/scored.json", "w") as f:
        json.dump(scored, f, indent=2)

    with open("data/brand_metrics.json", "w") as f:
        json.dump(brand_metrics, f, indent=2)

    with open("data/intents.json", "w") as f:
        json.dump(intents, f, indent=2)

    print("\n✅ Pipeline complete.")
    for wid, metrics in brand_metrics.items():
        print(f"  {wid}: {metrics['total_conversations']} convs, "
              f"{metrics['frustration_pct']}% frustrated")


if __name__ == "__main__":
    run()