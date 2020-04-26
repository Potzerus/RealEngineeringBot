import json
import discord
from discord.ext import commands
from threading import Event, Thread

bot = commands.Bot(command_prefix="c!")
info = json.loads(open("Info.json").read())
bot.clothes = ["Skirt"]
# Cant get this to work will comment for now
# bot.activity(discord.CustomActivity(name="Use s!help to get started"))

def get_guild(guild_thing):
    id = str(guild_thing.guild.id)
    if id not in info:
        info[id] = {}
    return info[id]


def call_repeatedly(interval, func, *args):
    stopped = Event()

    def loop():
        while not stopped.wait(interval):  # the first call is in `interval` secs
            func(*args)

    Thread(target=loop).start()
    return stopped.set


def save():
    open("Info.json", "w").write(json.dumps(info))

# autosave feature every 300 secs (5 minutes)
# call_repeatedly(300, save)

default_webhook = {"username": "Cephalobot",
                   "avatar_url": "https://cdn.discordapp.com/attachments/278555022646706176/699359432756166716/Cephalobot.png"
                   }


def is_authorized():
    def predicate(ctx):
        guild = get_guild(ctx)
        if "mod roles" in guild:
            mod_roles = guild["mod roles"]
            roles = ctx.author.roles
            for role in roles:
                if role.id in mod_roles:
                    return True
        return False

    return commands.check(predicate)


async def webhook_send(channel_id, embed):
    channel = bot.get_channel(channel_id)
    hooks = await channel.webhooks()
    hook = discord.utils.get(hooks, name='Modshard:' + str(+channel.id))
    if hook is None:
        hook = await channel.create_webhook(name='Modshard:' + str(channel.id))
    guild = get_guild(channel)
    if "webhook" not in guild:
        guild["webhook"] = dict(default_webhook)
    webhook_info = guild["webhook"]
    await hook.send(embed=embed, **webhook_info)


@bot.event
async def on_ready():
    global appli
    appli = await bot.application_info()
    print("Logged in! bot invite: https://discordapp.com/api/oauth2/authorize?client_id=" +
          str(appli.id) + "&permissions=0&scope=bot")


@bot.event
async def on_bulk_message_delete(messages):
    # Logging
    for message in messages:
        await on_message_delete(message)


@bot.event
async def on_message_delete(message):
    # Logging
    guild = get_guild(message.channel)
    if "message log" in guild:
        embed = discord.Embed(color=discord.Color.red())
        embed.title = "Deleted Message"
        embed.add_field(name="Username", value=message.author)
        embed.add_field(name="UserId", value=message.author.id, inline=False)
        embed.add_field(name="Channel", value="<#%d>" % message.channel.id, inline=False)
        embed.add_field(name="Content", value=message.content or "Empty Message", inline=False)
        await webhook_send(get_guild(message.channel)['message log'], embed)


@bot.event
async def on_message_edit(before, after):
    # Logging
    guild = get_guild(before.channel)
    if "message log" in guild and before.content != "" and before.content != after.content:
        embed = discord.Embed(color=discord.Color.blue())
        embed.title = "Edited Message"
        embed.add_field(name="Username", value=after.author)
        embed.add_field(name="UserId", value=after.author.id, inline=False)
        embed.add_field(name="Channel", value="<#%d>" % before.channel.id, inline=False)
        embed.add_field(name="Before", value=before.content or "Message Empty", inline=False)
        embed.add_field(name="After", value=after.content or "Message Empty", inline=False)
        await webhook_send(guild['message log'], embed)


@bot.event
async def on_member_remove(member):
    # Sticky Role
    guild = get_guild(member)
    if "sticky role" in guild and member.guild.get_role(get_guild(member)['sticky role']) in member.roles:
        if "evaders" not in guild:
            guild['evaders'] = []
        guild['evaders'].append(member.id)

    # Logging
    if "join log" in guild:
        embed = discord.Embed(color=discord.Color.orange())
        embed.title = "User Left"
        embed.add_field(name="Username", value=member)
        embed.add_field(name="UserId", value=member.id, inline=False)
        await webhook_send(guild['join log'], embed)


@bot.event
async def on_member_join(member):
    # Sticky Roles
    guild = get_guild(member)
    if "sticky role" in guild and "evaders" in guild and member.id in guild['evaders']:
        await member.add_roles(member.guild.get_role(guild['sticky role']))

    # Logging
    if "join log" in guild:
        embed = discord.Embed(color=discord.Color.blue())
        embed.title = "User Joined"
        embed.add_field(name="Username", value=member)
        embed.add_field(name="UserId", value=member.id, inline=False)
        await webhook_send(guild['join log'], embed)


