import json
import discord
from discord.ext import commands
from threading import Event, Thread

bot = commands.Bot(command_prefix="s!")
info = json.loads(open("Info.json").read())


def get_guild(guild_thing):
    return info[str(guild_thing.guild.id)]


def call_repeatedly(interval, func, *args):
    stopped = Event()

    def loop():
        while not stopped.wait(interval):  # the first call is in `interval` secs
            func(*args)

    Thread(target=loop).start()
    return stopped.set


def save():
    open("Info.json", "w").write(json.dumps(info))


call_repeatedly(300, save)

default_webhook = {"username": "Modshard",
                   "avatar_url": "https://cdn.discordapp.com/avatars/527283777605599243/ebac06e8cbe595e90c04999a1ace6de5.webp?size=1024"
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
        embed.add_field(name="Content", value=message.content, inline=False)
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
        embed.add_field(name="Before", value=before.content, inline=False)
        embed.add_field(name="After", value=after.content, inline=False)
        await webhook_send(guild['message log'], embed)


@bot.event
async def on_member_remove(member):
    # Sticky Role
    guild = get_guild(member)
    if "sticky role" in guild and member.guild.get_role(get_guild(member)['sticky role']) in member.roles:
        guild['evaders'].append(member.id)

    # Logging
    if "join log" in guild:
        embed = discord.Embed(color=discord.Color.orange())
        embed.title = "User Left"
        embed.add_field(name="Username", value=member)
        embed.add_field(name="UserId", value=member.id, inline=False)
        channel = bot.get_channel(guild['join log'])
        await webhook_send(channel, embed)


@bot.event
async def on_member_join(member):
    # Sticky Roles
    guild = get_guild(member)
    if "sticky role" in guild and member.id in guild['evaders']:
        await member.add_roles(member.guild.get_role(guild['sticky role']))

    # Logging
    if "join log" in guild:
        embed = discord.Embed(color=discord.Color.blue())
        embed.title = "User Joined"
        embed.add_field(name="Username", value=member)
        embed.add_field(name="UserId", value=member.id, inline=False)
        channel = bot.get_channel(guild["log channel"])
        await channel.send(embed=embed)


@bot.group(invoke_without_command=True, aliases=["s"])
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def settings(ctx):
    if str(ctx.guild.id) not in info:
        info[str(ctx.guild.id)] = {}
    embed = discord.Embed(title="Displaying Settings")
    guild = info[str(ctx.guild.id)]
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
    await ctx.send(embed=embed)


@settings.command()
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def reset(ctx, arg):
    if arg not in get_guild(ctx):
        await ctx.send("No such attribute to reset!")
        return

    get_guild(ctx).pop(arg)
    await ctx.send("%s has been reset successfully!")


@settings.command(aliases=["ml"])
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def message_log(ctx, channel: discord.TextChannel):
    info[str(ctx.guild.id)]["message log"] = channel.id
    await ctx.send("Successfully set the message log channel to %s" % channel.name)


@settings.command(aliases=["jl"])
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def join_log(ctx, channel: discord.TextChannel):
    info[str(ctx.guild.id)]["join log"] = channel.id
    await ctx.send("Successfully set the join log channel to %s" % channel.name)


@settings.group(invoke_without_command=True, aliases=["mr"])
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def modroles(ctx):
    """Displays the roles that are currently treated as mod roles by this bot"""
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


@modroles.command(invoke_without_command=True)
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def add(ctx, role: discord.Role):
    """Add a mod role to the list"""
    guild = get_guild(ctx)
    if "mod roles" not in guild:
        guild["mod roles"] = []
    info[str(ctx.guild.id)]["mod roles"].append(role.id)
    await ctx.send("Successfully added %s to the mod roles!" % role.name)


@modroles.command(invoke_without_command=True, aliases=["rem"])
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def remove(ctx, role: discord.Role):
    """Removes a mod role from the list"""
    info[str(ctx.guild.id)]["mod roles"].remove(role.id)
    await ctx.send("Successfully removed %s from the mod roles!" % role.name)


@settings.group(invoke_without_command=True, aliases=["wh"])
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def webhook(ctx):
    """Shows you an example as to what the log part of the bot looks like on your server"""
    embed = discord.Embed(title="Webhook Example!")
    embed.add_field(name="Sample Text", value="This is what i look like on here!")
    await webhook_send(ctx.channel.id, embed)


@webhook.command()
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def name(ctx, *, arg: str):
    """Changes the webhook's name to the given name"""
    guild = get_guild(ctx)
    if "webhook" not in guild:
        guild["webhook"] = dict(default_webhook)
    guild["webhook"]["username"] = arg
    await ctx.send("Updated the webhooks name to %s" % arg)


@webhook.command()
@commands.check_any(commands.has_permissions(administrator=True), is_authorized())
async def avatar(ctx, *, arg: str):
    """Changes the webhook's avatar to the given image URL"""
    guild = get_guild(ctx)
    if "webhook" not in guild:
        guild["webhook"] = dict(default_webhook)
    guild["webhook"]["avatar_url"] = arg
    await ctx.send("Updated the webhooks name to %s" % arg)


# Debug, done for manual saving
@bot.command(name="save")
@commands.is_owner()
async def save_command(ctx):
    save()

# Debug, done to get the bots avatar
@bot.command()
@commands.is_owner()
async def pic_pls(ctx):
    await ctx.send(bot.user.avatar_url)


bot.run(open("Token.txt").read())
