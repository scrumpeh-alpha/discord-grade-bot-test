import os
import discord
from dotenv import load_dotenv
import random
import logging
import asyncio
from grade_optimizer.grade_optimizer import calculate_optimized_grades

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

    async def grade_calculator(self, message):
        message_data = [i.split(',') for i in message.content.split('\n')[1:]]
        total_weightage = 0
        grade_data = []
        for i in range(len(message_data)):
            try:
                weightage_i = float(message_data[i][0])/100
                grade_i = message_data[i][1]
                if grade_i != 'x':
                    grade_i = float(grade_i)
                    if (grade_i < 0):
                        return await message.reply("Grade cannot be negative!")
                if (weightage_i < 0):
                    return await message.reply("Weightage cannot be negative!")
            except ValueError as ve:
                print(ve)
                return await message.reply("Invalid input. Please try again")
            except Exception as e:
                print(e)
                return await message.reply("Something went wrong. Please try again")

            if len(message_data[i]) == 2:
                grade_data.append([weightage_i, grade_i, f"Item {i+1}"])
            if len(message_data[i]) == 3:
                label = message_data[i][2]
                grade_data.append([weightage_i, grade_i, label])
            total_weightage += weightage_i*100
        if total_weightage < 100:
            return await message.reply("Weightage does not add up to 100. Please try again")
        await message.reply("Reply with your goal grade: ")

        is_valid = lambda x: x.author == message.author and x.content.isdigit()
        round_if_float = lambda x: int(x) if x%1 == 0 else round(x,2)

        try:
            goal_grade_msg = await self.wait_for('message', check=is_valid, timeout=10.0)
        except asyncio.TimeoutError:
            return await message.reply("You took too long to respond. Try again")

        try:
            goal_grade = float(goal_grade_msg.content)
        except ValueError as ve:
            print(ve)
            return await goal_grade_msg.reply("Enter a valid integer")
        optimized_grades = calculate_optimized_grades(grade_data, goal_grade)

        if not optimized_grades.success:
            print(f"{grade_data=}")
            result_msg = "This is the maximum and minimum grade you can get: \n"
            max_grade = 0
            min_grade = 0
            for i in grade_data:
                if i[1] == 'x':
                    max_grade += i[0]*100
                else:
                    max_grade += i[0]*i[1]
                    min_grade += i[0]*i[1]
            result_msg += f"(min\\max): {min_grade}\\{max_grade}"
            return await goal_grade_msg.reply(result_msg)
        else:
            result_msg = "Items with * are predicted grades: \n"
            count = 0
            for i in grade_data:
                weightage_percentage_display = round_if_float(i[0]*100)
                if i[1] == 'x':
                    grade_display = round_if_float(optimized_grades.x[count])
                    # result_msg += f"{i[2]} ({weightage_percentage_display}%)*: {grade_display}\n"
                    count += 1
                else:
                    grade_display = round_if_float(i[1])
                result_msg += f"{i[2]} ({weightage_percentage_display}%): {grade_display}\n"
            await goal_grade_msg.reply(result_msg)

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
            if message.content.strip() == "$gradeCalculate":
                await message.reply("""Input your grades in the following format:
                [Weightage1],[Grade1],[Label1:optional]
                [Weightage2],[Grade2],[Label2:optional]
                    """)
            else:
                await self.grade_calculator(message)


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
log_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
# client.run(TOKEN, log_handler=log_handler, log_level=logging.DEBUG)
client.run(TOKEN)
