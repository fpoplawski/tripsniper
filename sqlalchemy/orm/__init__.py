class Session:
    def __init__(self, *args, **kwargs):
        pass

    def execute(self, *args, **kwargs):  # pragma: no cover
        return []

    def scalars(self):  # pragma: no cover
        return self

    def all(self):  # pragma: no cover
        return []

    def add_all(self, items):  # pragma: no cover
        pass

    def commit(self):  # pragma: no cover
        pass

    def close(self):  # pragma: no cover
        pass


def sessionmaker(bind=None):
    class _SessionFactory:
        def __call__(self):
            return Session()
    return _SessionFactory()

