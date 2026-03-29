import json
from analysis.feature import compute_all_features
from analysis.repetition import compute_all_repetition
from analysis.flags import compute_all_flags
from analysis.aggregation import aggregate_by_brand

# Load processed data
with open("data/processed_data.json") as f:
    data = json.load(f)

# Compute features, repetition, flags
features = compute_all_features(data)
rep_scores = compute_all_repetition(data)
flags = compute_all_flags(data, features, rep_scores)

# Overall stats
print(f"Features computed: {len(features)}")
print(f"Repetition scores: {len(rep_scores)}")
print(f"Flags computed: {len(flags)}")
print(f"Frustration flags: {sum(1 for f in flags if f['frustration'])}")
print(f"Low quality flags: {sum(1 for f in flags if f['low_quality_response'])}")
print(f"Hallucination flags: {sum(1 for f in flags if f['hallucination'])}")

# Brand-level stats
print("\n--- Brand Level Metrics ---")
metrics = aggregate_by_brand(flags, features)

for wid, m in metrics.items():
    print(
        f"{wid[:8]}: "
        f"frustration={m['frustration_count']}, "
        f"low_quality={m['low_quality_count']}, "
        f"drop_offs={m['drop_offs']}"
    )