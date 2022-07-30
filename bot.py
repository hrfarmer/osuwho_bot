from twitchio.ext import commands
from osu import AsynchronousClient as Client
from get_animes import GetAnime
from last_fm import LastFM
from db import Database
from dotenv import load_dotenv
import time
import openai
import string
import asyncio
import requests
import os
import random
import threading
import cleverbotfree

load_dotenv()

client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')
channel = os.getenv('channel')
redirect_url = os.getenv('redirect_url')
twitch_token = os.getenv('twitch_token')
openai.api_key = os.getenv("OPENAI_API_KEY")
MAL_TOKEN = os.getenv("MAL_TOKEN")
banned_words = ['hentai', 'cum', 'penis', 'sex']


db = Database()
db.add_chatters()
get_anime = GetAnime()
lastfm = LastFM()
animes, animes_lower = get_anime.collect_animes()

client = Client.from_client_credentials(
    client_id, client_secret, redirect_url)


def truncate(n, decimals=0):
    n = n*100
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


async def cbot_chat(input):
    async with cleverbotfree.async_playwright() as p_w:
        c_b = await cleverbotfree.CleverbotAsync(p_w)
        user_input = input
        bot = await c_b.single_exchange(user_input)

        return bot


def online_check():
    global live
    while True:
        r = requests.get(
            "https://beta.decapi.me/twitch/uptime/btmc").text
        if r == "btmc is offline":
            live = False
            time.sleep(30)
        else:
            live = True
            time.sleep(30)


online_thread = threading.Thread(target=online_check)
online_thread.daemon = True


async def openai_request(message):
    response = openai.Completion.create(
        model="text-davinci-002",
        prompt=message,
        temperature=1,
        max_tokens=300,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    ai_text = response['choices'][0]['text']

    content_filter = openai.Completion.create(
        model="content-filter-alpha",
        prompt="<|endoftext|>"+ai_text+"\n--\nLabel:",
        temperature=0,
        max_tokens=1,
        top_p=0,
        logprobs=10
    )

    output_label = content_filter["choices"][0]["text"]
    print(f"AI generated text: {ai_text}")
    return ai_text, output_label

printable = set(string.printable)


class Bot(commands.Bot):

    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        super().__init__(token=twitch_token,
                         prefix='?', initial_channels=[channel])
        self.invis = False
        self.previous_time = None

    async def event_ready(self):

        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    async def event_message(self, message):
        if message.echo:
            return

        # FUNCTIONS THAT DONT START WITH PREFIX
        if message.content.startswith('\x01ACTION @osuwho Which anime is more popular?'):
            if message.author.name == 'hrfarmer_' or message.author.name == 'sheepposubot':
                user_message = message.content[45:]
                animes = user_message.split(' or ')

                anime1 = animes[0]
                anime1.join(filter(lambda x: x in printable, anime1))
                anime1 = anime1.lower()

                anime2 = animes[1]
                anime2.join(filter(lambda x: x in printable, anime2))
                anime2 = anime2.lower()
                anime2 = anime2[:-1]

                time.sleep(2)

                try:
                    anime1_rank = animes_lower.index(anime1)
                    anime2_rank = animes_lower.index(anime2)
                except ValueError:
                    print('guess?')
                    r = random.randint(1, 2)
                    if self.invis == False:
                        self.invis = True
                        return await bot.connected_channels[0].send(f"{r}")
                    else:
                        self.invis = False
                        return await bot.connected_channels[0].send(f"{r} 🤯")

                if anime1_rank > anime2_rank:
                    answer = "2"
                else:
                    answer = "1"

                await queue.put(answer)
            # Print the contents of our message to console...
        print(f"{message.author.name}: {message.content}")

        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)


