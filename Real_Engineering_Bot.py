import yaml
from discord.ext import commands
from tinydb import TinyDB, Query

server = TinyDB("Data.json")

config_file = open("config.yaml")
config = yaml.load(config_file, Loader=yaml.FullLoader)
config_file.close()

bot = commands.Bot(command_prefix=config["bot_prefix"])


@bot.event
async def on_ready():
    app_info = await bot.application_info()
    print("Logged in! bot invite: https://discordapp.com/api/oauth2/authorize?client_id=" +
          str(app_info.id) + "&permissions=0&scope=bot")


@bot.event
async def on_member_remove(member):
    for stickied in config["sticky_roles"]:
        if member.guild.get_role(stickied) in member.roles:
            server.insert({"server_id": member.guild.id, "member_id": member.id, "role_id": stickied})
            print(member.name + " caught leaving with a stickied role")


@bot.event
async def on_member_join(member):
    for stickied in server.search((Query().server_id == member.guild.id) & (Query().member_id == member.id)):
        await member.add_roles(member.guild.get_role(stickied["role_id"]), reason="Role Persistence")
        server.remove((Query().server_id == member.guild.id) & (Query().member_id == member.id))
        print(member.name + " stickied roles restored")


bot.run(config["bot_secret"])
