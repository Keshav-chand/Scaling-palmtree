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

    # Assign message_id to every text message
    # Sync into timeline so LLM gets correct IDs
    for conv in structured:
        text_msgs = conv.get("messages", [])
        for i, msg in enumerate(text_msgs):
            msg["message_id"] = i

        timeline = conv.get("timeline", [])
        text_idx = 0
        for item in timeline:
            if item["kind"] == "message":
                item["message_id"] = text_idx
                text_idx += 1

    print("\nComputing features...")
    features = compute_all_features(structured)

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

    with open("data/insights.json", "w") as f:
        json.dump(insights, f, indent=2)

    # Generate plain text audit report matching README format exactly
    from utils.formatter import format_all
    conv_by_id_map = {c["conversation_id"]: c for c in structured}
    format_all(llm_flags, conv_by_id_map, output_path="data/audit_report.txt")
    print("  Audit report written to data/audit_report.txt")

    print("\n✅ Pipeline complete.")
    print(f"\nBrand summary:")
    for wid, metrics in brand_metrics.items():
        from pipeline.clean import BRAND_CONTEXT
        brand_name = BRAND_CONTEXT.get(wid, {}).get("name", wid[:12])
        total = metrics['total_conversations']
        flagged = (
            metrics['frustration_count'] +
            metrics['hallucination_count'] +
            metrics['irrelevant_product_count'] +
            metrics['unanswered_question_count'] +
            metrics['context_ignored_count']
        )
        print(f"  {brand_name}: {total} convs | "
              f"frustration {metrics['frustration_pct']}% | "
              f"unanswered {metrics['unanswered_question_pct']}% | "
              f"context_ignored {metrics['context_ignored_pct']}% | "
              f"{flagged} total flags")


if __name__ == "__main__":
    run()