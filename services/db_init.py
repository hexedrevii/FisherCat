import sqlite3
import sys


def drop_tables(conn: sqlite3.Connection):
  '''
    Drops all tables in the database. This is ONLY meant for the development branch, and should not be called in production.
  '''

  if not conn:
    print('ERROR: No connection provided.', file=sys.stderr)
    return False

  try:
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table_name in tables:
      cursor.execute(f'DROP TABLE IF EXISTS {table_name[0]};')
      print(f'Dropped table: {table_name[0]}')

    conn.commit()
    return True
  except sqlite3.Error as e:
    print(f'ERROR: Failed to drop tables: {e}', file=sys.stderr)
    return False


def initialize_database(conn: sqlite3.Connection):
  if not conn:
    print("ERROR: No connection provided.", file=sys.stderr)
    return False

  try:
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guild (
            id INTEGER PRIMARY KEY
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS member (
            id INTEGER PRIMARY KEY
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guildmember (
            guildid INTEGER NOT NULL,
            memberid INTEGER NOT NULL,

            coins INTEGER DEFAULT 0,

            xp INTEGER DEFAULT 0,
            xpstep INTEGER DEFAULT 1,
            xpnext INTEGER DEFAULT 30,

            level INTEGER DEFAULT 1,

            lastclaimed TEXT DEFAULT '1970-01-01 02:00:00',

            PRIMARY KEY (guildid, memberid),
            FOREIGN KEY (guildid) REFERENCES guild(id) ON DELETE CASCADE,
            FOREIGN KEY (memberid) REFERENCES member(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    print("Tables created successfully.")
    return True

  except sqlite3.Error as e:
    print(f"ERROR: Could not create default tables: {e}", file=sys.stderr)
    return False
