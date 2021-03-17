import os
import requests
from discord import Embed
from Commands import Commands
from Decorators import Decorators
from DiscordDataTypes import Response, Message


@Decorators.commands
class AdminCommands(Commands):

    def __init__(self, app):
        self.app = app

    def __str__(self):
        return 'Admin Commands'

    @Decorators.command()
    async def adminhelp(self, app, message):
        """displays the admin commands"""
        await message.channel.send(app.list_commands(app.basic_commands, app.premium_commands, app.admin_commands))

    @Decorators.command()
    def stats(self, **kwargs):
        """displays the current bot status (connected, validated, premium guilds)"""
        embed = Embed(title='Active Servers', color=0xD84800)
        guilds = self.app.run_async(self.app.client.fetch_guilds().flatten())
        [embed.add_field(name=guild.name, value=f"ID: {guild.id}\nValidated: {'False' if guild.id not in self.app.active_guilds else str(self.app.active_guilds[guild.id]['validated'])}\nPremium: {'False' if guild.id not in self.app.active_guilds else str(self.app.active_guilds[guild.id]['premium'])}") for guild in guilds]
        return Response(embed=embed)

    @Decorators.command()
    def update(self, data, **kwargs):
        """Use with caution. Parameters: basic, premium, admin"""
        globalc, guildc, adminc = self.app.update_commands(**{option['name']: option['value'] for option in (data['options'] if 'options' in data else [])})
        print(f'Updated:\nGlobal:{globalc}\nGuild:{guildc}\nAdmin:{adminc}')
        return Response(f'Updated:\nGlobal: {globalc}\nGuild: {guildc}\nAdmin: {adminc}')

    @Decorators.command('Guild_ID', 'Role_ID')
    def validate(self, data, **kwargs):
        """validates the given guild by ID"""
        guild_ID = data['options'][0]['value']
        print(guild_ID)
        role_ID = data['options'][1]['value']
        guild = self.app.run_async(self.app.client.fetch_guild(guild_ID))
        if guild_ID not in self.app.active_guilds.keys():
            self.app.active_guilds[guild_ID] = {'admin': role_ID, 'validated': True, 'premium': False, 'servers': []}
            os.makedirs(os.path.dirname(f'./data/{guild_ID}/'), exist_ok=True)
        else:
            if self.app.active_guilds[guild_ID]['validated']:
                return Response('Server is already validated')
            self.app.active_guilds[guild_ID]['validated'] = True
            self.app.active_guilds[guild_ID]['admin'] = role_ID
        self.app.dump_file('./data/active_guilds.json', self.app.active_guilds)
        return Response(f"{guild.name} - {guild_ID} has been validated!")

    @Decorators.command('Guild_ID')
    def premium(self, app, message, guild_ID):
        """rewards the given guild premium by ID"""
        if guild_ID not in self.app.active_guilds.keys() or not self.app.active_guilds[guild_ID]['validated']:
            return Response('Server must be validated first')
        self.app.active_guilds[guild_ID]['premium'] = True
        self.app.dump_file('./data/active_guilds.json', app.active_guilds)
        return Response(f'{app.get_guild(int(guild_ID)).name} - {guild_ID} has been awarded with premium!')

    @Decorators.command('Guild_ID')
    def revoke(self, app, message, guild_ID):
        """revokes the given guild by ID"""
        if guild_ID not in self.app.active_guilds.keys():
            return Response('Server not found')
        if not self.app.active_guilds[guild_ID]['validated']:
            return Response('Server already revoked')
        self.app.active_guilds[guild_ID]['validated'] = False
        self.app.active_guilds[guild_ID]['premium'] = False
        self.app.dump_file('./data/active_guilds.json', self.app.active_guilds)
        return Response(f'{app.get_guild(int(guild_ID)).name} - {guild_ID} has been revoked!')

    @Decorators.command('File_Path')
    async def download(self, app, message, file_path):
        """sends you the file at the given path"""
        if not os.path.isfile(file_path):
            await message.channel.send('File not found!')
        elif '..' in file_path:
            await message.channel.send('Fuck you, no')
        else:
            await message.channel.send(file=discord.File(file_path))
            print(f'File was downloaded {file_path}')

    @Decorators.command('File_Path')
    async def upload(self, app, message, file_path):
        """saves the given file to the given path"""
        if not message.attachments:
            await message.channel.send('Attach the file to be uploaded')
            return
        await message.attachments[0].save(file_path)
        await message.channel.send('File has been uploaded. Use +load to override the current Data')
        print(f'File was uploaded to {file_path}')

    @Decorators.command('File')
    async def dump(self, app, message, file):
        """dumps the given file"""
        if file == 'active_guilds':
            app.dump_file('./data/active_guilds.json', app.active_guilds)
        elif file == 'config':
            app.dump_file('./config.json', app.config)
        else:
            await message.channel.send('File wasn\'t found')
            return
        await message.channel.send(f'{file} was dumped')
        print(f'{file} was dumped')

    @Decorators.command('File')
    async def load(self, app, message, file):
        """loads the given file"""
        if file == 'active_guilds':
            app.active_guilds = app.load_file('./data/active_guilds.json')
        elif file == 'config':
            app.config = app.load_file('./config.json')
        else:
            await message.channel.send('File wasn\'t found')
            return
        await message.channel.send(f'{file} was loaded')
        print(f'{file} was loaded')

    @Decorators.command
    def add_command(self, data):
        pass
