
import os
import asyncio
from discord import Embed, File
from Commands import Commands
from Decorators import Decorators
from DiscordDataTypes import Response


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
    async def stats(self, **kwargs):
        """displays the current bot status (connected, validated, premium guilds)"""
        embed = Embed(title='Active Servers', color=0xD84800)
        guilds = await self.app.client.fetch_guilds().flatten()
        [embed.add_field(name=guild.name, value=f"ID: {guild.id}\nValidated: {'False' if str(guild.id) not in self.app.active_guilds else str(self.app.active_guilds[str(guild.id)]['validated'])}\nPremium: {'False' if str(guild.id) not in self.app.active_guilds else str(self.app.active_guilds[str(guild.id)]['premium'])}") for guild in guilds]
        return Response(embed=embed)

    @Decorators.command()
    async def update(self, data, **kwargs):
        """Use with caution. Parameters: basic, premium, admin"""
        to_update = {option['name']: option['value'] for option in (data['options'] if 'options' in data else [])}
        globalc, guildc, adminc = self.app.update_commands(**to_update)
        print(f'Updated:\nGlobal:{globalc}\nGuild:{guildc}\nAdmin:{adminc}')
        return Response(f'Updated:\nGlobal: {globalc}\nGuild: {guildc}\nAdmin: {adminc}')

    @Decorators.command('Guild_ID', 'Role_ID')
    async def validate(self, data, **kwargs):
        """validates the given guild by ID"""
        guild_ID, role_ID = [option['value'] for option in data['options']]

        guild = await self.app.client.fetch_guild(guild_ID)
        if guild_ID not in self.app.active_guilds.keys():
            self.app.active_guilds[guild_ID] = {'admin': role_ID, 'validated': True, 'premium': False, 'servers': {}, 'commands': {}}
        else:
            if self.app.active_guilds[guild_ID]['validated']:
                return Response('Server is already validated')
            self.app.active_guilds[guild_ID]['validated'] = True
            self.app.active_guilds[guild_ID]['admin'] = role_ID
        post_requests = []
        for command in self.guild_command_blueprints:
            post_requests.append(self.app.create_guild_command(guild_ID, self.guild_command_blueprints[command]))
        command_infos = await asyncio.gather(*post_requests, loop=self.app.client.loop)
        for command in command_infos:
            self.app.active_guilds[guild_ID]['commands'][command['name']] = command['id']
        self.app.dump_file(self.app.bot_config['paths']['active_guilds'], self.app.active_guilds)
        return Response(f"{guild.name} - {guild_ID} has been validated!")

    @Decorators.command('Guild_ID')
    async def premium(self, data, **kwargs):
        """rewards the given guild premium by ID"""
        guild_ID = data['options'][0]['value']
        if guild_ID not in self.app.active_guilds or not self.app.active_guilds[guild_ID]['validated']:
            return Response('Server must be validated first')
        self.app.active_guilds[guild_ID]['premium'] = True
        self.app.dump_file(self.app.bot_config['paths']['active_guilds'], self.app.active_guilds)
        guild_name = (await self.app.client.fetch_guild(guild_ID)).name
        return Response(f'{guild_name} - {guild_ID} has been awarded with premium!')

    @Decorators.command('Guild_ID')
    async def revoke(self, data, **kwargs):
        """revokes the given guild by ID"""
        guild_ID = data['options'][0]['value']
        if guild_ID not in self.app.active_guilds:
            return Response('Guild not found')
        if not self.app.active_guilds[guild_ID]['validated']:
            return Response('Guild already revoked')
        self.app.active_guilds[guild_ID]['validated'] = False
        self.app.active_guilds[guild_ID]['premium'] = False
        self.app.dump_file(self.app.bot_config['paths']['active_guilds'], self.app.active_guilds)
        guild_name = (await self.app.client.fetch_guild(guild_ID)).name
        return Response(f'{guild_name} - {guild_ID} has been revoked!')

    @Decorators.command('File_Path')
    async def download(self, data, **kwargs):
        """sends you the file at the given path"""
        file_path = data['options'][0]['value']
        if not os.path.isfile(file_path):
            return Response('File not found!')
        elif '..' in file_path:
            return Response('Files out of the directory are restricted!')
        await self.app.client.http.send_file(file=File(file_path))
        print(f'File was downloaded {file_path}')
        return Response(f'{file_path} has been sent')

    @Decorators.command('File_Path')
    async def upload(self, data, channel_id, **kwargs):
        """saves the given file to the given path"""
        file_path, message_id = [option['value'] for option in data['options']]
        message = await (await self.app.client.fetch_channel(channel_id)).fetch_message(message_id)
        if not message.attachments:
            return Response('Attach the file to be uploaded')
        await message.attachments[0].save(file_path)
        print(f'File was uploaded to {file_path}')
        return Response('File has been uploaded. Use +load to override the current Data')

    @Decorators.command('File')
    async def dump(self, data, **kwargs):
        """dumps the given file"""
        file = data['options'][0]['value']
        if file == 'active_guilds':
            self.app.dump_file(self.app.bot_config['paths']['active_guilds'], self.app.active_guilds)
        elif file == 'config':
            self.app.dump_file('./config.json', self.app.bot_config)
        else:
            return Response('File wasn\'t found')
        print(f'{file} was dumped')
        return Response(f'{file} was dumped')

    @Decorators.command('File')
    async def load(self, data, **kwargs):
        """loads the given file"""
        file = data['options'][0]['value']
        if file == 'active_guilds':
            self.app.active_guilds = self.app.load_file(self.app.bot_config['paths']['active_guilds'])
        elif file == 'config':
            self.app.bot_config = self.app.load_file('./config.json')
        else:
            return Response('File wasn\'t found')
        print(f'{file} was loaded')
        return Response(f'{file} was loaded')

    @Decorators.command()
    async def sql(self, data, **kwargs):
        command = data['options'][0]['value']
        result = self.app.run_sql(command)
        return Response(str(result))

    @Decorators.command()
    async def restart(self, data, **kwargs):
        if not self.app.server_tasks:
            return Response("This should only be used if the bot has been restarted")
        for id in self.app.bot_config['liveinfo']:
            task = self.app.add_async(self.app.live_info(id))
            self.app.server_tasks.append(task)
        return Response()

    @Decorators.command()
    async def dummy(self, data, **kwargs):
        return Response(str([x[0] for x in os.walk('/mnt')]))
