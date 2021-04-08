from Commands import Commands
from Decorators import Decorators
from HTTPWebAdmin import Route as WARoute
from HTTPWebAdmin import Parser as WAParser
from DiscordDataTypes import Response
from DiscordDataTypes import CommandOption as Option
from DiscordDataTypes import CommandOptionChoice as Choice


@Decorators.guild_commands
class GuildCommands(Commands):  # Make these commands a sub_command_group (type 2)
                                # Instead of subcommands I can just make it an option server with choices of the servers
    def __init__(self, app):
        self.app = app

    def __str__(self):
        return 'Premium Commands'

    @Decorators.guild_command(options=[Option("player", "The player to warn"), Option("warning", "The warning which should be given")])
    def warn(self):
        """Warn a player"""
        pass

    @Decorators.guild_command(options=[Option("player", "The player to kick"), Option("reason", "Reason to kick the player")])
    def kick(self):
        """Kick a player"""
        pass

    @Decorators.guild_command(options=[Option("player", "The player to ban"), Option("reason", "Reason to ban the player")])
    def ban(self):
        """Ban a player"""
        pass

    @Decorators.guild_command(options=[Option("player_id", "The ID to ban"), Option("reason", "Reason to ban the player")])
    def banid(self):
        """Bans a given ID"""
        pass

    @Decorators.guild_command(options=[Option("message", "The message to be sent"), Option("team", "The team to send the message to (not required)", required=False, choices=[Choice('North', '0'), Choice('South', '1')])])
    def write(self, data, guild_id, **kwargs):
        """Sends a given message"""
        server = data['options'][0]['name']
        webadminip, authcred = [value[0] for value in self.app.run_sql(f"SELECT SERVERS.WAIP, SERVERS.Authcred FROM SERVERS WHERE SERVERS.ID = {self.app.active_guilds[guild_id]['servers'][server]}")]
        message = data['options'][0]['options'][0]['value']
        if len(data['options'][0]['options']) == 2:
            team = data['options'][0]['options'][1]['value']
            print(server, webadminip, message, team)
            self.app.run_async(self.app.client.http.request(WARoute('GET', webadminip, '/current/chat/data?message={message}?teamsay={team}', message=message, team=team), cookies={'Authcred': authcred}))
        else:
            self.app.run_async(self.app.http.client.request(WARoute('GET', webadminip, '/current/chat/data?message={message}', message=message), cookies={'Authcred': authcred}))
        return Response('The message was sent!')
