import discord
from Commands import Commands
from Decorators import Decorators
from DiscordDataTypes import Response
from WebAdmin import WebAdminSession, IncorrectLogindata, ServerOffline
from BattleMetrics import BattleMetricsSession


@Decorators.commands
class GlobalCommands(Commands):

    def __init__(self, app):
        self.app = app

    def __str__(self):
        return 'Basic Commands'

    @Decorators.command()
    def servers(self, guild_id, **kwargs):
        """lists the servers in your guilds server list"""
        if not self.app.active_guilds[guild_id]['servers']:
            return Response('Your server list is empty')

        embed = discord.Embed(title='Server List')
        for server in self.app.active_guilds[guild_id]['servers']:
            serverid = self.app.active_guilds[guild_id]['servers'][server]
            server_name, server_IP, bmID, waIP = self.app.run_sql(f'SELECT SERVERS.Name, SERVERS.ServerIP, SERVERS.BMID, SERVERS.WAIP FROM SERVERS WHERE SERVERS.ID = {serverid}', once=True)
            value = f"Abbreviation: {server}\nIP: {server_IP}\nWebAdmin IP: {waIP}\nBattleMetrics ID: {bmID}"
            embed.add_field(name=server_name, value=value)
        return Response(embed=embed)

    @Decorators.command('Abbreviation', 'BattleMetrics_ID', 'WebAdmin_IP:PORT')
    def addserver(self, guild_id, data, **kwargs):
        """adds a server to your guilds server list"""
        abbr, bmID, waIP, waUsername, waPassword = [option['value'] for option in data['options']]
        logindata = {'username': waUsername, 'password': waPassword}

        if abbr in self.app.active_guilds[guild_id]['servers']:
            return Response('Abbreviation already in use')

        waIP = waIP.split('//')[1]
        waIP = waIP.split('/')[0]

        waIP_list = self.app.run_sql('SELECT SERVERS.WAIP FROM SERVERS')
        if waIP in waIP_list:
            return Response('This server is already in your server list')

        async def check_webadmin():
            async with WebAdminSession(f'http://{waIP}') as webadmin:
                try:
                    await webadmin.login(logindata)
                except IncorrectLogindata:
                    return Response('Incorrect Logindata. To try again, restart the process')
                # except:
                #     return Response('WebAdmin_IP is invalid')

        webadmin_check = self.app.run_async(check_webadmin())
        if webadmin_check:
            return webadmin_check

        async def get_bminfo():
            async with BattleMetricsSession(bmID) as battlemetrics:
                info = await battlemetrics.getinfo()
                server_name = info['data']['attributes']['name']
                server_IP = f"{info['data']['attributes']['ip']}:{info['data']['attributes']['port']}"
                return server_name, server_IP

        server_name, server_IP = self.app.run_async(get_bminfo())

        logindata.pop('token', None)

        server_ID = self.app.run_sql("INSERT INTO SERVERS(Name, ServerIP, BMID, WAIP, Logindata) VALUES(%s, %s, %s, %s, %s)", server_name, server_IP, bmID, waIP, logindata, ret_ID=True)

        self.app.active_guilds[guild_id]['servers'][abbr] = server_ID
        self.app.dump_file('./data/active_guilds.json', self.app.active_guilds)
        return Response(f'{server_name} has been added to your server list as {abbr}\nServer ID: {server_ID}')

    @Decorators.command('Abbreviation')
    async def removeserver(self, app, message, abbreviation):
        """removes the given server from your guilds server list"""
        if abbreviation not in app.active_guilds[str(message.guild.id)]['servers']:
            await message.channel.send('Server not in your guilds server list')
            return
