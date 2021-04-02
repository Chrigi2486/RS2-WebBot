from Commands import Commands
from Decorators import Decorators
from DiscordDataTypes import CommandOption as Option


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
