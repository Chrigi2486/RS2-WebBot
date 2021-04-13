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
    def kick(self, data, guild_id, **kwargs):
        """Kick a player"""
        server = data['options'][0]['name']
        player_info, reason = [option['value'] for option in data['options'][0]['options']]
        player_db_id, player_id, player_key = player_info.split(',')
        server_id = self.app.active_guilds[guild_id]['servers'][server]
        player_name, platform_id = self.app.run_sql(f'SELECT PLAYERS.Name, PLAYERS.PlatformID FROM PLAYERS WHERE PLAYERS.ID = {player_db_id}')[0]
        webadminip, authcred = self.app.run_sql(f"SELECT SERVERS.WAIP, SERVERS.Authcred FROM SERVERS WHERE SERVERS.ID = {server_id}")[0]
        self.app.run_async # FINISH HERE
        return Response(f'{player_name} was kicked for {reason}\nPlatform ID: {platform_id}')

    @Decorators.guild_command(options=[Option("player", "The player to ban"), Option("reason", "Reason to ban the player")])
    def ban(self, data, guild_id, **kwargs):
        """Ban a player"""
        server = data['options'][0]['name']
        player_info, reason = [option['value'] for option in data['options'][0]['options']]
        player_db_id, player_id, player_key = player_info.split(',')
        server_id = self.app.active_guilds[guild_id]['servers'][server]
        player_name, platform_id = self.app.run_sql(f'SELECT PLAYERS.Name, PLAYERS.PlatformID FROM PLAYERS WHERE PLAYERS.ID = {player_db_id}')[0]
        webadminip, authcred = self.app.run_sql(f"SELECT SERVERS.WAIP, SERVERS.Authcred FROM SERVERS WHERE SERVERS.ID = {server_id}")[0]
        self.app.run_async(self.app.client.http.request(WARoute('GET', webadminip, '/ServerAdmin/current/players?action=banid?playerid={player_id}?playerkey={player_key}?__Reason={reason}?NotifyPlayers=0?__IdType=0?__ExpUnit=Never', player_id=player_id, player_key=player_key, reason=reason), cookies={'Authcred': authcred}))
        self.app.run_async(self.app.client.http.request(WARoute('GET', webadminip, '/ServerAdmin/policy/bans?action=add?__UniqueId={platform_id}?__Reason={reason}?NotifyPlayers=0?__IdType=1?__ExpUnit=Never', platform_id=platform_id, reason=reason), cookies={'Authcred': authcred}))
        ban_id = self.app.run_sql('INSERT INTO BANS(PID, SID, Date, Reason) VALUES(%s, %s, NOW(), %s)', player_db_id, server_id, reason, ret_ID=True)
        return Response(f'{player_name} was banned for {reason}\nPlatform ID: {platform_id}\nBan ID: {ban_id}')

    @Decorators.guild_command(options=[Option("player_id", "The ID to ban"), Option("reason", "Reason to ban the player")])
    def banid(self, data, guild_id, **kwargs):
        """Bans a given ID"""
        server = data['options'][0]['name']
        platform_id, reason = [option['value'] for option in data['options'][0]['options']]
        server_id = self.app.active_guilds[guild_id]['servers'][server]
        webadminip, authcred = self.app.run_sql(f"SELECT SERVERS.WAIP, SERVERS.Authcred FROM SERVERS WHERE SERVERS.ID = {server_id}")[0]
        self.app.run_async(self.app.client.http.request(WARoute('GET', webadminip, '/ServerAdmin/policy/bans?action=add?__UniqueId={platform_id}?__Reason={reason}?NotifyPlayers=0?__IdType=1?__ExpUnit=Never', platform_id=platform_id, reason=reason), cookies={'Authcred': authcred}))
        player_id = self.app.run_sql('SELECT PLAYERS.ID FROM PLAYERS WHERE PLAYERS.PlatformID = %s', platform_id)
        if not player_id:
            platform = 'Steam' if len(player_id) > 10 else 'EGS'
            player_id = self.app.run_sql('INSERT INTO PLAYERS(Platform, PlatformID) VALUES(%s, %s)', platform, platform_id, ret_ID=True)
        ban_id = self.app.run_sql('INSERT INTO BANS(PID, SID, Date, Reason) VALUES(%s, %s, NOW(), %s)', player_id, server_id, reason, ret_ID=True)
        return Response(f'{platform_id} was banned for {reason}\nBan ID: {ban_id}')

    @Decorators.guild_command(options=[Option("message", "The message to be sent"), Option("team", "The team to send the message to (not required)", required=False, choices=[Choice('North', '0'), Choice('South', '1')])])
    def write(self, data, guild_id, **kwargs):
        """Sends a given message"""
        server = data['options'][0]['name']
        webadminip, authcred = self.app.run_sql(f"SELECT SERVERS.WAIP, SERVERS.Authcred FROM SERVERS WHERE SERVERS.ID = {self.app.active_guilds[guild_id]['servers'][server]}")[0]
        message = data['options'][0]['options'][0]['value']
        if len(data['options'][0]['options']) == 2:
            team = data['options'][0]['options'][1]['value']
            print(server, webadminip, message, team)
            self.app.run_async(self.app.client.http.request(WARoute('GET', webadminip, '/current/chat/data?message={message}?teamsay={team}', message=message, team=team), cookies={'Authcred': authcred}))
        else:
            self.app.run_async(self.app.http.client.request(WARoute('GET', webadminip, '/current/chat/data?message={message}', message=message), cookies={'Authcred': authcred}))
        return Response('The message was sent!')
