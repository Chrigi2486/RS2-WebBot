
class Decorators:

    @staticmethod
    def commands(inst):
        inst.commands = dict()
        for name, func in inst.__dict__.items():
            if hasattr(func, 'command'):
                inst.commands[name] = func
        return inst

    @staticmethod
    def guild_commands(inst):
        inst.commands = dict()
        inst.command_blueprints = dict()
        for name, func in inst.__dict__.items():
            if hasattr(func, 'command'):
                inst.commands[name] = func
                inst.command_blueprints[name] = func.blueprint
                inst.command_options[name] = func.options
        return inst

    @staticmethod
    def command(*args):
        def register_command(func):
            func.command = True
            return func
        return register_command

    @staticmethod
    def guild_command(blueprint, options=[]):
        def register_command(func):
            func.command = True
            func.blueprint = blueprint
            func.options = options
            return func
        return register_command
