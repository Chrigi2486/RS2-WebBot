import asyncio
import datetime
from discord import Embed, Client
from discord.iterators import GuildIterator
from discord.utils import time_snowflake
from discord.object import Object

BASE_URL = 'https://discord.com/api/v8'


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


class Response:  # reengineer Response object

    def __init__(self, content: str = None, embed: Embed = None, embeds: list = [], tts: bool = False, allowed_mentions: [] = [], mtype: int = 4):
        self.mtype = mtype
        self.data = {'tts': tts, 'content': content, 'embeds': ([embed.to_dict()] if embed else [embed.to_dict() for embed in embeds]), 'allowed_mentions': allowed_mentions}

    def to_dict(self):  # move the to_dicts in self.data to here
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


class CustomGuildIterator(GuildIterator):
    def __init__(self, bot, limit, before=None, after=None):

        if isinstance(before, datetime.datetime):
            before = Object(id=time_snowflake(before, high=False))
        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))

        self.bot = bot
        self.limit = limit
        self.before = before
        self.after = after

        self._filter = None

        self.state = self.bot._connection
        self.get_guilds = self.bot.http.get_guilds
        self.guilds = asyncio.Queue(loop=bot.loop)

        if self.before and self.after:
            self._retrieve_guilds = self._retrieve_guilds_before_strategy  # type: ignore
            self._filter = lambda m: int(m['id']) > self.after.id
        elif self.after:
            self._retrieve_guilds = self._retrieve_guilds_after_strategy  # type: ignore
        else:
            self._retrieve_guilds = self._retrieve_guilds_before_strategy  # type: ignore


class CustomClient(Client):
    def fetch_guilds(self, *, limit=100, before=None, after=None):
        return CustomGuildIterator(self, limit=limit, before=before, after=after)
