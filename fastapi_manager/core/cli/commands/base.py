class BaseCommand:
    name = "command"
    def __init__(self, name):
        self.name = name

    @classmethod
    def execute(cls, *args, **kwargs):
        raise NotImplementedError