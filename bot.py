import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import random
import logging
import asyncio
from grade_optimizer.grade_optimizer import calculate_optimized_grades
from colors import bold, red, blue, magenta, cyan

async def random_number_game(message):
    answer = random.randint(1,10)
    is_correct = lambda msg: msg.author == message.author and msg.content.isdigit()

    try:
        guess = await bot.wait_for('message', check=is_correct, timeout=5.0)
    except asyncio.TimeoutError:
        return await message.reply(f"You took too long to respond. It was {answer}")

    while guess.content != str(answer):
        distance: int = abs(answer - int(guess.content))
        if distance > int(guess.content)//2:
            distance = int(guess.content)//2
        await guess.reply(f"Wrong guess! Try again (hint: the number is at least {distance} number(s) away).")
        try:
            guess = await bot.wait_for('message', check=is_correct, timeout=5.0)
        except asyncio.TimeoutError:
            return await message.reply(f"You took too long to respond. It was {answer}")

    await guess.reply("Correct Answer!")

async def show_error(ctx, title, text):
    # Embed template
    error_embed = discord.Embed(
        title="Grade Optimizer - "+title,
        description="Error: " + text,
        color=discord.Color.red()
    )
    error_embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    # error_embed.add_field(name=name, value=value)

    return await ctx.reply(embed=error_embed)



async def get_inputs_from_user(ctx: commands.Context, message_data: list):
    total_weightage = 0
    grade_data = []
    for i in range(len(message_data)):
        try:
            weightage_i = float(message_data[i][0])/100
            grade_i = message_data[i][1]
            if grade_i != 'x':
                grade_i = float(grade_i)
                if (grade_i < 0):
                    return await show_error(ctx, title="Grade Error", text="Grade cannot be negative!")
            if (weightage_i < 0):
                return await show_error(ctx, title="Weight Error", text="Weightage cannot be negative!")
        except ValueError as ve:
            print(ve)
            return await show_error(ctx, title="Value Error", text="Invalid input. Please try again")
        except Exception as e:
            print(e)
            return await show_error(ctx, title="Error", text="Something went wrong. Please try again")

        if len(message_data[i]) == 2:
            grade_data.append([weightage_i, grade_i, f"Item {i+1}"])
        if len(message_data[i]) == 3:
            label = message_data[i][2]
            grade_data.append([weightage_i, grade_i, label])
        total_weightage += weightage_i*100

    if total_weightage < 100:
        return await show_error(ctx, title="Weightage Error", text="Weightage does not add up to 100. Please try again")

    is_valid = lambda x: x.author == ctx.author and x.content.isdigit()

    # await ctx.reply("Reply with your goal grade: ")
    goal_grade_embed = discord.Embed(
        title="Grade Optimizer",
        description="Reply with your goal grade:",
        color=discord.Color.blue()
    )
    goal_grade_embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    await ctx.reply(embed=goal_grade_embed)

    try:
        goal_grade_msg = await bot.wait_for('message', check=is_valid, timeout=10.0)
    except asyncio.TimeoutError:
        return await show_error(ctx, name="Timeout Error",value="You took too long to respond. Try again")

    return grade_data, goal_grade_msg


