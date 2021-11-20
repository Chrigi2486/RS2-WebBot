import os
import sys
import asyncio
import importlib
import traceback
from json import load, dump
from discord import Client
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from HTTPDiscord import Route
from DiscordDataTypes import Response, AutoCompleteResponse, CommandOptionChoice
from quart import Quart, request, jsonify
import mysql.connector
import GlobalCommands
import GuildCommands
import AdminCommands

sys.path.insert(0, os.path.dirname(__file__))


class RS2WebBot(Quart):

    CLIENT_PUBLIC_KEY = os.getenv('CLIENT_PUBLIC_KEY')
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    CLIENT_ID = os.getenv('CLIENT_ID')
    MYSQL_DATABASE = 'RS2Database'
    MYSQL_HOST = '127.0.0.1'
    MYSQL_USERNAME = 'RS2WebBot'
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')

    def __init__(self, *args, **kwargs):

        self.verifier = VerifyKey(bytes.fromhex(self.CLIENT_PUBLIC_KEY))

        self.client = Client()

        self.run_async(self.client.login(self.BOT_TOKEN))

        def check_for_file(path, base=False):
            if not os.path.isfile(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as wfile:
                    wfile.write((base if base else'{}'))
                return False
            return True

        self.update_commands(True, True, True)

        check_for_file('./config.json')
        self.bot_config = self.load_file('./config.json')

        check_for_file(self.bot_config['paths']['active_guilds'])
        self.active_guilds = self.load_file(self.bot_config['paths']['active_guilds'])

        self.info_tasks = {}
        self.chat_tasks = {}

        self.current_players = {}

        super().__init__(*args, **kwargs)

    def run_async(self, command):
        return self.client.loop.run_until_complete(command)

    def add_async(self, command):
        return asyncio.ensure_future(command)

    def run_sql(self, command, *args, ret_ID=False, one=False):
        database = mysql.connector.connect(user=self.MYSQL_USERNAME, password=self.MYSQL_PASSWORD, host=self.MYSQL_HOST, database=self.MYSQL_DATABASE)
        cursor = database.cursor()
        cursor.execute(command, args)
        if ret_ID:
            result = cursor.lastrowid
        elif one:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
        cursor.close()
        database.commit()
        database.close()
        return result

    async def check_command(self, data):
        command = data['data']['name']
        if command in self.global_commands:
            return await self.check_user(self.global_commands, data)

        if command in self.guild_commands:
            if self.active_guilds[data['guild_id']]['premium']:
                return await self.check_user(self.guild_commands, data)
            return Response('Upgrade to Premium to unlock these commands!')
        if command in self.admin_commands:
            return await self.check_user(self.admin_commands, data, admin=True)
        return Response(f'Command {command} not found')

    async def check_user(self, commands, data, admin=False):
        if admin:
            if data['member']['user']['id'] in self.bot_config['validators']:
                return await self.run_command(commands, data)
            return Response('You aren\'t authorised to use this command!')

        guild_id = data['guild_id']
        if guild_id in self.active_guilds and self.active_guilds[guild_id]['validated']:
            if self.active_guilds[data['guild_id']]['admin'] in data['member']['roles']:
                return await self.run_command(commands, data)
            return Response('You aren\'t authorised to use this command!')
        return Response('This Discord-Server must be validated by -[HELLO]- before the bot can be used!')

    async def run_command(self, commands, data):
        command = data['data']['name']
        try:
            return await commands[command](commands, **data)
        except Exception as e:
            self.logger.error(traceback.format_exc())
            return Response(f'An Error occured! Please contact a member of the -[HELLO]- Team and provide the error message below :)\n**Command:** {command}\n**Error:** {e}')

    def update_commands(self, globalc=False, guildc=False, adminc=False):
        if guildc:
            importlib.reload(GuildCommands)
            self.guild_commands = GuildCommands.GuildCommands(self)
        if globalc:
            importlib.reload(GlobalCommands)
            self.global_commands = GlobalCommands.GlobalCommands(self)
        if adminc:
            importlib.reload(AdminCommands)
            self.admin_commands = AdminCommands.AdminCommands(self)
        return globalc, guildc, adminc

    def auto_complete(self, data):

        for option in data['data']['options']:
            for aoption in option['options']:
                if aoption.get('focused'):
                    abbr = option['name']
                    value = aoption['value']
                    break

        choices = []
        playerlist = self.current_players.get(self.active_guilds[data['guild_id']][abbr])
        if playerlist:
            for player in playerlist:
                if player['name'].lower.startswith(value):
                    choices.append(CommandOptionChoice(player['name'], player['name']))

        return AutoCompleteResponse(choices)

    def load_file(self, path):
        with open(path, 'r') as file:
            return load(file)

    def dump_file(self, path, data):
        with open(path, 'w') as file:
            dump(data, file)

    def get_global_command(self, command_id):
        return self.client.http.request(Route('GET', f'/applications/{self.CLIENT_ID}/commands/{command_id}'))

    def get_guild_command(self, guild_id, command_id):
        return self.client.http.request(Route('GET', f'/applications/{self.CLIENT_ID}/guilds/{guild_id}/commands/{command_id}', guild_id=guild_id))

    def create_global_command(self, payload):
        return self.client.http.request(Route('POST', f'/applications/{self.CLIENT_ID}/commands'), json=payload)

    def create_guild_command(self, guild_id, payload):
        return self.client.http.request(Route('POST', f'/applications/{self.CLIENT_ID}/guilds/{guild_id}/commands', guild_id=guild_id), json=payload)

    def edit_global_command(self, command_id, payload):
        return self.client.http.request(Route('PATCH', f'/applications/{self.CLIENT_ID}/commands/{command_id}'), json=payload)

    def edit_guild_command(self, guild_id, command_id, payload):
        return self.client.http.request(Route('PATCH', f'/applications/{self.CLIENT_ID}/guilds/{guild_id}/commands/{command_id}', guild_id=guild_id), json=payload)


app = RS2WebBot(__name__)


@app.route('/', methods=['GET'])
async def status():
    return jsonify({"status": 1})


@app.route('/', methods=['POST'])
async def handle_command():
    signature = request.headers.get('X-Signature-Ed25519')
    timestamp = request.headers.get('X-Signature-Timestamp')
    if signature is None or timestamp is None:
        return 'No request signature', 401
    request_data = (await request.get_data()).decode('utf-8')
    try:
        app.verifier.verify(f'{timestamp}{request_data}'.encode(), bytes.fromhex(signature))
    except BadSignatureError:
        print('Bad signature')
        return 'Bad request signature', 401

    # Automatically respond to pings
    request_json = await request.get_json()
    if request_json:
        if request_json.get('type') == 1:
            return jsonify({'type': 1})
        if request_json.get('type') == 2:
            return jsonify((await app.check_command(request_json)).to_dict())
        if request_json.get('type') == 4:
            return jsonify((app.auto_complete(request_json)).to_dict())


if __name__ == '__main__':
    app.run()
