class BaseCommand:
    name = "command"
    def __init__(self, name):
        self.name = name

    def action(self):
        pass

    @classmethod
    def execute(cls):
        cls.action()