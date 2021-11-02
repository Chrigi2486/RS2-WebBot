import string
import base64
import hashlib
import discord
import asyncio
import traceback
from aiohttp import ClientSession
from HTTPWebAdmin import Route as WARoute
from HTTPWebAdmin import Parser as WAParser
from HTTPBattleMetrics import Route as BMRoute
from Commands import Commands
from Decorators import Decorators
from DiscordDataTypes import Response


@Decorators.commands
class GlobalCommands(Commands):

    def __init__(self, app):
        self.app = app
        self.guild_command_options = self.app.guild_commands.command_options

    def __str__(self):
        return 'Global Commands'

    @staticmethod
    def flush_tasks(tasks):
        for task in tasks:
            if tasks[task].cancelled():
                tasks.pop(task)

    @Decorators.command()
    async def servers(self, guild_id, **kwargs):
        """lists the servers in your guilds server list"""
        if not self.app.active_guilds[guild_id]['servers']:
            return Response('Your server list is empty')

        embed = discord.Embed(title='Server List')
        abbreviations = {v: k for k, v in self.app.active_guilds[guild_id]['servers'].items()}
        servers = self.app.run_sql(f"SELECT SERVERS.ID, SERVERS.Name, SERVERS.ServerIP, SERVERS.BMID, SERVERS.WAIP FROM SERVERS WHERE SERVERS.ID IN ({','.join([str(v) for v in self.app.active_guilds[guild_id]['servers'].values()])})")
        for server in servers:
            server_id, server_name, server_IP, bmID, waIP = server
            value = f"Abbreviation: {abbreviations[server_id]}\nID: {server_id}\nIP: {server_IP}\nWebAdmin IP: {waIP}\nBattleMetrics ID: {bmID}"
            embed.add_field(name=server_name, value=value)
        return Response(embed=embed)

    @Decorators.command('Abbreviation', 'BattleMetrics_ID', 'WebAdmin_IP:PORT')
    async def addserver(self, guild_id, data, **kwargs):
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

        async def check_webadmin():
            page = await self.app.client.http.request(WARoute('GET', waIP, '/current'), cookies={'authcred': authcred})
            title = WAParser.parse_page_title(page)
            if title == 'Rising Storm 2: Vietnam WebAdmin - Login':
                return Response('Incorrect Logindata')
            if title == 'Rising Storm 2: Vietnam WebAdmin - Current Game':
                return
            return Response('Invalid URL or PORT')

        webadmin_check = await check_webadmin()
        if webadmin_check:
            return webadmin_check

        async def create_session_id():  # needed for chat
            async with ClientSession() as session:
                async with session.get(WARoute('GET', waIP, '').url) as page:
                    session_id = page.cookies.get('sessionid').value.replace('"', '')
                    token = WAParser.parse_login_page(await page.text())
            payload = {'token': token, 'password_hash': authhash, 'username': waUsername, 'password': '', 'remember': '-1'}
            await self.app.client.http.request(WARoute('POST', waIP, '/', data=payload))
            return session_id

        session_id = await create_session_id()

        async def get_bminfo():
            info = await self.app.client.http.request(BMRoute('GET', bmID, ''))
            server_name = info['data']['attributes']['name']
            server_IP = f"{info['data']['attributes']['ip']}:{info['data']['attributes']['port']}"
            return server_name, server_IP

        server_name, server_IP = await get_bminfo()

        server_ID = self.app.run_sql("INSERT INTO SERVERS(Name, ServerIP, BMID, WAIP, Authcred, SessionID) VALUES(%s, %s, %s, %s, %s, %s)", server_name, server_IP, bmID, waIP, authcred, session_id, ret_ID=True)

        self.app.active_guilds[guild_id]['servers'][abbr] = server_ID
        self.app.dump_file(self.app.bot_config['paths']['active_guilds'], self.app.active_guilds)
        get_requests = []
        for command in self.app.active_guilds[guild_id]['commands']:
            command_id = self.app.active_guilds[guild_id]['commands'][command]
            get_requests.append(self.app.get_guild_command(guild_id, command_id))
        command_infos = await asyncio.gather(*get_requests, loop=self.app.client.loop)
        post_requests = []
        for command in command_infos:
            command_id = command['id']
            if 'options' in command:
                options = command['options']
            else:
                options = []
            options.append({"name": abbr, "description": server_name, "type": 1, "options": self.guild_command_options[command['name']]})
            post_requests.append(self.app.edit_guild_command(guild_id, command_id, {'options': options}))
        await asyncio.gather(*post_requests, loop=self.app.client.loop)
        return Response(f'{server_name} has been added to your server list\nAbbreviation: {abbr}\nServer ID: {server_ID}\nMake sure to delete any messages containing passwords!')

    @Decorators.command('Abbreviation')
    async def removeserver(self, guild_id, data, **kwargs):
        """removes the given server from your guilds server list"""
        abbr = data['options'][0]['value']
        if abbr not in self.app.active_guilds[guild_id]['servers']:
            return Response('Server not in your guilds server list')
        server_id = self.app.active_guilds[guild_id]['servers'].pop(abbr)
        self.app.dump_file(self.app.bot_config['paths']['active_guilds'], self.app.active_guilds)
        self.app.run_sql(f'DELETE FROM SERVERS WHERE SERVERS.ID = {server_id}')
        self.app.run_sql(f'DELETE FROM STATS WHERE STATS.SID = {server_id}')
        self.app.run_sql(f'DELETE FROM BANS WHERE BANS.SID = {server_id}')
        get_requests = []
        for command in self.app.active_guilds[guild_id]['commands']:
            command_id = self.app.active_guilds[guild_id]['commands'][command]
            get_requests.append(self.app.get_guild_command(guild_id, command_id))
        command_infos = await asyncio.gather(*get_requests, loop=self.app.client.loop)
        post_requests = []
        for command in command_infos:
            command_id = command['id']
            options = command['options']
            for i, option in enumerate(options):
                if option['name'] == abbr:
                    options.pop(i)
                    break
            post_requests.append(self.app.edit_guild_command(guild_id, command_id, {'options': options}))
        await asyncio.gather(*post_requests, loop=self.app.client.loop)
        return Response(f'{abbr} has been removed from your server list and our database')

    @Decorators.command()
    async def liveinfo(self, data, guild_id, **kwargs):
        start, abbr, channel_id = [option['value'] for option in data['options']]
        if abbr not in self.app.active_guilds[guild_id]['servers']:
            return Response('Server not in your guilds server list')
        server_id = self.app.active_guilds[guild_id]['servers'][abbr]
        if not start:
            if server_id not in self.app.info_tasks:
                return Response(f'Live info is currently not running on {abbr}')
            self.app.info_tasks[server_id].cancel()
            self.flush_tasks(self.app.info_tasks)
            return Response(f'Live info has been stopped for {abbr}')
        self.app.current_players[server_id] = None
        task = self.app.add_async(self.live_info(server_id, channel_id, guild_id, abbr))
        self.app.info_tasks[server_id] = task
        return Response(f"Live info for {abbr} will start momentarily")

    @Decorators.command()
    async def livechat(self, data, guild_id, **kwargs):
        start, abbr, channel_id = [option['value'] for option in data['options']]
        if abbr not in self.app.active_guilds[guild_id]['servers']:
            return Response('Server not in your guilds server list')
        server_id = self.app.active_guilds[guild_id]['servers'][abbr]
        if not start:
            if server_id not in self.app.chat_tasks:
                return Response(f'Live chat is currently not running on {abbr}')
            self.app.chat_tasks[server_id].cancel()
            self.flush_tasks(self.app.chat_tasks)
            return Response(f'Live chat has been stopped for {abbr}')
        if server_id in self.app.chat_tasks:
            return Response(f'Live chat is already active for {abbr}')
        task = self.app.add_async(self.live_chat(server_id, channel_id))
        self.app.chat_tasks[server_id] = task
        return Response(f"Live chat for {abbr} will start momentarily")

    async def live_info(self, server_id, channel_id, guild_id, abbr):
        bm_id, wa_ip, authcred = self.app.run_sql(f'SELECT SERVERS.BMID, SERVERS.WAIP, SERVERS.Authcred FROM SERVERS WHERE SERVERS.ID = {server_id}')[0]
        cookies = {'authcred': authcred}
        message = await (await self.app.client.fetch_channel(channel_id)).send('Placeholder for live info')
        try:
            while True:
                current = await self.app.client.http.request(WARoute('GET', wa_ip, '/current'), cookies=cookies)
                current = WAParser.parse_current(current)
                players = await self.app.client.http.request(WARoute('GET', wa_ip, '/current/players'), cookies=cookies)
                players = WAParser.parse_player_list(players)
                self.app.current_players[server_id] = players
                if players:
                    choices = [{'name': player['name'], 'value': str(index)} for index, player in enumerate(players)]
                else:
                    choices = []
                command = await self.app.get_guild_command(guild_id, self.app.active_guilds[guild_id]['commands']['kick'])
                options = command['options']
                for option in options:
                    if option['name'] == abbr:
                        option['options'][0]['choices'] = choices
                await self.app.edit_guild_command(guild_id, self.app.active_guilds[guild_id]['commands']['kick'], {'options': options})
                content = '------------------------------------------------------\nName: {name}\nPlayers: {players}/64\nMap: {map}\n------------------------------------------------------'
                content = content.format(**current)
                await message.edit(content=content)
                await asyncio.sleep(30)
        except Exception as e:
            print(traceback.format_exc())

    async def live_chat(self, server_id, channel_id):
        wa_ip, authcred, session_id = self.app.run_sql(f'SELECT SERVERS.WAIP, SERVERS.Authcred, SERVERS.SessionID FROM SERVERS WHERE SERVERS.ID = {server_id}')[0]
        channel = await self.app.client.fetch_channel(channel_id)
        print(channel)
        cookies = {'authcred': authcred, 'sessionid': session_id}
        try:
            while True:
                chat_response = await self.app.client.http.request(WARoute('GET', wa_ip, '/current/chat/data'), cookies=cookies)
                print(chat_response)
                messages = WAParser.parse_chat(chat_response)
                print(messages)
                for message in messages:
                    embed = discord.Embed(
                        description=f"{message['team']} **{message['username']}**: {message['content']}",
                        color=message['color']
                        )
                    await channel.send(embed=embed)
                await asyncio.sleep(5)
        except Exception as e:
            print(traceback.format_exc())
