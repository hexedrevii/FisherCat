
class db_service:
    def __init__(self, connection):
        self.connection = connection

    def enroll_guild(self, guild_id: int) -> None:
      '''
      Enrolls a guild in the database.
      '''
      try:
        cursor = self.connection.cursor()

        # Check if the guild is already there.
        guild_exists = cursor.execute("SELECT * FROM guild WHERE id = ?", (guild_id,)).fetchone()
        if not guild_exists is None:
           return

        cursor.execute("INSERT OR IGNORE INTO guild (id) VALUES (?)", (guild_id,))
        self.connection.commit()

        print("Enrolled guild: ", guild_id)
      except Exception as e:
        print(f"Error enrolling guild {guild_id}: {e}")
