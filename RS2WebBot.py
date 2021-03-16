import os
import sys
import importlib
import traceback
from json import load, dump
from HTTPDiscord import HTTPDiscord
from DiscordDataTypes import Response
from flask import Flask, request, jsonify
from discord_interactions import verify_key_decorator
import mysql.connector
import GlobalCommands
import GuildCommands
import AdminCommands

sys.path.insert(0, os.path.dirname(__file__))


class RS2WebBot(Flask):

    CLIENT_PUBLIC_KEY = os.getenv('CLIENT_PUBLIC_KEY')
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    HEADER = {'Authorization': f'Bot {BOT_TOKEN}'}
    CLIENT_ID = os.getenv('CLIENT_ID')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')

    def __init__(self, *args, **kwargs):

        self.discord = HTTPDiscord(self.BOT_TOKEN, self.CLIENT_ID)

        def check_for_file(path, l=False):
            if not os.path.isfile(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as wfile:
                    wfile.write(('[]' if l else'{}'))
                return False
            return True

        self.update_commands(True, True, True)

        check_for_file('./config.json')
        check_for_file('./data/active_guilds.json')

        self.bot_config = self.load_file('./config.json')
        self.active_guilds = self.load_file('./data/active_guilds.json')

        super().__init__(*args, **kwargs)

    def run_sql(self, command, *args):
        database = mysql.connector.connect(user='RS2WebBot', password=self.MYSQL_PASSWORD, host='127.0.0.1', database='RS2Database')
        cursor = database.cursor()
        cursor.excecute(command, *args)
        result = cursor.fetchall()
        cursor.close()
        database.close()
        return result

    def check_command(self, data):
        command = data['data']['name']
        if command in self.global_commands:
            return self.check_user(self.global_commands, data)

        if command in self.guild_commands:
            if self.active_guilds[data['guild_id']]['premium']:
                return self.check_user(self.guild_commands, data)
            return Response('Upgrade to Premium to unlock these commands!')
        if command in self.admin_commands:
            return self.check_user(self.admin_commands, data, admin=True)
        return Response(f'Command {command} not found')

    def check_user(self, commands, data, admin=False):
        if admin:
            if data['member']['user']['id'] in self.bot_config['validators']:
                return self.run_command(commands, data)
            return Response('You aren\'t authorised to use this command!')

        if 'guild_id' in self.active_guilds and self.active_guilds['guild_id']['validated']:
            if self.active_guilds[data['guild_id']]['admin'] in data['member']['roles']:
                return self.run_command(commands, data)
            return Response('You aren\'t authorised to use this command!')
        return Response('This Discord-Server must be validated by -[FGC]- before the bot can be used!')

    def run_command(self, commands, data):
        command = data['data']['name']
        try:
            return commands[command](commands, **data)
        except Exception as e:
            print(traceback.format_exc())
            return Response(f'An Error occured! Please contact a member of the -[FGC]- Team and provide the error message below :)\n**Command:** {command}\n**Error:** {e}')

    def update_commands(self, globalc=False, guildc=False, adminc=False):
        if globalc:
            importlib.reload(GlobalCommands)
            self.global_commands = GlobalCommands.GlobalCommands(self)
        if guildc:
            importlib.reload(GuildCommands)
            self.guild_commands = GuildCommands.GuildCommands(self)
        if adminc:
            importlib.reload(AdminCommands)
            self.admin_commands = AdminCommands.AdminCommands(self)
        return globalc, guildc, adminc

    def load_file(self, path):
        with open(path, 'r') as file:
            return load(file)

    def dump_file(self, path, data):
        with open(path, 'w') as file:
            dump(data, file)


app = RS2WebBot(__name__)


@app.route('/', methods=['GET'])
def status():
    return 'RS2-Web-Bot up and running'


@app.route('/', methods=['POST'])
@verify_key_decorator(app.CLIENT_PUBLIC_KEY)
def handle_command():
    if request.json['type'] == 2:
        return jsonify((app.check_command(request.json)).to_dict())


if __name__ == '__main__':
    app.run()