# Commands

    @commands.command()
    async def die(self, ctx: commands.Context):
        if ctx.message.author.name == "hrfarmer_" or ctx.message.author.name == 'osuwhotest':
            await queue.put("DIESOFCRINGE *dies*")
            exit()
        else:
            await queue.put("PogO YOU ARE NOT WORTHY ENOUGH TO MURDER ME")

    @commands.command()
    async def start(self, ctx: commands.Context):
        await self.send_message(ctx)

    @commands.command()
    async def reload_animes(self, ctx: commands.Context):
        get_anime.collect_animes()
        await queue.put("Anime list reloaded")

    @commands.command()
    async def search_anime_rank(self, ctx: commands.Context):
        message = ctx.message.content[19:]
        message_lower = message.lower()
        print(message_lower)
        try:
            print(message)
            anime_lower = animes_lower.index(message_lower)
            anime_name = animes[anime_lower]
        except ValueError:
            return await queue.put("That anime is not found")

        anime_lower += 1
        await queue.put(f"{anime_name} is at rank {anime_lower}")

    @commands.command()
    async def random_animes(self, ctx: commands.Context):
        try:
            message = int(ctx.message.content[15:])
            message += 1
        except ValueError:
            return await queue.put("Put a number after the command")

        if message > 6:
            return await queue.put("Limited to 5 at a time so you don't burn down chat Stare")

        for i in range(1, message):
            r = random.randint(0, 1000)
            anime = animes[r]
            r += 1
            await queue.put(f"Anime: {anime} | Rank: {r}")

    @commands.command()
    async def list_animes(self, ctx: commands.Context):
        for n, anime in enumerate(animes, 1):
            print(f"{n}: {anime}")

    @commands.command()
    async def recent_anime(self, ctx: commands.Context):
        message = ctx.message.content[14:]
        user_anime = get_anime.get_anime_list(message)

        try:
            title = user_anime['data'][0]['node']['alternative_titles']['en'] if user_anime['data'][
                0]['node']['alternative_titles']['en'] != "" else user_anime['data'][0]['node']['title']
            id = user_anime['data'][0]['node']['id']
            score = user_anime['data'][0]['list_status']['score']
        except:
            return await queue.put("User not found or something broke")

        await queue.put(f"{message}'s recent anime: {title} | Score: {score} 🌟 | Link: https://myanimelist.net/anime/{id}")

    @commands.command()
    async def dink(self, ctx: commands.Context):
        await queue.put("DinkDonk DONK")
        # await self.send_message(ctxx)

    @commands.command()
    async def repeat(self, ctx: commands.Context):
        message = ctx.message.content
        message = message[8:]
        await queue.put(message)

    @commands.command()
    async def aiwebsite(self, ctx: commands.Context):
        await queue.put(f"@{ctx.message.author.name}, https://beta.openai.com/playground?mode=complete")

    @commands.command()
    async def cytube(self, ctx: commands.Context):
        await queue.put(f"@{ctx.message.author.name}, https://cytu.be/r/enyoters")

    @commands.command()
    async def cbot(self, ctx: commands.Context):
        message = ctx.message.content
        message.join(filter(lambda x: x in printable, message))
        message = message[6:]

        cbot_message = await cbot_chat(message)
        await queue.put(f"{cbot_message}")

    @commands.command()
    async def ai(self, ctx: commands.Context):
        return await queue.put("Ai is gone because I have no more openai credits LULW")
        if ctx.message.author.name == "styx_e_clap":
            return await queue.put(f"@{ctx.message.author.name} fuck you you're banned FRICK")

        await queue.put("ppHop Loading (other commands may or may not run after the ai has responded, resend if it doesn't)")
        message = ctx.message.content
        message.join(filter(lambda x: x in printable, message))
        message = message[4:]

        text, content_filter = await openai_request(message)

        if content_filter == "2":
            text = "This is too Susge for twitch chat"

        for banned_word in banned_words:
            if banned_word in text.lower():
                text = "This is too Susge for twitch chat"

        await asyncio.sleep(1)

        length = len(text)
        if length > 475:
            n = 450
            split_text = [text[i:i+n] for i in range(0, len(text), n)]
            for _text in split_text:
                await queue.put(f"@{ctx.message.author.name}, {_text}")
                await asyncio.sleep(1.5)

        else:
            await queue.put(f"@{ctx.message.author.name}, {text}")

    @commands.command()
    async def link(self, ctx: commands.Context):
        self.twitch_username = ctx.message.author.name

        self.osu_username = ctx.message.content
        self.osu_username.join(
            filter(lambda x: x in printable, self.osu_username))
        self.osu_username = self.osu_username[6:]

        try:
            self.yep = db.return_osu_username(self.twitch_username)
            if self.yep != None:
                await queue.put("NOPERS Tssk you can't link more than one account (do ?unlink to remove previous account)")
        except:
            pass

        try:
            self.yep = await client.get_user(key="username", user=self.osu_username)
        except:
            return await queue.put("This is not a valid account")

        try:
            db.add_osu_username(self.twitch_username, self.osu_username)
        except:
            return await queue.put("Failed to link (ping hr man)")

        await queue.put(f"Linked {self.twitch_username} to {self.osu_username}")

    @commands.command()
    async def checkuser(self, ctx: commands.Context):
        self.twitch_username = ctx.message.author.name
        self.osu_username = db.return_osu_username(self.twitch_username)

        if self.osu_username == None:
            return await queue.put("You aren't linked to an osu account!")

        await queue.put(f"@{self.twitch_username}, your linked osu! username is {self.osu_username[1]}")

    @commands.command()
    async def unlink(self, ctx: commands.Context):
        self.twitch_username = ctx.message.author.name
        try:
            self.osu_username = db.return_osu_username(self.twitch_username)
        except:
            return await queue.put("You aren't linked to an account")

        db.remove_osu_username(self.twitch_username)
        await queue.put(f"Unlinked {self.twitch_username} from {self.osu_username[1]}")

    @commands.command()
    async def rs(self, ctx: commands.Context):
        username = ctx.message.content
        username.join(filter(lambda x: x in printable, username))
        username = username[4:]

        if username == "":
            try:
                username = db.return_osu_username(ctx.message.author.name)
                user = await client.get_user(key="username", user=username[1])
                id = user.id
            except:
                return await queue.put("Please link your username with ?link")
        else:
            try:
                user = await client.get_user(key="username", user=username)
            except:
                return await queue.put("Either you did not enter a username or the username entered is incorrect/does not exist.")
            id = user.id

        scores = await client.get_user_scores(
            id, 'recent', '1', 'osu', '1', '0')
        for score in scores:
            accuracy = truncate(score.accuracy, 2)

            if score.passed == True:
                if score.beatmap.status == 'graveyard' or score.beatmap.status == 'wip' or score.beatmap.status == 'pending':
                    s = f"@{ctx.message.author.name} {score.beatmapset.artist} - {score.beatmapset.title} [{score.beatmap.version}]: {score.score} | [{score.statistics.count_300}/{score.statistics.count_100}/{score.statistics.count_50}/{score.statistics.count_miss}] | {accuracy}% | Not ranked (can't get pp) | https://osu.ppy.sh/b/{score.beatmap.id}"
                    print(s)
                    await queue.put(s)
                elif score.beatmap.status == 'loved':
                    s = f"@{ctx.message.author.name} {score.beatmapset.artist} - {score.beatmapset.title} [{score.beatmap.version}]: {score.score} | [{score.statistics.count_300}/{score.statistics.count_100}/{score.statistics.count_50}/{score.statistics.count_miss}] | {accuracy}% | Loved (can't get pp) | https://osu.ppy.sh/b/{score.beatmap.id}"
                    print(s)
                    await queue.put(s)
                elif score.beatmap.status == 'qualified':
                    s = f"@{ctx.message.author.name} {score.beatmapset.artist} - {score.beatmapset.title} [{score.beatmap.version}]: {score.score} | [{score.statistics.count_300}/{score.statistics.count_100}/{score.statistics.count_50}/{score.statistics.count_miss}] | {accuracy}% | Qualified (can't get pp) | https://osu.ppy.sh/b/{score.beatmap.id}"
                    print(s)
                    await queue.put(s)
                else:
                    s = f"@{ctx.message.author.name} {score.beatmapset.artist} - {score.beatmapset.title} [{score.beatmap.version}]: {score.score} | [{score.statistics.count_300}/{score.statistics.count_100}/{score.statistics.count_50}/{score.statistics.count_miss}] | {accuracy}% | {score.pp}pp | https://osu.ppy.sh/b/{score.beatmap.id}"
                    print(s)
                    await queue.put(s)
            else:
                s = f"@{ctx.message.author.name} (FAILED) {score.beatmapset.artist} - {score.beatmapset.title} [{score.beatmap.version}]: {score.score} | [{score.statistics.count_300}/{score.statistics.count_100}/{score.statistics.count_50}/{score.statistics.count_miss}] | {accuracy}% | https://osu.ppy.sh/b/{score.beatmap.id}"
                print(s)
                await queue.put(s)

    # lastfm commands

    @commands.command()
    async def lastfm_link(self, ctx: commands.Context):
        self.twitch_username = ctx.message.author.name

        self.lastfm_username = ctx.message.content
        self.lastfm_username.join(
            filter(lambda x: x in printable, self.lastfm_username))
        self.lastfm_username = self.lastfm_username[13:]

        if self.lastfm_username == "":
            return await queue.put("Your username can't be blank PogO")

        try:
            self.yep = db.return_lastfm_username(self.twitch_username)
            if self.yep != None:
                return await queue.put("NOPERS Tssk you can't link more than one account (do ?lastfm_unlink to remove previous account)")
        except:
            pass

        try:
            db.add_lastfm_username(self.twitch_username, self.lastfm_username)
        except:
            return await queue.put("Failed to link (ping hr man)")

        await queue.put(f"Linked {self.twitch_username} to {self.lastfm_username}")

    @commands.command()
    async def lastfm_checkuser(self, ctx: commands.Context):
        self.twitch_username = ctx.message.author.name
        self.lastfm_username = db.return_lastfm_username(self.twitch_username)

        if self.lastfm_username == None:
            return await queue.put("You aren't linked to a LastFM account!")

        await queue.put(f"@{self.twitch_username}, your linked LastFM username is {self.lastfm_username[1]}")

    @commands.command()
    async def lastfm_unlink(self, ctx: commands.Context):
        self.twitch_username = ctx.message.author.name
        try:
            self.lastfm_username = db.return_lastfm_username(
                self.twitch_username)
        except:
            return await queue.put("You aren't linked to an account")

        db.remove_lastfm_username(self.twitch_username)
        await queue.put(f"Unlinked {self.twitch_username} from {self.lastfm_username[1]}")

    @commands.command()
    async def np(self, ctx: commands.Context):
        username = ctx.message.content
        username.join(filter(lambda x: x in printable, username))
        username = username[4:]

        if username == "":
            try:
                username = db.return_lastfm_username(ctx.message.author.name)
            except:
                return await queue.put(f"Please link a username with ?lastfm_link")

        recent_song = lastfm.getRecentSong(username)

        try:
            song_title = recent_song['recenttracks']['track'][0]['name']
            song_artist = recent_song['recenttracks']['track'][0]['artist']['name']
            song_url = recent_song['recenttracks']['track'][0]['url']
        except:
            return await queue.put("Either that username is invalid, or something broke LULW")

        await queue.put(f"Now playing for {username[1]}: {song_artist} - {song_title} | {song_url}")

    @commands.command()
    async def lastfm_instructions(self, ctx: commands.Context):
        await queue.put(f"@{ctx.message.author.name}, https://pastebin.com/raw/ppReYSDm")

    @commands.command()
    async def lastfm_commands(self, ctx: commands.Context):
        await queue.put(f"@{ctx.message.author.name}, The commands for LastFM are ?np, ?lastfm_link, ?lastfm_unlink, ?lastfm_checkuser, and ?lastfm_instructions")

    # chatstats commands
    @commands.command()
    async def messages_sent(self, ctx: commands.Context):
        username = ctx.message.author.name.lower()
        messages = db.return_messages(username)
        if messages == None:
            return await queue.put(f"@{ctx.message.author.name} You are not on the chatter leaderboard pepePoint")

        await queue.put(f"{messages[0]} is rank {messages[2]} with {messages[1]} messages sent in BTMC (data from https://stats.streamelements.com/c/btmc )")

    @commands.command()
    async def refresh_stats(self, ctx: commands.Context):
        if ctx.message.author.name == 'hrfarmer_' or ctx.message.author.name == 'osuwhotest':
            await queue.put("ppCircle refreshing chatstats")
            db.add_chatters()
            await queue.put("ppL done")
        else:
            await queue.put("PogO you don't have perms for this")

    @commands.command()
    async def lb(self, ctx: commands.Context):
        if ctx.message.author.name == 'styx_e_clap':
            return await queue.put("FRICK im not letting you use this until theres a cooldown")
        top10 = db.return_top10()
        message = ""
        for person in top10:
            name = person[0]
            message = message + \
                f"#{person[2]} {name[:1]}'{name[1:]}: {person[1]} messages | "
        await queue.put(message)

    @commands.command()
    async def roll(self, ctx: commands.Context):
        number = random.randint(1, 1000)
        if self.previous_time == None:
            self.previous_time = time.perf_counter()
            return await queue.put(f"@{ctx.message.author.name}, you rolled {number}")

        current_time = time.perf_counter()
        if current_time - round(self.previous_time, 0) < 5:
            return
        await queue.put(f"@{ctx.message.author.name}, you rolled {number}")
        self.previous_time = current_time


bot = Bot()

queue = asyncio.Queue()


async def send_message():
    previous_mesasge = ""
    while True:
        message = await queue.get()

        if message == previous_mesasge:
            message = message + "ㅤ"

        if live == True:
            print("deadge")
            continue
        else:
            print("he is not live")
            await bot.connected_channels[0].send(message)
            print(f"osuWHO: {message}")
            previous_mesasge = message
            await asyncio.sleep(1.5)

asyncio.run_coroutine_threadsafe(send_message(), bot.loop)
online_thread.start()
asyncio.run(bot.run())

# bot.run() is blocking and will stop execution of any below code here until stopped or closed.
