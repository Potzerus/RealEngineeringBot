from discord.ext import commands
from tinydb import TinyDB, Query

bot = commands.Bot(command_prefix="!re")
server = TinyDB("Data.json")

muted_role_id = 517400874709155860  # actual id for RE


def get_or_make_guild(server_id):
    if not server.contains(Query().server == server_id):
        server.insert({"server": server_id, "members": [], })
    return server.search(Query().server == server_id)[0]


@bot.event
async def on_ready():
    app_info = await bot.application_info()
    print("Logged in! bot invite: https://discordapp.com/api/oauth2/authorize?client_id=" +
          str(app_info.id) + "&permissions=0&scope=bot")


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
