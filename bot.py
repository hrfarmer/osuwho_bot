from numpy import empty
import twitchio
from twitchio.ext import commands
from osu import AsynchronousClient as Client
from get_animes import GetAnime
from db import Database
from dotenv import load_dotenv
import time
import openai
import string
import asyncio
import os
import sys
import random
import cleverbotfree

load_dotenv()

client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')
redirect_url = os.getenv('redirect_url')
twitch_token = os.getenv('twitch_token')
openai.api_key = os.getenv("OPENAI_API_KEY")
MAL_TOKEN = os.getenv("MAL_TOKEN")

banned_words = ['hentai', 'cum', 'penis', 'sex']

db = Database()
get_anime = GetAnime()
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
                         prefix='?', initial_channels=['btmc'])
        self.queue = asyncio.Queue()
        self.invis = False

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    async def event_message(self, message):
        if message.echo:
            return
        # HOW TO SEND MESSAGES
        # await bot.connected_channels[0].send('what')
        if message.content.startswith('\x01ACTION @osuwho Which anime is more popular?'):
            user_message = message.content[45:]
            animes = user_message.split(' or ')

            anime1 = animes[0]
            anime1.join(filter(lambda x: x in printable, anime1))
            anime1 = anime1.lower()

            anime2 = animes[1]
            anime2.join(filter(lambda x: x in printable, anime2))
            anime2 = anime2.lower()
            anime2 = anime2[:-1]

            anime1_rank = animes_lower.index(anime1)
            anime2_rank = animes_lower.index(anime2)

            time.sleep(2)

            if anime1_rank > anime2_rank:
                answer = "2"
            else:
                answer = "1"

            if self.invis == False:
                await bot.connected_channels[0].send(f"{answer}")
                self.invis = True
            else:
                await bot.connected_channels[0].send(f"{answer} 🤯")
                self.invis = False
            # Print the contents of our message to console...
        print(f"{message.author.name}: {message.content}")

        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)

    async def send_message(self, ctx: commands.Context):
        while True:
            if self.queue.empty():
                return
            m = await self.queue.get()
            print(m)
            await ctx.send(m)
            await asyncio.sleep(1.5)


