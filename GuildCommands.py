from Commands import Commands
from Decorators import Decorators


@Decorators.commands
class GuildCommands(Commands):

    def __init__(self, client):
        self.client = client

    def __str__(self):
        return 'Premium Commands'
