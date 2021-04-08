import string
import base64
import hashlib
import discord
import asyncio
from HTTPWebAdmin import Route as WARoute
from Commands import Commands
from Decorators import Decorators
from DiscordDataTypes import Response
from BattleMetrics import BattleMetricsSession


@Decorators.commands
class GlobalCommands(Commands):

    def __init__(self, app):
        self.app = app
        self.guild_command_options = self.app.guild_commands.command_options

    def __str__(self):
        return 'Basic Commands'

    @Decorators.command()
    def servers(self, guild_id, **kwargs):
        """lists the servers in your guilds server list"""
        if not self.app.active_guilds[guild_id]['servers']:
            return Response('Your server list is empty')

        embed = discord.Embed(title='Server List')
        abbreviations = {v: k for k, v in self.app.active_guilds[guild_id]['servers'].items()}
        servers = self.app.run_sql(f"SELECT SERVERS.ID, SERVERS.Name, SERVERS.ServerIP, SERVERS.BMID, SERVERS.WAIP FROM SERVERS WHERE SERVERS.ID IN {tuple(self.app.active_guilds[guild_id]['servers'].values())}")
        for server in servers:
            server_id, server_name, server_IP, bmID, waIP = server
            value = f"Abbreviation: {abbreviations[server_id]}\nID: {server_id}\nIP: {server_IP}\nWebAdmin IP: {waIP}\nBattleMetrics ID: {bmID}"
            embed.add_field(name=server_name, value=value)
        return Response(embed=embed)

    @Decorators.command('Abbreviation', 'BattleMetrics_ID', 'WebAdmin_IP:PORT')
    def addserver(self, guild_id, data, **kwargs):
        """adds a server to your guilds server list"""
        abbr, bmID, waIP, waUsername, waPassword = [option['value'] for option in data['options']]
        authhash = '$sha1$' + hashlib.sha1((waPassword + waUsername).encode('utf-8')).hexdigest()
        authcred = base64.b64encode(f'{waUsername}\n{authhash}'.encode('UTF-8')).decode('UTF-8')

        if abbr in self.app.active_guilds[guild_id]['servers']:
            return Response('Abbreviation already in use')

        waIP = waIP.strip(string.ascii_letters + '/:')

        waIP_list = [IP[0] for IP in self.app.run_sql('SELECT SERVERS.WAIP FROM SERVERS')]
        if waIP in waIP_list:
            return Response('This server is already in your server list')

        # async def check_webadmin():
        #     async with WebAdminSession(f'http://{waIP}') as webadmin:
        #         try:
        #             await webadmin.login(logindata)
        #         except IncorrectLogindata:
        #             return Response('Incorrect Logindata. To try again, restart the process')
                # except:
                #     return Response('WebAdmin_IP is invalid')

        webadmin_check = None  # self.app.run_async(check_webadmin())
        if webadmin_check:
            return webadmin_check

        async def get_bminfo():
            async with BattleMetricsSession(bmID) as battlemetrics:
                info = await battlemetrics.getinfo()
                server_name = info['data']['attributes']['name']
                server_IP = f"{info['data']['attributes']['ip']}:{info['data']['attributes']['port']}"
                return server_name, server_IP

        server_name, server_IP = self.app.run_async(get_bminfo())

        server_ID = self.app.run_sql("INSERT INTO SERVERS(Name, ServerIP, BMID, WAIP, authcred) VALUES(%s, %s, %s, %s, %s)", server_name, server_IP, bmID, waIP, authcred, ret_ID=True)

        self.app.active_guilds[guild_id]['servers'][abbr] = server_ID
        self.app.dump_file('./data/active_guilds.json', self.app.active_guilds)
        for command in self.guild_command_options:
            command_id = self.app.active_guilds[guild_id]['commands'][command]
            try:
                options = self.app.get_guild_command(guild_id, command_id)['options']
            except KeyError:
                options = []
            options.append({"name": abbr, "description": server_name, "type": 1, "options": self.guild_command_options[command]})
            self.app.edit_guild_command(guild_id, command_id, {'options': options})
        return Response(f'{server_name} has been added to your server list as {abbr}\nServer ID: {server_ID}\nMake sure to delete any messages containing passwords!')

    @Decorators.command('Abbreviation')
    def removeserver(self, guild_id, data, **kwargs):  # TODO remove the subcommands for this server
        """removes the given server from your guilds server list"""
        abbr = data['options'][0]['value']
        if abbr not in self.app.active_guilds[guild_id]['servers']:
            return Response('Server not in your guilds server list')
        server_id = self.app.active_guilds[guild_id]['servers'].pop(abbr)
        self.app.dump_file('./data/active_guilds.json', self.app.active_guilds)
        self.app.run_sql(f'DELETE FROM SERVERS WHERE SERVERS.ID = {server_id}')
        self.app.run_sql(f'DELETE FROM STATS WHERE STATS.SID = {server_id}')
        self.app.run_sql(f'DELETE FROM BANS WHERE BANS.SID = {server_id}')
        get_requests = []
        for command in self.guild_command_options:
            command_id = self.app.active_guilds[guild_id]['commands'][command]
            get_requests.append(self.app.cour_get_guild_command(guild_id, command_id))
        command_infos = self.app.run_async(asyncio.gather(get_requests))
        post_requests = []
        for command in command_infos:
            command_id = command['id']
            options = command['options']
            for i, option in enumerate(options):
                if option['name'] == abbr:
                    options.pop(i)
                    break
            post_requests.append(self.app.cour_edit_guild_command(guild_id, command_id, {'options': options}))
        self.app.run_async(asyncio.gather(post_requests))
        return Response(f'{abbr} has been removed from your server list and our database')
