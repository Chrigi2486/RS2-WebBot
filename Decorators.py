
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
    def guild_command(options=None):
        if options is None:
            options = []

        def register_command(func):
            func.command = True
            func.blueprint = {'type': 2, 'name': func.__name__, 'description': func.__doc__, 'options': []}
            func.options = [option.to_dict() for option in options]
            return func
        return register_command
