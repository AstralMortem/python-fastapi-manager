class BaseCommand:
    name = "command"
    def __init__(self, name):
        self.name = name

    @classmethod
    def execute(cls):
        raise NotImplementedError