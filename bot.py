from twitchio.ext import commands
from osu import AsynchronousClient as Client
from db import Database
from dotenv import load_dotenv
import time
import openai
import string
import asyncio
import os
import sys
import random

load_dotenv()

client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')
redirect_url = os.getenv('redirect_url')
twitch_token = os.getenv('twitch_token')
openai.api_key = os.getenv("OPENAI_API_KEY")

messages = []

db = Database()

client = Client.from_client_credentials(
    client_id, client_secret, redirect_url)


def truncate(n, decimals=0):
    n = n*100
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier


async def openai_request(message):
    response = openai.Completion.create(
        model="text-davinci-002",
        prompt=message,
        temperature=0.7,
        max_tokens=175,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    text = response['choices'][0]['text']
    return text

printable = set(string.printable)


class Bot(commands.Bot):

    def __init__(self):
        # Initialise our Bot with our access token, prefix and a list of channels to join on boot...
        # prefix can be a callable, which returns a list of strings or a string...
        # initial_channels can also be a callable which returns a list of strings...
        super().__init__(token=twitch_token,
                         prefix='?', initial_channels=['btmc'])

    async def event_ready(self):
        # Notify us when everything is ready!
        # We are logged in and ready to chat and use commands...
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')

    async def event_message(self, message):
        # Messages with echo set to True are messages sent by the bot...
        # For now we just want to ignore them...
        if message.echo:
            return

        # Print the contents of our message to console...
        print(f"{message.author.name}: {message.content}")

        # Since we have commands and are overriding the default `event_message`
        # We must let the bot know we want to handle and invoke our commands...
        await self.handle_commands(message)


# Commands


    @commands.command()
    async def die(self, ctx: commands.Context):
        if ctx.message.author.name == "hrfarmer_" or ctx.message.author.name == 'osuwhotest':
            await ctx.send("DIESOFCRINGE *dies*")
            exit()
        else:
            await ctx.send("PogO YOU ARE NOT WORTHY ENOUGH TO MURDER ME")

    @commands.command()
    async def dink(self, ctx: commands.Context):
        await ctx.send("DinkDonk DONK")

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
    async def ai(self, ctx: commands.Context):
        await ctx.send("ppHop Loading")
        message = ctx.message.content
        message.join(filter(lambda x: x in printable, message))
        message = message[4:]

        text = await openai_request(message)
        await asyncio.sleep(1)
        length = len(text)
        if length > 500:
            n = 470
            split_text = [text[i:i+n] for i in range(0, len(text), n)]
            for _text in split_text:
                await ctx.send(_text)
                await asyncio.sleep(1.5)

        else:
            await ctx.send(text)
            print(text)

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
            return await ctx.send("Either you did not enter a username or the username entered is incorrect/does not exist.")

        try:
            db.add_username(self.twitch_username, self.osu_username)
        except:
            return await ctx.send("Failed to link (ping hr man)")

        await ctx.send(f"Linked {self.twitch_username} to {self.osu_username}")

    @commands.command()
    async def checkuser(self, ctx: commands.Context):
        self.twitch_username = ctx.message.author.name

        self.osu_username = db.return_username(self.twitch_username)
        await ctx.send(f"@{self.twitch_username}, your linked osu! username is {self.osu_username[1]}")

    @commands.command()
    async def unlink(self, ctx: commands.Context):
        self.twitch_username = ctx.message.author.name

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
bot.run()
# bot.run() is blocking and will stop execution of any below code here until stopped or closed.
