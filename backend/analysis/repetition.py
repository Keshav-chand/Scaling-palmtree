import pickle
import os
from sentence_transformers import SentenceTransformer, util
from config import EMBEDDINGS_PATH

model = None

def get_model():
    global model
    if model is None:
        print("Loading sentence-transformer model...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
    return model

def compute_repetition(conv):
    user_msgs = [m["text"] for m in conv["messages"] if m["sender"] == "user" and m.get("text")]

    if len(user_msgs) < 2:
        return 0.0

    m = get_model()
    embeddings = m.encode(user_msgs, convert_to_tensor=True)

    scores = []
    for i in range(len(embeddings) - 1):
        score = util.cos_sim(embeddings[i], embeddings[i+1]).item()
        scores.append(score)

    return round(sum(scores) / len(scores), 4)

def compute_all_repetition(structured_convs):
    # Cache embeddings
    if os.path.exists(EMBEDDINGS_PATH):
        print("Loading cached embeddings...")
        with open(EMBEDDINGS_PATH, "rb") as f:
            return pickle.load(f)

    print("Computing repetition scores...")
    results = {}
    for conv in structured_convs:
        results[conv["conversation_id"]] = compute_repetition(conv)

    with open(EMBEDDINGS_PATH, "wb") as f:
        pickle.dump(results, f)

    print(f"Saved embeddings cache to {EMBEDDINGS_PATH}")
    return results