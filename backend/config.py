import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "helio_intern")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

INTENT_MODEL = "llama-3.1-8b-instant"
INSIGHTS_MODEL = "llama-3.1-8b-instant"

# Cache file paths
DATA_DIR = "data"
PROCESSED_DATA_PATH = f"{DATA_DIR}/processed_data.json"
EMBEDDINGS_PATH = f"{DATA_DIR}/embeddings.pkl"
INTENTS_PATH = f"{DATA_DIR}/intents.json"
INSIGHTS_PATH = f"{DATA_DIR}/insights.json"