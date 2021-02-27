

class Decorators:

    @staticmethod
    def commands(inst):
        inst.commands = dict()
        for name, func in inst.__dict__.items():
            if hasattr(func, 'command'):
                inst.commands[name] = func
        return inst

    @staticmethod
    def command(*args):
        def register_command(func):
            func.command = True
            return func
        return register_command
