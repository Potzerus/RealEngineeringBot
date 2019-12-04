import subprocess as sp
from discord.ext import commands

bot = commands.Bot(command_prefix="!re")

process = sp.Popen(['python', 'Real_Engineering_Bot.py'])
print("Pop")


