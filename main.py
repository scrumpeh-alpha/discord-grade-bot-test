import os
import discord
from dotenv import load_dotenv
import logging

class MyClient(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.startswith('$hello'):
            print(f"Message from {message.author}: {message.content}")
            await message.channel.send('Hello!')


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
log_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(TOKEN, log_handler=log_handler, log_level=logging.DEBUG)
