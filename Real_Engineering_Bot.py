import asyncio
import sys
import time
import signal

import discord
from discord.ext import commands
from tinydb import TinyDB, Query

bot = commands.Bot(command_prefix="!re")
server = TinyDB("Data.json")

muted_role_id = 517400874709155860  # actual id for RE
log_channel_id = 480190548511031306  # id for RE


def get_or_make_guild(server_id):
    if not server.contains(Query().server == server_id):
        server.insert({"server": server_id, "members": [], })
    return server.search(Query().server == server_id)[0]


@bot.event
async def on_ready():
    global appli
    appli = await bot.application_info()
    print("Logged in! bot invite: https://discordapp.com/api/oauth2/authorize?client_id=" +
          str(appli.id) + "&permissions=0&scope=bot")

@bot.event
async def on_message_delete(message):
    embed = discord.Embed()
    embed.title = "Deleted Message"
    embed.add_field(name="Username", value=message.author)
    embed.add_field(name="UserId", value=message.author.id, inline=False)
    embed.add_field(name="Channel", value="<#%d>" % message.channel.id, inline=False)
    embed.add_field(name="Content", value=message.content, inline=False)
    await bot.get_channel(log_channel_id).send(embed=embed)


@bot.event
async def on_message_edit(before, after):
    if before.content != "" and before.content is not after.content:
        embed = discord.Embed()
        embed.title = "Edited Message"
        embed.add_field(name="Username", value=after.author)
        embed.add_field(name="UserId", value=after.author.id, inline=False)
        embed.add_field(name="Channel", value="<#%d>" % before.channel.id, inline=False)
        print(before.content)
        embed.add_field(name="Before", value=before.content, inline=False)
        print(after.content)
        embed.add_field(name="After", value=after.content, inline=False)
        print(embed)
        channel = bot.get_channel(log_channel_id)
        await channel.send(embed=embed)


@bot.event
async def on_member_remove(member):
    if member.guild.get_role(muted_role_id) in member.roles:
        get_or_make_guild(member.guild.id)
        members = server.all()[0]['members']
        members.append(member.id)
        server.update({"members": members}, Query().server == member.guild.id)
        print(member.name + " caught leaving with a mute")


@bot.event
async def on_member_join(member):
    muted_members = get_or_make_guild(member.guild.id)['members']
    if member.id in muted_members:
        muted_members.remove(member.id)
        await member.add_roles(
            member.guild.get_role(muted_role_id), reason="Mute Persistence")
        server.update({"members": muted_members})
        print(member.name + " caught mute evading")


bot.run(open("RE-Token.txt").read())