async def grade_calculator(ctx: commands.Context):
    message_data = [i.split(',') for i in ctx.message.content.split('\n')[1:]]

    result_embed = discord.Embed(
        title="Grade Optimizer",
        description="Result of grade optimized.",
        color=discord.Color.blue()
    )
    result_embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)

    round_if_float = lambda x: int(x) if round(x,2) % 1 == 0 else round(x,2)

    user_inputs = await get_inputs_from_user(ctx, message_data)
    # if return type is a discord message, that means it must be an error
    # TODO: Come up with better way
    if type(user_inputs) == discord.Message:
        return
    grade_data, goal_grade_msg = user_inputs

    try:
        goal_grade = float(goal_grade_msg.content)
    except ValueError as ve:
        print(ve)
        return await show_error(goal_grade, name="Error", value="Enter a valid integer")

    optimized_grades = calculate_optimized_grades(grade_data, goal_grade)

    if not optimized_grades.success:
        result_title = "This is the maximum and minimum grade you can get:"
        result_msg = "```ansi\n"
        max_grade = 0
        min_grade = 0
        for i in grade_data:
            if i[1] == 'x':
                max_grade += i[0]*100
            else:
                max_grade += i[0]*i[1]
                min_grade += i[0]*i[1]
        # result_msg += f"(min\\max): {min_grade}\\{max_grade}"
        result_msg += bold(red("Min:")) + blue(f"\t{min_grade}") + '\n\n'
        result_msg += bold(red("Max:")) + cyan(f"\t{max_grade}") + '```'

        result_embed.add_field(name=result_title, value=result_msg)
        return await goal_grade_msg.reply(embed=result_embed)
    else:
        result_title = "Items bolded are predicted grades:"
        result_msg = "```ansi\n"
        count = 0
        # Justify-length for output according to the label with biggest size
        justify_length = max([len(i[2]) for i in grade_data]) + 14      # Extra spacing
        for i in grade_data:
            weightage_percentage_display = round_if_float(i[0]*100)
            if i[1] == 'x':
                grade_display = str(round_if_float(optimized_grades.x[count]))
                label = f"{i[2]} ({weightage_percentage_display}%)*:"
                result_msg += bold(red(label))
                result_msg += bold(blue(grade_display.rjust(justify_length - len(label)))) + '\n\n'
                count += 1
            else:
                grade_display = str(round_if_float(i[1]))
                label = f"{i[2]} ({weightage_percentage_display}%):"
                result_msg += magenta(label)
                result_msg += cyan(grade_display.rjust(justify_length - len(label))) + '\n\n'
        result_embed.add_field(name=result_title, value=result_msg+"```")
        return await goal_grade_msg.reply(embed=result_embed)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
log_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="$",intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command(name="random")
async def random_start(ctx):
    await ctx.reply("Random game started. Pick a number between 1-10")
    await random_number_game(ctx)

@bot.command(name="gradeOpt")
async def grade_optimize(ctx, opts: str):
    if opts == 'help':
        embedVar = discord.Embed(title="Grade Optimizer", description="This bot optimizes your grades.", color=0x00bbff)
        embedVar.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
        embedVar.add_field(name="Input Format", value="""Input your grades in the following format:
        [Weightage1],[Grade1],[Label1:optional]
        [Weightage2],[Grade2],[Label2:optional]
        """, inline=False)
        await ctx.reply(embed=embedVar)
    else:
        await grade_calculator(ctx)



# async def on_message(self, message):
#     if message.author == self.user:
#         return
#     if message.content.startswith('$hello'):
#         print(f"Message from {message.author}: {message.content}")
#         await message.channel.send('Hello!')
#     if message.content.startswith('$random'):
#         await message.reply("Random game started. Pick a number between 1-10")
#         await self.random_number_game(message)
#     if message.content.startswith('$gradeOptimize'):
#         if message.content.strip() == "$gradeOptimize":
#             embedVar = discord.Embed(title="Grade Optimizer", description="This bot optimizes your grades.", color=0x00bbff)
#             embedVar.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
#             embedVar.add_field(name="Input Format", value="""Input your grades in the following format:
#             [Weightage1],[Grade1],[Label1:optional]
#             [Weightage2],[Grade2],[Label2:optional]
#             """, inline=False)
#             # await message.reply("""Input your grades in the following format:
#             # [Weightage1],[Grade1],[Label1:optional]
#             # [Weightage2],[Grade2],[Label2:optional]
#             #     """)
#             await message.reply(embed=embedVar)
#         else:
#             await self.grade_calculator(message)

# client = MyClient(intents=intents)
# client.run(TOKEN, log_handler=log_handler, log_level=logging.DEBUG)
# client.run(TOKEN)

bot.run(TOKEN)
