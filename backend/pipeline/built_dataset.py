import json
import os
from pipeline.ingest import fetch_all
from pipeline.clean import clean_and_group
from config import PROCESSED_DATA_PATH

def build():
    print("Fetching from MongoDB...")
    conversations, messages = fetch_all()
    print(f"Fetched {len(conversations)} conversations, {len(messages)} messages")

    print("Cleaning and structuring...")
    structured = clean_and_group(conversations, messages)
    print(f"Structured {len(structured)} non-empty conversations")

    os.makedirs("data", exist_ok=True)
    with open(PROCESSED_DATA_PATH, "w") as f:
        json.dump(structured, f, indent=2, default=str)

    print(f"Saved to {PROCESSED_DATA_PATH}")
    return structured

if __name__ == "__main__":
    build()