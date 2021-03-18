import os
import discord
from Commands import Commands
from Decorators import Decorators
from DirscordDataTypes import Response
from WebAdmin import WebAdminSession, IncorrectLogindata, ServerOffline
from BattleMetrics import BattleMetricsSession


@Decorators.commands
class GlobalCommands(Commands):

    def __init__(self, app):
        self.app = app

    def __str__(self):
        return 'Basic Commands'

    @Decorators.command()
    async def servers(self, app, message):
        """lists the servers in your guilds server list"""
        if not app.active_guilds[str(message.guild.id)]['servers']:
            return Response('Your server list is empty')

        embed = discord.Embed(title='Server List')
        for server in app.active_guilds[str(message.guild.id)]['servers']:
            server_config = app.load_file(f'./data/{str(message.guild.id)}/{server}/config.json')
            value = f"Abbreviation: {server}\nIP: {server_config['server_IP']}\nWebAdmin IP: {server_config['webadmin_IP']}\nBattleMetrics ID: {server_config['battlemetrics_ID']}"
            embed.add_field(name=server_config['server_name'], value=value)
        return Response(embed=embed)

    @Decorators.command('Abbreviation', 'BattleMetrics_ID', 'WebAdmin_IP:PORT')
    async def addserver(self, data, **kwargs):
        """adds a server to your guilds server list"""
        abbr, bmID, waIP, waUsername, waPassword = [option['value'] for option in data['options']]

        if abbr in self.app.active_guilds[str(message.guild.id)]['servers']:
            return Response('Abbreviation already in use')

        def get_webadmin_IP_list():
            webadmin_IP_list = []
            for server in app.active_guilds[str(message.guild.id)]['servers']:
                server_config = app.load_file(f'./data/{str(message.guild.id)}/{server}/config.json')
                webadmin_IP_list.append(server_config['webadmin_IP'])
            return webadmin_IP_list

        webadmin_IP_list = get_webadmin_IP_list()
        if webadmin_IP in webadmin_IP_list:
            await message.channel.send('This server is already in your server list')

        async with WebAdminSession(f'http://{webadmin_IP}') as webadmin:
            try:
                async with webadmin.get(webadmin.WAURL) as webadminpage:
                    if str(webadminpage.url) != f'{webadmin.WAURL}/ServerAdmin/':
                        await message.channel.send('WebAdmin_IP is invalid')
                        print(f'{webadmin.WAURL}/ServerAdmin/')
                        print(webadminpage.url)
                        return
            except:
                print(webadmin_IP)
                await message.channel.send('WebAdmin_IP is invalid')
                return

            def check(m):
                return(m.author == message.author)

            logindata = {}

            async def check_cancel(m):
                if m.content.lower() == 'cancel':
                    await m.channel.send('Process has been cancelled')
                    return True
                return False

            await message.channel.send('To cancel the process write "cancel" (30s Timeout)')

            await message.channel.send('Enter WebAdmin username:')
            try:
                msg = await app.wait_for('message', check=check, timeout=30)
            except:
                await message.channel.send('Process has been cancelled')
                return

            if await check_cancel(msg):
                return

            logindata['username'] = msg.content

            await message.channel.send('Enter WebAdmin password: (The password will be hashed)')
            try:
                msg = await app.wait_for('message', check=check, timeout=30)
            except:
                await message.channel.send('Process has been cancelled')
                return

            if await check_cancel(msg):
                return

            logindata['password'] = msg.content

            await message.channel.send('Make sure to delete any messages containing sensitive data (passwords)')

            try:
                await webadmin.login(logindata)
            except IncorrectLogindata:
                await message.channel.send('Incorrect Logindata. To try again, restart the process')
                return

        async with BattleMetricsSession(battlemetrics_ID) as battlemetrics:
            info = await battlemetrics.getinfo()
            server_name = info['data']['attributes']['name']
            server_IP = f"{info['data']['attributes']['ip']}:{info['data']['attributes']['port']}"

        app.active_guilds[str(message.guild.id)]['servers'].append(abbreviation)
        app.dump_file('./data/active_guilds.json', app.active_guilds)
        os.makedirs(os.path.dirname(f'./data/{str(message.guild.id)}/{abbreviation}/'), exist_ok=True)
        app.dump_file(f'./data/{str(message.guild.id)}/{abbreviation}/config.json', {'server_name': server_name, 'server_IP': server_IP, 'battlemetrics_ID': battlemetrics_ID, 'webadmin_IP': webadmin_IP, 'logindata': logindata})
        await message.channel.send(f'{server_name} has been added to your server list as {abbreviation}')

    @Decorators.command('Abbreviation')
    async def removeserver(self, app, message,  abbreviation):
        """removes the given server from your guilds server list"""
        if abbreviation not in app.active_guilds[str(message.guild.id)]['servers']:
            await message.channel.send('Server not in your guilds server list')
            return
