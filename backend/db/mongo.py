from pymongo import MongoClient
from config import MONGODB_URI, DB_NAME

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]

conversations_col = db["conversations"]
messages_col = db["messages"]