from pathlib import Path
import sqlite3

DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "word.db"

def get_connection():
    return sqlite3.connect(DATABASE_PATH)