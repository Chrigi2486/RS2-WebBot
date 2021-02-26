import requests

BASE_URL = 'https://discord.com/api/v8'


class Application:

    def __init__(self, ID: int, TOKEN: str, global_commands: [Command] = None, guilds: [Guild] = None):
        self.ID = ID
        self.TOKEN = TOKEN
        self.global_commands = global_commands if global_commands else []
        self.guilds = guilds if guilds else []

    def get_command(self, command_ID):
        pass


class Guild:

    GUILDCOMMANDS_URL = BASE_URL + '/applications/{application_ID}/guilds/{guild_ID}/commands'

    def __init__(self, ID: int, commands: [Command] = None):
        self.ID = ID
        self.commands = commands if commands else []

    def get_commands(self):
        with requests.get(GUILDCOMMANDS_URL.format(self.application_ID, self.guild_ID)) as guild_commands_page:
            for guild_command in guild_commands_page.json:
                self.commands.append(GuildCommand.from_dict(guild_command))


class GlobalCommand(dict):

    COMMAND_URL = '/applications/{application_ID}/commands/{command_ID}'

    def __init__(self, name: str = None, description: str = None, options: [Option] = None, ID: int = None):
        self.name = name
        self.description = description
        self.options = options if options else []
        self.ID = ID

    @classmethod
    def from_ID(cls, application_ID, command_ID):
        with requests.get(cls.COMMAND_URL.format(application_ID, command_ID)) as command_page:



class GuildCommand(dict):

    def __init__(self, name: str = None, description: str = None, options: [Option] = None, ID: int = None):
        self.name = name
        self.description = description
        self.options = options
        self.ID = ID

    @classmethod
    def from_ID(cls, ID):
        with requests.get()
