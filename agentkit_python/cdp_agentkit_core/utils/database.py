# agentkit_python/utils/database.py
import sqlite3
from typing import List, Optional

DATABASE_NAME = "theo_data.db"  # Database file name

def create_tables():
    """Creates the necessary tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            fid INTEGER PRIMARY KEY,  
            username TEXT UNIQUE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            hash TEXT PRIMARY KEY,
            fid INTEGER,
            username TEXT,
            text TEXT,
            likes INTEGER,
            timestamp TEXT,
            FOREIGN KEY (fid) REFERENCES users(fid)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nominations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nominator_fid INTEGER,
            nominee_fid INTEGER,
            post_hash TEXT,
            timestamp TEXT,
            FOREIGN KEY (nominator_fid) REFERENCES users(fid),
            FOREIGN KEY (nominee_fid) REFERENCES users(fid),
            FOREIGN KEY (post_hash) REFERENCES posts(hash)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS based_creator_of_day (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fid INTEGER UNIQUE,
            date TEXT UNIQUE,
            FOREIGN KEY (fid) REFERENCES users(fid)
        )
    """)

    conn.commit()
    conn.close()

def get_user(fid: int) -> Optional[dict]:
    """Retrieves a user by their Farcaster ID."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE fid = ?", (fid,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"fid": result[0], "username": result[1]}
    return None

def create_user(fid: int, username: str):
    """Creates a new user."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (fid, username) VALUES (?, ?)", (fid, username))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"User with FID {fid} already exists.")
    finally:
        conn.close()

def get_post(hash: str) -> Optional[dict]:
    """Retrieves a post by its hash."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE hash = ?", (hash,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "hash": result[0],
            "fid": result[1],
            "username": result[2],
            "text": result[3],
            "likes": result[4],
            "timestamp": result[5]
        }
    return None

def create_post(fid: int, username: str, text: str, likes: int, timestamp: str, hash: str):
    """Creates a new post."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO posts (fid, username, text, likes, timestamp, hash)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (fid, username, text, likes, timestamp, hash))
    conn.commit()
    conn.close()

def record_nomination(nominator_fid: int, nominee_fid: int, post_hash: str, timestamp: str):
    """Records a nomination."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO nominations (nominator_fid, nominee_fid, post_hash, timestamp)
            VALUES (?, ?, ?, ?)
        """, (nominator_fid, nominee_fid, post_hash, timestamp))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Nomination already exists.")
    finally:
        conn.close()

def get_daily_leader():
    """
    Retrieves the current "Based Creator of the Day" post from the database.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.* 
        FROM posts p
        JOIN based_creator_of_day b ON p.fid = b.fid
        WHERE b.date = DATE('now')
        ORDER BY p.likes DESC
        LIMIT 1
    """)
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "hash": result[0],
            "fid": result[1],
            "username": result[2],
            "text": result[3],
            "likes": result[4],
            "timestamp": result[5]
        }
    return None

def mark_based_creator_of_the_day(fid: int):
    """Marks the given user as the 'Based Creator of the Day'."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO based_creator_of_day (fid, date) VALUES (?, DATE('now'))", (fid,))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Based Creator of the Day for today already exists.")
    finally:
        conn.close()

def get_leaderboard() -> List[dict]:
    """
    Retrieves the leaderboard data from the database.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # This is a simplified example. You might need a more complex query to calculate points
    # based on nominations and other factors.
    cursor.execute("""
        SELECT u.username, COUNT(n.nominee_fid) as points
        FROM users u
        LEFT JOIN nominations n ON u.fid = n.nominee_fid
        GROUP BY u.username
        ORDER BY points DESC
        LIMIT 10
    """)
    results = cursor.fetchall()
    conn.close()

    leaderboard = []
    for result in results:
        leaderboard.append({"username": result[0], "points": result[1]})
    return leaderboard

# Initialize the database tables when the module is imported
create_tables()