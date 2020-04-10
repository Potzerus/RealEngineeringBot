import subprocess as sp
from discord.ext import commands
import discord
import builtins

bot = commands.Bot(command_prefix="re!")

process = None  # sp.Popen(['python3', 'Real_Engineering_Bot.py'])
authorized_roles = [431504659060883466, 517700484195418125]

bot.help_command = None


@bot.command()
@commands.has_any_role(*authorized_roles)
async def help(ctx):
    await ctx.send(
        ">>> %sstart --- Starts the Bot\n%sstatus --- Displays Bot Status\n%sterminate --- Terminates the Bot" % (
            bot.command_prefix, bot.command_prefix, bot.command_prefix))


@bot.command()
@commands.is_owner()
async def eval(ctx, expression: str):
    try:
        channel = ctx.channel
        author = ctx.author
        server = ctx.guild
        message = ctx.message
        bot = ctx.bot
        await ctx.send(builtins.eval(
            discord.utils.escape_mentions(expression)))
    except Exception as e:
        await ctx.send(e)


@bot.command()
@commands.is_owner()
async def async_eval(ctx, expression: str):
    try:
        channel = ctx.channel
        author = ctx.author
        server = ctx.guild
        message = ctx.message
        bot = ctx.bot
        await ctx.send(await builtins.eval(
            discord.utils.escape_mentions(expression)))
    except Exception as e:
        await ctx.send(e)


@bot.command()
@commands.has_any_role(*authorized_roles)
async def status(ctx):
    """Displays Bot Status"""
    if process.poll() is None:
        await ctx.channel.send("Currently Running!")
    else:
        await ctx.send("Currently Paused!")


@bot.command()
@commands.has_any_role(*authorized_roles)
async def start(ctx):
    """Starts the Bot"""
    global process
    if process.poll() is None:
        await ctx.channel.send('It\'s already running!')
        return
    process = sp.Popen(['python3', 'Real_Engineering_Bot.py'])
    await ctx.channel.send("Start!")


@bot.command()
@commands.has_any_role(*authorized_roles)
async def terminate(ctx):
    """Terminates the Bot"""
    process.terminate()
    process.wait()
    await ctx.channel.send("Terminated!")
    await ctx.guild.get_channel(517432636944416781).send(
        "%s has terminated the bot(id: %d)" % (ctx.author.name, ctx.author.id))


@bot.command()
@commands.has_any_role(*authorized_roles)
async def ban(ctx, id: int, *, reason: str):
    try:
        target = await bot.fetch_user(id)
        await ctx.guild.ban(target, reason=reason)
    except Exception as e:
        await ctx.channel.send(e)


bot.run(open("RE-Token.txt").read())