# Commands


    @commands.command()
    async def die(self, ctx: commands.Context):
        if ctx.message.author.name == "hrfarmer_" or ctx.message.author.name == 'osuwhotest':
            await ctx.send("DIESOFCRINGE *dies*")
            exit()
        else:
            await ctx.send("PogO YOU ARE NOT WORTHY ENOUGH TO MURDER ME")

    @commands.command()
    async def ac(self, ctx: commands.Context):
        await ctx.send("!ac")

    @commands.command()
    async def start(self, ctx: commands.Context):
        await self.send_message(ctx)

    @commands.command()
    async def test(self, ctx: commands.Context):
        message = '@osuwho Which anime is more popular? Princess Connect! Re: Dive or Persona 5 The Animation'
        message = message[37:]
        animes = message.split(' or ')
        print(animes)

    @commands.command()
    async def reload_animes(self, ctx: commands.Context):
        get_anime.collect_animes()
        await ctx.send("Anime list reloaded")

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
            return await ctx.send("That anime is not found")

        anime_lower += 1
        await ctx.send(f"{anime_name} is at rank {anime_lower}")

    @commands.command()
    async def random_animes(self, ctx: commands.Context):
        r1 = random.randint(0, 1000)
        r2 = random.randint(0, 1000)

        anime1 = animes[r1]
        anime2 = animes[r2]
        r1 += 1
        r2 += 2

        await ctx.send(f"Anime 1: {anime1} Rank: {r1}")
        await asyncio.sleep(1.5)
        await ctx.send(f"Anime 2: {anime2} Rank: {r2}")

    @commands.command()
    async def list_animes(self, ctx: commands.Context):
        for n, anime in enumerate(animes, 1):
            print(f"{n}: {anime}")

    @commands.command()
    async def dink(self, ctx: commands.Context):
        await self.queue.put("DinkDonk DONK")
        # await self.send_message(ctx)

    @commands.command()
    async def repeat(self, ctx: commands.Context):
        message = ctx.message.content
        message = message[8:]
        await ctx.send(message)

    @commands.command()
    async def roll(self, ctx: commands.Context):
        number = random.randint(1, 1000)
        await ctx.send(f"@{ctx.message.author.name}, you rolled {number}")

    @commands.command()
    async def aiwebsite(self, ctx: commands.Context):
        await ctx.send(f"@{ctx.message.author.name}, https://beta.openai.com/playground?mode=complete")

    @commands.command()
    async def cytube(self, ctx: commands.Context):
        await ctx.send(f"@{ctx.message.author.name}, https://cytu.be/r/enyoters")

    @commands.command()
    async def cbot(self, ctx: commands.Context):
        message = ctx.message.content
        message.join(filter(lambda x: x in printable, message))
        message = message[6:]

        cbot_message = await cbot_chat(message)
        await ctx.send(f";cbot {cbot_message}")

    @commands.command()
    async def ai(self, ctx: commands.Context):

        return await ctx.send("Sadge ran out of free trial for openai, no more generation sorry")
        if ctx.message.author.name == "styx_e_clap":
            return await ctx.send(f"@{ctx.message.author.name} fuck you you're banned FRICK")

        await ctx.send("ppHop Loading (other commands may or may not run after the ai has responded, resend if it doesn't)")
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
                await ctx.send(f"@{ctx.message.author.name}, {_text}")
                await asyncio.sleep(1.5)

        else:
            await ctx.send(f"@{ctx.message.author.name}, {text}")

    @commands.command()
    async def link(self, ctx: commands.Context):
        self.twitch_username = ctx.message.author.name

        self.osu_username = ctx.message.content
        self.osu_username.join(
            filter(lambda x: x in printable, self.osu_username))
        self.osu_username = self.osu_username[6:]

        try:
            self.yep = db.return_username(self.twitch_username)
            if self.yep != None:
                await ctx.send("NOPERS Tssk you can't link more than one account (do ?unlink to remove previous account)")
        except:
            pass

        try:
            self.yep = await client.get_user(key="username", user=self.osu_username)
        except:
            return await ctx.send("This is not a valid account")

        try:
            db.add_username(self.twitch_username, self.osu_username)
        except:
            return await ctx.send("Failed to link (ping hr man)")

        await ctx.send(f"Linked {self.twitch_username} to {self.osu_username}")

    @commands.command()
    async def checkuser(self, ctx: commands.Context):
        self.twitch_username = ctx.message.author.name
        self.osu_username = db.return_username(self.twitch_username)

        if self.osu_username == None:
            return await ctx.send("You aren't linked to an osu account!")

        await ctx.send(f"@{self.twitch_username}, your linked osu! username is {self.osu_username[1]}")

    @commands.command()
    async def unlink(self, ctx: commands.Context):
        self.twitch_username = ctx.message.author.name
        try:
            self.osu_username = db.return_username(self.twitch_username)
        except:
            return await ctx.send("You aren't linked to an account")

        db.remove_username(self.twitch_username)
        await ctx.send(f"Unlinked {self.twitch_username} from {self.osu_username[1]}")

    @commands.command()
    async def rs(self, ctx: commands.Context):
        username = ctx.message.content
        username.join(filter(lambda x: x in printable, username))
        username = username[4:]

        if username == "":
            try:
                username = db.return_username(ctx.message.author.name)
                user = await client.get_user(key="username", user=username[1])
                id = user.id
            except:
                return await ctx.send("Please link your username with ?link")
        else:
            try:
                user = await client.get_user(key="username", user=username)
            except:
                return await ctx.send("Either you did not enter a username or the username entered is incorrect/does not exist.")
            id = user.id

        scores = await client.get_user_scores(
            id, 'recent', '1', 'osu', '1', '0')
        for score in scores:
            accuracy = truncate(score.accuracy, 2)

            if score.passed == True:
                if score.beatmap.status == 'graveyard' or score.beatmap.status == 'wip' or score.beatmap.status == 'pending':
                    s = f"@{ctx.message.author.name} {score.beatmapset.artist} - {score.beatmapset.title} [{score.beatmap.version}]: {score.score} | [{score.statistics.count_300}/{score.statistics.count_100}/{score.statistics.count_50}/{score.statistics.count_miss}] | {accuracy}% | Not ranked (can't get pp) | https://osu.ppy.sh/b/{score.beatmap.id}"
                    print(s)
                    await ctx.send(s)
                elif score.beatmap.status == 'loved':
                    s = f"@{ctx.message.author.name} {score.beatmapset.artist} - {score.beatmapset.title} [{score.beatmap.version}]: {score.score} | [{score.statistics.count_300}/{score.statistics.count_100}/{score.statistics.count_50}/{score.statistics.count_miss}] | {accuracy}% | Loved (can't get pp) | https://osu.ppy.sh/b/{score.beatmap.id}"
                    print(s)
                    await ctx.send(s)
                elif score.beatmap.status == 'qualified':
                    s = f"@{ctx.message.author.name} {score.beatmapset.artist} - {score.beatmapset.title} [{score.beatmap.version}]: {score.score} | [{score.statistics.count_300}/{score.statistics.count_100}/{score.statistics.count_50}/{score.statistics.count_miss}] | {accuracy}% | Qualified (can't get pp) | https://osu.ppy.sh/b/{score.beatmap.id}"
                    print(s)
                    await ctx.send(s)
                else:
                    s = f"@{ctx.message.author.name} {score.beatmapset.artist} - {score.beatmapset.title} [{score.beatmap.version}]: {score.score} | [{score.statistics.count_300}/{score.statistics.count_100}/{score.statistics.count_50}/{score.statistics.count_miss}] | {accuracy}% | {score.pp}pp | https://osu.ppy.sh/b/{score.beatmap.id}"
                    print(s)
                    await ctx.send(s)
            else:
                s = f"@{ctx.message.author.name} (FAILED) {score.beatmapset.artist} - {score.beatmapset.title} [{score.beatmap.version}]: {score.score} | [{score.statistics.count_300}/{score.statistics.count_100}/{score.statistics.count_50}/{score.statistics.count_miss}] | {accuracy}% | https://osu.ppy.sh/b/{score.beatmap.id}"
                print(s)
                await ctx.send(s)


bot = Bot()
asyncio.run(bot.run())

# bot.run() is blocking and will stop execution of any below code here until stopped or closed.
