import requests
from discord import Embed

BASE_URL = 'https://discord.com/api/v8'


class Application:

    def __init__(self, ID: int, TOKEN: str, global_commands: list = None, guilds: list = None):
        self.ID = ID
        self.TOKEN = TOKEN
        self.global_commands = global_commands if global_commands else []
        self.guilds = guilds if guilds else []

    def get_command(self, command_ID):
        pass


class Guild:

    GUILDCOMMANDS_URL = BASE_URL + '/applications/{application_ID}/guilds/{guild_ID}/commands'

    def __init__(self, ID: int, commands: list = None):
        self.ID = ID
        self.commands = commands if commands else []

    def get_commands(self):
        with requests.get(self.GUILDCOMMANDS_URL.format(self.application_ID, self.guild_ID)) as guild_commands_page:
            for guild_command in guild_commands_page.json:
                self.commands.append(GuildCommand.from_dict(guild_command))


class CommandOptionChoice:

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def to_dict(self):
        return {'name': self.name, 'value': self.value}


class SubCommand:

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def to_dict(self):
        return {'name': self.name, 'description': self.description}


class CommandOption:

    def __init__(self, name: str, description: str, otype: int = 3, required: bool = True, choices: [CommandOptionChoice] = None):
        self.name = name
        self.description = description
        self.otype = otype
        self.required = required
        self.choices = [] if choices is None else choices

    def to_dict(self):
        return {'name': self.name, 'description': self.description, 'type': self.otype, 'required': self.required, 'choices': [choice.to_dict() for choice in self.choices]}


class GlobalCommand:

    def __init__(self, name: str = None, description: str = None, options: [CommandOption, SubCommand] = [], ID: int = None):
        self.name = name
        self.description = description
        self.options = options
        self.ID = ID

    @classmethod
    def from_ID(cls, application_ID, command_ID):
        with requests.get(cls.COMMAND_URL.format(application_ID, command_ID)) as command_page:
            pass

    @classmethod
    def from_dict(cls, command_dict):
        pass

    def to_dict(self, ID: bool = False):
        ret = {'name': self.name, 'description': self.description, 'options': [option.to_dict() for option in self.options]}
        if ID:
            ret['id'] = self.ID
        return ret


class GuildCommand:

    def __init__(self, name: str = None, description: str = None, options: list = [], ID: int = None):
        self.name = name
        self.description = description
        self.options = options
        self.ID = ID

    @classmethod
    def from_ID(cls, ID):
        pass

    def to_dict(self, ID: bool = False):
        ret = {'name': self.name, 'description': self.description, 'options': [option.to_dict() for option in self.options]}
        if ID:
            ret['id'] = self.ID
        return ret


class Response:

    def __init__(self, content: str = None, embed: Embed = None, embeds: list = [], tts: bool = False, allowed_mentions: [] = [], mtype: int = 4):
        self.mtype = mtype
        self.data = {'tts': tts, 'content': content, 'embeds': ([embed.to_dict()] if embed else [embed.to_dict() for embed in embeds]), 'allowed_mentions': allowed_mentions}

    def to_dict(self):
        return {'type': self.mtype, 'data': self.data}


class Message:
    def __init__(self, content: str = None, embed: Embed = None, embeds: list = [], tts: bool = False, allowed_mentions: [] = []):
        self.data = {'tts': tts, 'content': content, 'embeds': ([embed.to_dict()] if embed else [embed.to_dict() for embed in embeds]), 'allowed_mentions': allowed_mentions}

    def to_dict(self):
        return self.data
