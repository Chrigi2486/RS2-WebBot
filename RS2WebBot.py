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


class RS2WebBot(Quart):  # This is the main class for the bot. It inherits the functionality of an asynchronous WebApp from the Quart class

    # These next variables need to be manually set as enviroment variables before running the bot
    CLIENT_PUBLIC_KEY = os.getenv('CLIENT_PUBLIC_KEY')  # Needed by Discord to authenticate the Bot. Found under Application -> General Information -> Public Key (In the Discord Developer Portal)
    BOT_TOKEN = os.getenv('BOT_TOKEN')  # Needed by the bot. Found under Application -> Bot -> Token
    CLIENT_ID = os.getenv('CLIENT_ID')  # Needed by the bot to find and edit its own commands. Found under Application -> General Information -> Application ID
    
    # These are variables for the SQL database in order to connect
    MYSQL_DATABASE = 'RS2Database'
    MYSQL_HOST = '127.0.0.1'
    MYSQL_USERNAME = 'RS2WebBot'
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')

    def __init__(self, *args, **kwargs):

        # Used to verify incoming commands
        self.verifier = VerifyKey(bytes.fromhex(self.CLIENT_PUBLIC_KEY))

        # Discord.py Client, used to send/edit messages and to get information on Discord servers
        self.client = Client()

        self.run_async(self.client.login(self.BOT_TOKEN))  # Logging in to the Discord.py Client

        def check_for_file(path, base=False):  # lil function to check if a file exists and if it doesn't then it creates it
            if not os.path.isfile(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as wfile:
                    wfile.write((base if base else'{}'))
                return False
            return True

        self.update_commands(True, True, True)  # This does an initial import of the commands

        # loads in the config file which should contain the validators and the path to the config and active_guilds file like so:
        #   {"validators": ["validatorID1", "validatorID2"], "paths": {"active_guilds": "./active_guilds.json", "config": "./config.json"}}
        check_for_file('./config.json')
        self.bot_config = self.load_file('./config.json')

        # loads the active_guilds file. This file is filled out automatically
        check_for_file(self.bot_config['paths']['active_guilds'])
        self.active_guilds = self.load_file(self.bot_config['paths']['active_guilds'])

        # initialising some valriables
        self.info_tasks = {}
        self.chat_tasks = {}

        self.current_players = {}

        super().__init__(*args, **kwargs)

    def run_async(self, command):  # A function to run an asynchronous function synchronously (blocking)
        return self.client.loop.run_until_complete(command)

    def add_async(self, command):  # A function to add an asynchronous function to the event loop, so it can be executed asynchronously (non-blocking)
        return asyncio.ensure_future(command)

    def run_sql(self, command, *args, ret_ID=False, one=False):  # A function to run an SQL command
        database = mysql.connector.connect(user=self.MYSQL_USERNAME, password=self.MYSQL_PASSWORD, host=self.MYSQL_HOST, database=self.MYSQL_DATABASE)  # Connects to Database
        cursor = database.cursor() # Creates a cursor to edit/read from the database
        cursor.execute(command, args)  # executes the given command
        if ret_ID:
            result = cursor.lastrowid  # Sets return value to the ID of the added item (very useful)
        elif one:
            result = cursor.fetchone()  # Sets the return value to a single value (use this when you only expect to get one result)
        else:
            result = cursor.fetchall()  # Return the default values. Will return all the rows selected
        cursor.close()  # Stops editing/reading
        database.commit()  # Commits changes to the Database
        database.close()  # Closes Database
        return result

    async def check_command(self, data):  # A function to check if a command exists or if the server has rights to it
        command = data['data']['name']  # Get the command from the data
        
        if command in self.global_commands:  # Checks if command is in global commands and passes it on to check if server is validated and if user is server admin
            return await self.check_user(self.global_commands, data)

        if command in self.guild_commands:  # Checks if command is in guild commands and if server is premium, then passes it on to check if user is server admin
            if self.active_guilds[data['guild_id']]['premium']:
                return await self.check_user(self.guild_commands, data)
            return Response('Upgrade to Premium to unlock these commands!')
        
        if command in self.admin_commands:  # Checks if command is in admin commands and passes it on to check if user is bot admin
            return await self.check_user(self.admin_commands, data, admin=True)
        return Response(f'Command {command} not found')

    async def check_user(self, commands, data, admin=False):  # A function to check if user using command has the rights to do so and to check if server is validated
        if admin:
            if data['member']['user']['id'] in self.bot_config['validators']:  # Checks if user is bot admin
                return await self.run_command(commands, data)  # If so it runs the command
            return Response('You aren\'t authorised to use this command!')

        guild_id = data['guild_id']
        if guild_id in self.active_guilds and self.active_guilds[guild_id]['validated']:  # Checks if discord server is validated
            if self.active_guilds[data['guild_id']]['admin'] in data['member']['roles']:  # Checks if user is a server admin
                return await self.run_command(commands, data)  # If so it runs the command
            return Response('You aren\'t authorised to use this command!')
        return Response('This Discord-Server must be validated by -[HELLO]- before the bot can be used!')

    async def run_command(self, commands, data):  # A function to run the given command
        command = data['data']['name']  # Command is extracted from the data
        try:
            return await commands[command](commands, **data)  # Command is executed using the data as possible arguments
        except Exception as e:  # If an error occurs during execution, a detailed error will be printed in the terminal and a smaller error message will be given to the user
            self.logger.error(traceback.format_exc())
            return Response(f'An Error occured! Please contact a member of the -[HELLO]- Team and provide the error message below :)\n**Command:** {command}\n**Error:** {e}')

    def update_commands(self, globalc=False, guildc=False, adminc=False):  # A function to update the commands without having to restart the app, in case we make changes to the commands down the road
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

    def auto_complete(self, data):  # A function to giev a list of names when using kick or ban (very cool and useful lol)

        for option in data['data']['options']:  # Gets the value given into the player field
            for aoption in option['options']:
                if aoption.get('focused'):
                    abbr = option['name']
                    value = aoption['value']
                    break

        choices = []
        playerlist = self.current_players.get(self.active_guilds[data['guild_id']]['servers'][abbr])  # Gets the player list of the current server
        if playerlist:
            for player in playerlist:  # Finds players with similar names and adds them to the possible choices
                if player['name'].lower().startswith(value.lower()):
                    choices.append(CommandOptionChoice(player['name'], player['name']))

        return AutoCompleteResponse(choices[:25])  # Returns the choices cut down to 25 option, as this is the max that Discord will allow

    def load_file(self, path):  # Loads a specified file to the specific variable (used for manual config and active_guilds changes)
        with open(path, 'r') as file:
            return load(file)

    def dump_file(self, path, data):  # Dumps the data to the specified path (used for manually changing the config and active_guilds files)
        with open(path, 'w') as file:
            dump(data, file)

    def get_global_command(self, command_id):  # A function to get info on a global command
        return self.client.http.request(Route('GET', f'/applications/{self.CLIENT_ID}/commands/{command_id}'))

    def get_guild_command(self, guild_id, command_id):  # A function to get info on a guild command
        return self.client.http.request(Route('GET', f'/applications/{self.CLIENT_ID}/guilds/{guild_id}/commands/{command_id}', guild_id=guild_id))

    def create_global_command(self, payload):  # A function to create a new global command
        return self.client.http.request(Route('POST', f'/applications/{self.CLIENT_ID}/commands'), json=payload)

    def create_guild_command(self, guild_id, payload):  # A function to create a new guild command
        return self.client.http.request(Route('POST', f'/applications/{self.CLIENT_ID}/guilds/{guild_id}/commands', guild_id=guild_id), json=payload)

    def edit_global_command(self, command_id, payload):  # A function to edit a global command
        return self.client.http.request(Route('PATCH', f'/applications/{self.CLIENT_ID}/commands/{command_id}'), json=payload)

    def edit_guild_command(self, guild_id, command_id, payload):  # A function to edit a guild command
        return self.client.http.request(Route('PATCH', f'/applications/{self.CLIENT_ID}/guilds/{guild_id}/commands/{command_id}', guild_id=guild_id), json=payload)


app = RS2WebBot(__name__)  # Creates an instance of the bot


@app.route('/', methods=['GET'])  # Defines the root of the WebApp, which shows the status of the bot (always 1)
async def status():
    return jsonify({"status": 1})


@app.route('/', methods=['POST'])  # Handles post requests
async def handle_command():
    signature = request.headers.get('X-Signature-Ed25519')  # Gets signature of the request from the headers
    timestamp = request.headers.get('X-Signature-Timestamp')  # Gets the timestamp of the request from the headers
    if signature is None or timestamp is None:  # If any of these are missing, it'll return an error
        return 'No request signature', 401
    request_data = (await request.get_data()).decode('utf-8')  # Extracts the request data from the request
    try:
        app.verifier.verify(f'{timestamp}{request_data}'.encode(), bytes.fromhex(signature))  # Verifies if the timestamp and data correspond to the signature (for security and integrity reasons)
    except BadSignatureError:
        print('Bad signature')
        return 'Bad request signature', 401

    # Automatically respond to pings
    request_json = await request.get_json()  # Extracts the json data from the request
    if request_json:
        if request_json.get('type') == 1:  # Checks if the request is a PING, then it'll return a PONG
            return jsonify({'type': 1})
        if request_json.get('type') == 2:  # Checks if the request is a command, then sends the command/user/server to be checked and executed
            return jsonify((await app.check_command(request_json)).to_dict())  # And returns the response of the command
        if request_json.get('type') == 4:  # Checks if the request is for autocomplete (currently only autocompletes player names)
            return jsonify((app.auto_complete(request_json)).to_dict())  # Creates a list of possible players and returns them


if __name__ == '__main__':  # If you run this file it will run the WebApp like this. One should use the main.py file though
    app.run()
