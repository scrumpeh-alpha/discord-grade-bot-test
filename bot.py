import os
import discord
from dotenv import load_dotenv
import random
import logging
import asyncio

class MyClient(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}")

    async def random_number_game(self, message):
        answer = random.randint(1,10)
        is_correct = lambda msg: msg.author == message.author and msg.content.isdigit()

        try:
            guess = await self.wait_for('message', check=is_correct, timeout=5.0)
        except asyncio.TimeoutError:
            return await message.reply(f"You took too long to respond. It was {answer}")

        while guess.content != str(answer):
            distance: int = abs(answer - int(guess.content))
            if distance > int(guess.content)//2:
                distance = int(guess.content)//2
            await guess.reply(f"Wrong guess! Try again (hint: the number is at least {distance} number(s) away).")
            try:
                guess = await self.wait_for('message', check=is_correct, timeout=5.0)
            except asyncio.TimeoutError:
                return await message.reply(f"You took too long to respond. It was {answer}")

        await guess.reply("Correct Answer!")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.content.startswith('$hello'):
            print(f"Message from {message.author}: {message.content}")
            await message.channel.send('Hello!')
        if message.content.startswith('$random'):
            await message.reply("Random game started. Pick a number between 1-10")
            await self.random_number_game(message)
        if message.content.startswith('$gradeCalculate'):
            await message.reply("""Input your grades in the following format:
            [Weightage1],[Grade1],[Label1:optional]
            [Weightage2],[Grade2],[Label2:optional]
            """)
            await self.grade_calculator(message)


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
log_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
# client.run(TOKEN, log_handler=log_handler, log_level=logging.DEBUG)
client.run(TOKEN)
