from .connection import get_connection

def get_random_words(count: int, language: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT word_id, word, word_lengths, language
        FROM words
        WHERE language = ?
        ORDER BY RANDOM()
        LIMIT ?
        """,
        (language, count)
    )

    words = cursor.fetchall()

    connection.close()

    return words