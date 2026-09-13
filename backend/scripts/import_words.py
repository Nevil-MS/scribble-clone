import json

from app.database.connection import get_connection

def import_words():
    with open("data/words_en_v1.0.0.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    connection = get_connection()
    cursor = connection.cursor()

    for category in data.values():
        for word_length_group in category.values():
            for item in word_length_group:
                word = item["word"]
                word_lengths = item["lens"]


                cursor.execute(
                    """
                    INSERT OR IGNORE INTO words (word, word_lengths, language)
                    VALUES (?, ?, ?)
                    """,
                    (word, str(word_lengths), "en")
                    
                )

    connection.commit()
    connection.close()

if __name__ == "__main__":
    import_words()

# "python -m scripts.import_words" (run from \backend)