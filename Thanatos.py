import subprocess as sp
from discord.ext import commands

bot = commands.Bot(command_prefix="re!")

process = sp.Popen(['python3', 'Real_Engineering_Bot.py'])
print('pop')


@bot.command()
async def status(ctx):
    if process.poll() is None:
        await ctx.channel.send("None")
    else:
        await ctx.send(process.poll())


@bot.command()
async def start(ctx):
    if ctx.author.id == 125660719323676672:
        global process
        process = sp.Popen(['python', 'Real_Engineering_Bot.py'])
        await ctx.channel.send("Start!")


@bot.command()
async def terminate(ctx):
    if ctx.author.id == 125660719323676672:
        process.terminate()
        process.wait()
        await ctx.channel.send("Terminated!")


bot.run(open("RE-Token.txt").read())
