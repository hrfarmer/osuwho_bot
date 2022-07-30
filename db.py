import mysql.connector
import os
from dotenv import load_dotenv
from se_chatstats import ChatStats

load_dotenv()
mysqlhost = os.getenv("MYSQLHOST")
mysqluser = os.getenv("MYSQLUSER")
mysqlpassword = os.getenv("MYSQLPASSWORD")
mysqlport = os.getenv("MYSQLPORT")
mysqldatabase = os.getenv("MYSQLDATABASE")

cs = ChatStats()


class Database:

    def __init__(self):
        print("Connecting to SQL server...")
        self.conn = mysql.connector.connect(
            host=mysqlhost,
            user=mysqluser,
            password=mysqlpassword,
            port=mysqlport,
            database=mysqldatabase
        )
        print("Done")

    @property
    def cursor(self):
        return self.conn.cursor()

    def add_osu_username(self, twitch_user, osu_user):
        cursor = self.cursor
        cursor.execute(
            f"INSERT INTO osu_usernames (twitch_username, osu_username) VALUES('{twitch_user}', '{osu_user}')")
        self.conn.commit()

    def return_osu_username(self, twitch_user):
        cursor = self.cursor
        cursor.execute(
            f"SELECT * FROM osu_usernames WHERE twitch_username = '{twitch_user}'")
        return cursor.fetchone()

    def remove_osu_username(self, twitch_user):
        cursor = self.cursor
        cursor.execute(
            f"DELETE FROM osu_usernames WHERE twitch_username = '{twitch_user}'")
        self.conn.commit()

# lastfm database stuff
    def add_lastfm_username(self, twitch_user, lastfm_user):
        cursor = self.cursor
        cursor.execute(
            f"INSERT INTO lastfm_usernames (twitch_username, lastfm_username) VALUES('{twitch_user}', '{lastfm_user}')")
        self.conn.commit()

    def return_lastfm_username(self, twitch_user):
        cursor = self.cursor
        cursor.execute(
            f"SELECT * FROM lastfm_usernames WHERE twitch_username = '{twitch_user}'")
        return cursor.fetchone()

    def remove_lastfm_username(self, twitch_user):
        cursor = self.cursor
        cursor.execute(
            f"DELETE FROM lastfm_usernames WHERE twitch_username = '{twitch_user}'")
        self.conn.commit()

# chatstats database stuff
    def add_chatters(self):
        cursor = self.cursor
        try:
            cursor.execute("DELETE FROM chatter_leaderboard")
            self.conn.commit()
        except:
            pass

        data = cs.getStats()
        leaderboard = data['chatters']

        for i, person in enumerate(leaderboard, 1):
            twitch_user = person['name']
            messages = person['amount']

            cursor.execute(
                f"INSERT INTO chatter_leaderboard (twitch_username, messages, placement) VALUES ('{twitch_user}', '{messages}', '{i}')")
            self.conn.commit()

    def return_messages(self, twitch_user):
        cursor = self.cursor
        cursor.execute(
            f"SELECT * FROM chatter_leaderboard WHERE twitch_username = '{twitch_user}'")
        return cursor.fetchone()

    def return_top10(self):
        cursor = self.cursor
        cursor.execute(f"SELECT * FROM chatter_leaderboard LIMIT 0, 10")
        return cursor.fetchall()
