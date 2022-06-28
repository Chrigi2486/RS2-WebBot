import asyncio
import datetime
from discord import Embed, Client
from discord.iterators import GuildIterator
from discord.utils import time_snowflake
from discord.object import Object

BASE_URL = 'https://discord.com/api/v8'

# These classes are to make the general code more legible. They take the complex dictionary structures given by Discord and makes it a bit easier to handle
# Check Discord Slash Commands Documentation https://discord.com/developers/docs/interactions/application-commands
# To figure out the structure of the dictionaries returned by Discord 


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
    # If you don't know about typing in Python ___ <- under there (str) shows what type the variable should be. In this case description has to be a string
    def __init__(self, name: str, description: str, otype: int = 3, required: bool = True, choices: [CommandOptionChoice] = None, autocomplete: bool = False):  # Wow, I actually did typing in Python lmao
        self.name = name
        self.description = description
        self.otype = otype
        self.required = required
        self.choices = [] if choices is None else choices
        self.autocomplete = autocomplete

    def to_dict(self):
        return {'name': self.name, 'description': self.description, 'type': self.otype, 'required': self.required, 'choices': [choice.to_dict() for choice in self.choices], 'autocomplete': self.autocomplete}


class Response:  # reengineer Response object. Maybe don't fix what isn't broken lmao

    def __init__(self, content: str = None, embed: Embed = None, embeds: list = [], tts: bool = False, allowed_mentions: [] = [], mtype: int = 4):
        self.mtype = mtype
        self.data = {'tts': tts, 'content': content, 'embeds': ([embed.to_dict()] if embed else [embed.to_dict() for embed in embeds]), 'allowed_mentions': allowed_mentions}

    def to_dict(self):  # move the to_dicts in self.data to here (or not, doesn't matter)
        return {'type': self.mtype, 'data': self.data}


class AutoCompleteResponse:

    def __init__(self, choices: [CommandOptionChoice], mtype: int = 8):
        self.mtype = mtype
        self.choices = choices

    def to_dict(self):
        return {'type': self.mtype, 'data': {'choices': [choice.to_dict() for choice in self.choices]}}


class Message:
    def __init__(self, content: str = None, embed: Embed = None, embeds: list = [], tts: bool = False, allowed_mentions: [] = []):
        self.data = {'tts': tts, 'content': content, 'embeds': ([embed.to_dict()] if embed else [embed.to_dict() for embed in embeds]), 'allowed_mentions': allowed_mentions}

    def to_dict(self):
        return self.data
