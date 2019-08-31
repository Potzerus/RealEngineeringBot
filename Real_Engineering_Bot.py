from discord.ext import commands
from tinydb import TinyDB, Query

server = TinyDB("Data.json")
config = TinyDB("Config.json")

bot = commands.Bot(command_prefix=config.search(Query().bot_prefix)[0]["bot_prefix"])


@bot.event
async def on_ready():
    app_info = await bot.application_info()
    print("Logged in! bot invite: https://discordapp.com/api/oauth2/authorize?client_id=" +
          str(app_info.id) + "&permissions=0&scope=bot")


@bot.event
async def on_member_remove(member):
    print(member.name + " left")
    for stickied in config.search(Query().sticky_roles)[0]["sticky_roles"]:
        if member.guild.get_role(stickied) in member.roles:
            server.insert({"server_id": member.guild.id, "member_id": member.id, "role_id": stickied})
            print(member.name + " caught leaving with a stickied role")


@bot.event
async def on_member_join(member):
    for stickied in server.search((Query().server_id == member.guild.id) & (Query().member_id == member.id)):
        await member.add_roles(member.guild.get_role(stickied["role_id"]), reason="Role Persistence")

        server.remove((Query().server_id == member.guild.id) & (Query().member_id == member.id))
        print(member.name + " caught mute evading")


bot.run(config.search(Query().bot_secret)[0]["bot_secret"])
