

class Commands:

    def __getitem__(self, val):
        if type(val) is str:
            return self.commands[val]

    def __iter__(self):
        yield from self.commands
