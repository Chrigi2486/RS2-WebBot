import importlib
from discord import Embed
from Commands import Commands
from Decorators import Decorators
from HTTPDiscord import Route
import GuildCommands
from DiscordDataTypes import Response, Message


@Decorators.commands
class AdminCommands(Commands):

    def __init__(self, app):
        self.app = app
        self.guild_command_blueprints = self.app.guild_commands.command_blueprints

    def __str__(self):
        return 'Admin Commands'

    # @Decorators.command()
    # async def adminhelp(self, app, message):
    #     """displays the admin commands"""
    #     await message.channel.send(app.list_commands(app.basic_commands, app.premium_commands, app.admin_commands))

    @Decorators.command()
    def stats(self, **kwargs):
        """displays the current bot status (connected, validated, premium guilds)"""
        embed = Embed(title='Active Servers', color=0xD84800)
        guilds = self.app.run_async(self.app.client.fetch_guilds().flatten())
        [embed.add_field(name=guild.name, value=f"ID: {guild.id}\nValidated: {'False' if str(guild.id) not in self.app.active_guilds else str(self.app.active_guilds[str(guild.id)]['validated'])}\nPremium: {'False' if str(guild.id) not in self.app.active_guilds else str(self.app.active_guilds[str(guild.id)]['premium'])}") for guild in guilds]
        return Response(embed=embed)

    @Decorators.command()
    def update(self, data, **kwargs):
        """Use with caution. Parameters: basic, premium, admin"""
        to_update = {option['name']: option['value'] for option in (data['options'] if 'options' in data else [])}
        globalc, guildc, adminc = self.app.update_commands(**to_update)
        print(f'Updated:\nGlobal:{globalc}\nGuild:{guildc}\nAdmin:{adminc}')
        return Response(f'Updated:\nGlobal: {globalc}\nGuild: {guildc}\nAdmin: {adminc}')

    @Decorators.command('Guild_ID', 'Role_ID')
    def validate(self, data, **kwargs):
        """validates the given guild by ID"""
        guild_ID, role_ID = [option['value'] for option in data['options']]

        guild = self.app.run_async(self.app.client.fetch_guild(guild_ID))
        if guild_ID not in self.app.active_guilds.keys():
            self.app.active_guilds[guild_ID] = {'admin': role_ID, 'validated': True, 'premium': False, 'servers': {}, 'commands': {}}
        else:
            if self.app.active_guilds[guild_ID]['validated']:
                return Response('Server is already validated')
            self.app.active_guilds[guild_ID]['validated'] = True
            self.app.active_guilds[guild_ID]['admin'] = role_ID
        self.app.dump_file('./data/active_guilds.json', self.app.active_guilds)
        return Response(f"{guild.name} - {guild_ID} has been validated!")

    @Decorators.command('Guild_ID')
    def premium(self, data, **kwargs):
        """rewards the given guild premium by ID"""
        guild_ID = data['options'][0]['value']
        if guild_ID not in self.app.active_guilds or not self.app.active_guilds[guild_ID]['validated']:
            return Response('Server must be validated first')
        self.app.active_guilds[guild_ID]['premium'] = True
        self.app.dump_file('./data/active_guilds.json', self.app.active_guilds)
        for command in self.guild_command_blueprints:
            resp = self.app.create_guild_command(guild_ID, self.guild_command_blueprints[command])
            self.app.active_guilds[guild_id]['commands'][command] = resp['id']
        return Response(f'{self.app.run_async(self.app.client.fetch_guild(guild_ID)).name} - {guild_ID} has been awarded with premium!')

    @Decorators.command('Guild_ID')
    def revoke(self, data, **kwargs):
        """revokes the given guild by ID"""
        guild_ID = data['options'][0]['value']
        if guild_ID not in self.app.active_guilds:
            return Response('Guild not found')
        if not self.app.active_guilds[guild_ID]['validated']:
            return Response('Guild already revoked')
        self.app.active_guilds[guild_ID]['validated'] = False
        self.app.active_guilds[guild_ID]['premium'] = False
        self.app.dump_file('./data/active_guilds.json', self.app.active_guilds)
        return Response(f'{self.app.run_async(self.app.client.fetch_guild(guild_ID)).name} - {guild_ID} has been revoked!')

    # @Decorators.command('File_Path')
    # async def download(self, app, message, file_path):
    #     """sends you the file at the given path"""
    #     if not os.path.isfile(file_path):
    #         await message.channel.send('File not found!')
    #     elif '..' in file_path:
    #         await message.channel.send('Fuck you, no')
    #     else:
    #         await message.channel.send(file=discord.File(file_path))
    #         print(f'File was downloaded {file_path}')

    # @Decorators.command('File_Path')
    # async def upload(self, app, message, file_path):
    #     """saves the given file to the given path"""
    #     if not message.attachments:
    #         await message.channel.send('Attach the file to be uploaded')
    #         return
    #     await message.attachments[0].save(file_path)
    #     await message.channel.send('File has been uploaded. Use +load to override the current Data')
    #     print(f'File was uploaded to {file_path}')

    @Decorators.command('File')
    def dump(self, data, **kwargs):
        """dumps the given file"""
        file = data['options'][0]['value']
        if file == 'active_guilds':
            self.app.dump_file('./data/active_guilds.json', self.app.active_guilds)
        elif file == 'config':
            self.app.dump_file('./config.json', self.app.config)
        else:
            return Response('File wasn\'t found')
        print(f'{file} was dumped')
        return Response(f'{file} was dumped')

    @Decorators.command('File')
    def load(self, data, **kwargs):
        """loads the given file"""
        file = data['options'][0]['value']
        if file == 'active_guilds':
            self.app.active_guilds = self.app.load_file('./data/active_guilds.json')
        elif file == 'config':
            self.app.config = self.app.load_file('./config.json')
        else:
            return Response('File wasn\'t found')
        print(f'{file} was loaded')
        return Response(f'{file} was loaded')

    @Decorators.command()
    def sql(self, data, **kwargs):
        command = data['options'][0]['value']
        result = self.app.run_sql(command)
        return Response(str(result))