@bot.group(invoke_without_command=True, aliases=["s"])
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def settings(ctx):
    """Gives you an overview of your current settings"""
    embed = discord.Embed(title="Displaying Settings")
    guild = get_guild(ctx)
    v = None
    if "message log" in guild:
        v = "<#%d>" % guild["message log"]
    embed.add_field(name="Message Log", value=v or "None")
    v = None
    if "join log" in guild:
        v = "<#%d>" % guild["join log"]
    embed.add_field(name="Join Log", value=v or "None")
    v = None
    if "mod roles" in guild:
        v = ""
        for role in guild['mod roles']:
            v += "%s\n" % ctx.guild.get_role(role).name
    embed.add_field(name="Mod Roles", value=v or "None")
    v = None
    if "sticky role" in guild:
        v = ctx.guild.get_role(guild["sticky role"]).name
    embed.add_field(name="Sticky Role", value=v or "None")
    await ctx.send(embed=embed)


@bot.command()
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def reset(ctx, *, arg: str):
    """Let's you reset a configured setting on the bot valid targets are
    mod roles
    basically lets you instantly remove all mod roles from the bot

    message log
    lets you turn off message logging permanently

    join log
    lets you turn off join log permanently

    webhook
    will reset the loggers appearance to its default(same avatar/name as the bot)

    sticky role
    will remove the sticky role

    evaders
    will allow all current evaders to rejoin without having the sticky role back on them
    """
    if arg not in get_guild(ctx):
        await ctx.send("%s is not a valid attribute!" % arg)
        return

    get_guild(ctx).pop(arg)
    await ctx.send("%s has been reset successfully!" % arg)


@bot.command(aliases=["ml"])
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def message_log(ctx, channel: discord.TextChannel):
    """Set the message log channel"""
    get_guild(ctx)["message log"] = channel.id
    await ctx.send("Successfully set the message log channel to %s" % channel.name)


@bot.command(aliases=["jl"])
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def join_log(ctx, channel: discord.TextChannel):
    """Set the join log channel"""
    get_guild(ctx)["join log"] = channel.id
    await ctx.send("Successfully set the join log channel to %s" % channel.name)


@bot.group(invoke_without_command=True, aliases=["mr"])
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def mod_roles(ctx):
    """Display Mod roles"""
    guild = get_guild(ctx)
    if "mod roles" in guild:
        v = ""
        for role in guild['mod roles']:
            v += "\n%s" % ctx.guild.get_role(role).name
        if len(v) == 0:
            v = "\nNone"
    else:
        v = "\nNone"
    await ctx.send("Current modroles:%s" % v)


@mod_roles.command(invoke_without_command=True)
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def add(ctx, role: discord.Role):
    """Add a mod role"""
    guild = get_guild(ctx)
    if "mod roles" not in guild:
        guild["mod roles"] = []
    guild["mod roles"].append(role.id)
    await ctx.send("Successfully added %s to the mod roles!" % role.name)


@mod_roles.command(invoke_without_command=True, aliases=["rem"])
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def remove(ctx, role: discord.Role):
    """Remove a mod role"""
    get_guild(ctx)["mod roles"].remove(role.id)
    await ctx.send("Successfully removed %s from the mod roles!" % role.name)


@bot.group(invoke_without_command=True, aliases=["wh"])
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def webhook(ctx):
    """Shows example webhook"""
    embed = discord.Embed(title="Webhook Example!")
    embed.add_field(name="Sample Text", value="This is what i look like on here!")
    await webhook_send(ctx.channel.id, embed)


@webhook.command()
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def name(ctx, *, arg: str):
    """Set webhook name"""
    guild = get_guild(ctx)
    if "webhook" not in guild:
        guild["webhook"] = dict(default_webhook)
    guild["webhook"]["username"] = arg
    await ctx.send("Updated the webhooks name to %s" % arg)


@webhook.command()
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def avatar(ctx, *, arg: str):
    """Set Webhook avatar"""
    guild = get_guild(ctx)
    if "webhook" not in guild:
        guild["webhook"] = dict(default_webhook)
    guild["webhook"]["avatar_url"] = arg
    await ctx.send("Updated the webhooks avatar to %s" % arg)


@bot.command(aliases=["sr"])
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def sticky_role(ctx, role: discord.Role):
    """Set a sticky role"""
    get_guild(ctx)["sticky role"] = role.id
    await ctx.send("Successfully set %s to be the sticky role" % role.name)


# Debug, done for manual saving
@bot.command(name="save")
@commands.is_owner()
async def save_command(ctx):
    """Owner command: Lets me manually save data"""
    save()


@bot.command()
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def ban(ctx, id: int, *, reason: str = ""):
    try:
        target = await bot.fetch_user(id)
        await ctx.guild.ban(target, reason=reason)
    except Exception as e:
        await ctx.channel.send(e)



bot.run(open("Token.txt").read())
