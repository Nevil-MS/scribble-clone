from .connection import get_connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            word_id INTEGER PRIMARY KEY,
            word TEXT NOT NULL,
            word_lengths TEXT NOT NULL,
            language TEXT NOT NULL,
            UNIQUE(word, language)   
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_words (
            word_id INTEGER PRIMARY KEY,
            room_id TEXT NOT NULL,
            word TEXT NOT NULL,
            word_lengths TEXT NOT NULL,
            UNIQUE(room_id, word)
        )
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()

# "python -m app.database.init_db" (run from \backend)