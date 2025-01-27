import sqlite3
from typing import List, Optional
import re
import os

DATABASE_NAME = "theo_data.db"  # Database file name


class Database:
    def __init__(self, db_name: str = DATABASE_NAME):
        self.db_name = db_name
        self.conn = None  # Initialize connection to None

    def connect(self):
        """Establishes a connection to the database."""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            # Consider logging the error

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def create_tables(self):
        """Creates the necessary tables if they don't exist."""
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    fid INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    hash TEXT PRIMARY KEY,
                    fid INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    text TEXT NOT NULL,
                    likes INTEGER,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (fid) REFERENCES users(fid)
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nominations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nominator_fid INTEGER NOT NULL,
                    nominee_fid INTEGER NOT NULL,
                    post_hash TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (nominator_fid) REFERENCES users(fid),
                    FOREIGN KEY (nominee_fid) REFERENCES users(fid),
                    FOREIGN KEY (post_hash) REFERENCES posts(hash),
                    UNIQUE (nominator_fid, post_hash)
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS based_creator_of_day (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fid INTEGER UNIQUE NOT NULL,
                    date TEXT UNIQUE NOT NULL,
                    FOREIGN KEY (fid) REFERENCES users(fid)
                )
            """
            )

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"An error occurred while creating tables: {e}")
            # Consider logging the error
        finally:
            self.close()

    def get_user(self, fid: int) -> Optional[dict]:
        """Retrieves a user by their Farcaster ID."""
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM users WHERE fid = ?", (fid,))
            result = cursor.fetchone()
            if result:
                return {"fid": result[0], "username": result[1]}
        except sqlite3.Error as e:
            print(f"An error occurred while retrieving user: {e}")
            # Consider logging the error
        finally:
            self.close()
        return None

    def create_user(self, fid: int, username: str):
        """Creates a new user."""
        if not isinstance(fid, int):
            print(f"Error: Invalid FID format: {fid}. FID must be an integer.")
            return

        if not self.is_valid_username(username):
            print(f"Error: Invalid username format: {username}")
            return

        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO users (fid, username) VALUES (?, ?)", (fid, username))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"Failed to create user: {e}")
            # Consider logging the error
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            # Consider logging the error
        finally:
            self.close()

    def get_post(self, hash: str) -> Optional[dict]:
        """Retrieves a post by its hash."""
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM posts WHERE hash = ?", (hash,))
            result = cursor.fetchone()
            if result:
                return {
                    "hash": result[0],
                    "fid": result[1],
                    "username": result[2],
                    "text": result[3],
                    "likes": result[4],
                    "timestamp": result[5]
                }
        except sqlite3.Error as e:
            print(f"An error occurred while retrieving post: {e}")
            # Consider logging the error
        finally:
            self.close()
        return None

    def create_post(self, fid: int, username: str, text: str, likes: int, timestamp: str, hash: str):
        """Creates a new post."""
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO posts (fid, username, text, likes, timestamp, hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (fid, username, text, likes, timestamp, hash))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"An error occurred while creating post: {e}")
            # Consider logging the error
        finally:
            self.close()

    def record_nomination(self, nominator_fid: int, nominee_fid: int, post_hash: str, timestamp: str):
        """Records a nomination."""
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO nominations (nominator_fid, nominee_fid, post_hash, timestamp)
                VALUES (?, ?, ?, ?)
            """, (nominator_fid, nominee_fid, post_hash, timestamp))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"Failed to record nomination: {e}")
            # Consider logging the error or raising the exception
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            # Consider logging the error
        finally:
            self.close()

    def get_daily_leader(self):
        """
        Retrieves the current "Based Creator of the Day" post from the database.
        """
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT p.* 
                FROM posts p
                JOIN based_creator_of_day b ON p.fid = b.fid
                WHERE b.date = DATE('now')
                ORDER BY p.likes DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                return {
                    "hash": result[0],
                    "fid": result[1],
                    "username": result[2],
                    "text": result[3],
                    "likes": result[4],
                    "timestamp": result[5]
                }
        except sqlite3.Error as e:
            print(f"An error occurred while retrieving daily leader: {e}")
            # Consider logging the error
        finally:
            self.close()
        return None

    def mark_based_creator_of_the_day(self, fid: int):
        """Marks the given user as the 'Based Creator of the Day'."""
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO based_creator_of_day (fid, date) VALUES (?, DATE('now'))", (fid,))
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"Failed to mark based creator of the day: {e}")
            # Consider logging the error
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            # Consider logging the error
        finally:
            self.close()
            
    def get_leaderboard(self) -> List[dict]:
        """
        Retrieves the leaderboard data from the database.
        """
        self.connect()
        try:
            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT username, COUNT(nominee_fid) as points
                FROM nominations
                LEFT JOIN users ON users.fid = nominee_fid
                GROUP BY username
                ORDER BY points DESC
                LIMIT 10
            """
            )
            results = cursor.fetchall()

            leaderboard = []
            for result in results:
                leaderboard.append({"username": result[0], "points": result[1]})
            return leaderboard

        except sqlite3.Error as e:
            print(f"An error occurred while retrieving leaderboard data: {e}")
            # Consider logging the error
            return []  # Return an empty list in case of error
        finally:
            self.close()

    def is_valid_username(self, username: str) -> bool:
        """Checks if a username is valid according to Farcaster rules."""
        return bool(re.fullmatch(r"[a-z0-9]([a-z0-9-]{0,14}[a-z0-9])?", username))
    
    def format_leaderboard(self, leaderboard_data: List[dict]) -> str:
        """Formats the leaderboard data into a string for display."""
        leaderboard_string = "🏆 Top Creators Leaderboard (Based on Nominations):\n\n"
        for i, creator in enumerate(leaderboard_data):
            leaderboard_string += f"{i+1}. @{creator['username']} - {creator['points']} points\n"
        leaderboard_string += f"\nNominate your favorite creators by tagging @{os.getenv('THEO_FARCASTER_USERNAME')} in the comments of their posts!"
        return leaderboard_string
    
    def get_most_liked_posts(self, start_time: str, limit: int = 3) -> List[dict]:
        """
        Retrieves the most liked posts created after a specific time, limited to a certain number.

        Args:
            start_time: The timestamp for the earliest posts to retrieve.
            limit: The maximum number of posts to return.

        Returns:
            A list of dictionaries, each representing a post.
        """
        self.connect()
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT *
                FROM posts
                WHERE timestamp >= ?
                ORDER BY likes DESC
                LIMIT ?
                """,
                (start_time, limit),
            )
            results = cursor.fetchall()

            posts = []
            for result in results:
                posts.append(
                    {
                        "hash": result[0],
                        "fid": result[1],
                        "username": result[2],
                        "text": result[3],
                        "likes": result[4],
                        "timestamp": result[5],
                    }
                )
            return posts

        except sqlite3.Error as e:
            print(f"An error occurred while retrieving most liked posts: {e}")
            return []
        finally:
            self.close()