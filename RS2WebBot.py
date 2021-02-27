import os
import sys
import importlib
import traceback
from json import load, dump
from DiscordDataTypes import Response
from flask import Flask, request, jsonify
from discord_interactions import verify_key_decorator
import GlobalCommands
import GuildCommands
import AdminCommands

sys.path.insert(0, os.path.dirname(__file__))


class RS2WebBot(Flask):
    def __init__(self, *args, **kwargs):
        self.CLIENT_PUBLIC_KEY = os.getenv('CLIENT_PUBLIC_KEY')

        self.BOT_TOKEN = os.getenv('BOT_TOKEN')

        self.HEADER = {'Application': f'Bot {self.BOT_TOKEN}'}

        self.CLIENT_ID = os.getenv('CLIENT_ID')

        def check_for_file(path, l=False):
            if not os.path.isfile(path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as wfile:
                    wfile.write(('[]' if l else'{}'))
                return False
            return True

        self.update_commands()

        check_for_file('./config.json')
        check_for_file('./data/active_guilds.json')

        self.bot_config = self.load_file('./config.json')
        self.active_guilds = self.load_file('./data/active_guilds.json')

        super().__init__(*args, **kwargs)

    def check_command(self, data):
        command = data['data']['name']
        if command in self.global_commands:
            return self.check_user(data)

        if command in self.guild_commands:
            if self.active_guilds[data['guild_id']]['premium']:
                return self.check_user(data)
            return Response('Upgrade to Premium to unlock these commands!')
        if command in self.admin_commands:
            return self.check_user(self.admin_commands, data, admin=True)

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
            return {'type': 4, data: {'content': f'An Error occured! Please contact a member of the -[FGC]- Team and provide the error message below :)\n**Command:** {command}\n**Error:** {e}'}}

    def update_commands(self, basic=True, premium=True, admin=True):
        if basic:
            importlib.reload(GlobalCommands)
            self.global_commands = GlobalCommands.GlobalCommands(self)
        if premium:
            importlib.reload(GuildCommands)
            self.guild_commands = GuildCommands.GuildCommands(self)
        if admin:
            importlib.reload(AdminCommands)
            self.admin_commands = AdminCommands.AdminCommands(self)
        return basic, premium, admin

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
