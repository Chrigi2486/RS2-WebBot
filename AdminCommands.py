import os
import requests
from discord import Embed
from Commands import Commands
from Decorators import Decorators
from DiscordDataTypes import Response, Message


@Decorators.commands
class AdminCommands(Commands):

    def __init__(self, client):
        self.client = client

    def __str__(self):
        return 'Admin Commands'

    @Decorators.command()
    async def adminhelp(self, client, message):
        """displays the admin commands"""
        await message.channel.send(client.list_commands(client.basic_commands, client.premium_commands, client.admin_commands))

    @Decorators.command()
    def stats(self, **kwargs):
        """displays the current bot status (connected, validated, premium guilds)"""
        embed = Embed(title='Active Servers', color=0xD84800)
        guilds = self.client.discord.get_guilds()
        [embed.add_field(name=guild['name'], value=f"ID: {guild['id']}\nValidated: {'False' if guild['id'] not in self.client.active_guilds.keys() else str(self.client.active_guilds[guild['id']]['validated'])}\nPremium: {'False' if guild['id'] not in self.client.active_guilds.keys() else str(self.client.active_guilds[guild['id']]['premium'])}") for guild in guilds]
        return Response(embed=embed)

    @Decorators.command()
    def update(self, data, **kwargs):
        """Use with caution. Parameters: basic, premium, admin"""
        basic, premium, admin = self.client.update_commands(**{option['name']: option['value'] for option in (data['options'] if 'options' in data else [])})
        print(f'Updated:\nBasic:{basic}\nPremium:{premium}\nAdmin:{admin}')
        return Response(f'Updated:\nBasic:{basic}\nPremium:{premium}\nAdmin:{admin}')

    @Decorators.command('Guild_ID', 'Role_ID')
    def validate(self, client, message, guild_ID, role_ID):
        """validates the given guild by ID"""
        if guild_ID not in self.client.active_guilds.keys():
            self.client.active_guilds[guild_ID] = {'admin': role_ID, 'validated': True, 'premium': False, 'servers': []}
            os.makedirs(os.path.dirname(f'./data/{guild_ID}/'), exist_ok=True)
        else:
            if self.client.active_guilds[guild_ID]['validated']:
                return Response('Server is already validated')
            self.client.active_guilds[guild_ID]['validated'] = True
            self.client.active_guilds[guild_ID]['admin'] = role_ID
        self.client.dump_file('./data/active_guilds.json', self.client.active_guilds)
        return Response(f'{client.get_guild(int(guild_ID)).name} - {guild_ID} has been validated!')

    @Decorators.command('Guild_ID')
    def premium(self, client, message, guild_ID):
        """rewards the given guild premium by ID"""
        if guild_ID not in self.client.active_guilds.keys() or not self.client.active_guilds[guild_ID]['validated']:
            return Response('Server must be validated first')
        self.client.active_guilds[guild_ID]['premium'] = True
        self.client.dump_file('./data/active_guilds.json', client.active_guilds)
        return Response(f'{client.get_guild(int(guild_ID)).name} - {guild_ID} has been awarded with premium!')

    @Decorators.command('Guild_ID')
    def revoke(self, client, message, guild_ID):
        """revokes the given guild by ID"""
        if guild_ID not in self.client.active_guilds.keys():
            return Response('Server not found')
        elif not self.client.active_guilds[guild_ID]['validated']:
            return Response('Server already revoked')
        self.client.active_guilds[guild_ID]['validated'] = False
        self.client.active_guilds[guild_ID]['premium'] = False
        self.client.dump_file('./data/active_guilds.json', self.client.active_guilds)
        return Response(f'{client.get_guild(int(guild_ID)).name} - {guild_ID} has been revoked!')

    @Decorators.command('File_Path')
    async def download(self, client, message, file_path):
        """sends you the file at the given path"""
        if not os.path.isfile(file_path):
            await message.channel.send('File not found!')
        elif '..' in file_path:
            await message.channel.send('Fuck you, no')
        else:
            await message.channel.send(file=discord.File(file_path))
            print(f'File was downloaded {file_path}')

    @Decorators.command('File_Path')
    async def upload(self, client, message, file_path):
        """saves the given file to the given path"""
        if not message.attachments:
            await message.channel.send('Attach the file to be uploaded')
            return
        await message.attachments[0].save(file_path)
        await message.channel.send('File has been uploaded. Use +load to override the current Data')
        print(f'File was uploaded to {file_path}')

    @Decorators.command('File')
    async def dump(self, client, message, file):
        """dumps the given file"""
        if file == 'active_guilds':
            client.dump_file('./data/active_guilds.json', client.active_guilds)
        elif file == 'config':
            client.dump_file('./config.json', client.config)
        else:
            await message.channel.send('File wasn\'t found')
            return
        await message.channel.send(f'{file} was dumped')
        print(f'{file} was dumped')

    @Decorators.command('File')
    async def load(self, client, message, file):
        """loads the given file"""
        if file == 'active_guilds':
            client.active_guilds = client.load_file('./data/active_guilds.json')
        elif file == 'config':
            client.config = client.load_file('./config.json')
        else:
            await message.channel.send('File wasn\'t found')
            return
        await message.channel.send(f'{file} was loaded')
        print(f'{file} was loaded')

    @Decorators.command
    def add_command(self, data):
        pass
