# Table called osu_usernames

import sqlite3

class Database:

    def __init__(self):
        self.conn = sqlite3.connect('database.db')
        self.cursor = self.conn.cursor()

    def add_username(self, twitch_user, osu_user):
        cursor = self.cursor
        cursor.execute(f"INSERT INTO osu_usernames (twitch_username, osu_username) VALUES('{twitch_user}', '{osu_user}')")
        self.conn.commit()
    
    def return_username(self, twitch_user):
        cursor = self.cursor
        cursor.execute(f"SELECT * FROM osu_usernames WHERE twitch_username = '{twitch_user}'")
        return cursor.fetchone()
