from Commands import Commands
from Decorators import Decorators


@Decorators.guild_commands
class GuildCommands(Commands):  # Make these commands a sub_command_group (type 2)

    def __init__(self, app):
        self.app = app

    def __str__(self):
        return 'Premium Commands'

    @Decorators.guild_command()
    def warn(self):
        pass

    @Decorators.guild_command()
    def kick(self):
        pass

    @Decorators.guild_command()
    def ban(self):
        pass

    @Decorators.guild_command()
    def banid(self):
        pass
