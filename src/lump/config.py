import configparser


class Config:
    """
    Helper class for easier config loading with sensible defaults
    """
    def __init__(self, config=None, section=None):
        if config is None:
            config = 'config.ini'
        if type(config) is str:
            config_file = config
            config = configparser.ConfigParser()
            config.read(config_file)
        if section and section in config:
            config = config[section]

        self.config = config
        self.overrides = {}

    def __getattr__(self, name):
        if name in self.overrides:
            return self.overrides[name]
        if name in self.config:
            return self.config[name]
        raise KeyError(name)

    def __contains__(self, key):
        return key in self.config or key in self.overrides

    def __getitem__(self, key):
        return self.__getattr__(key)

    def update(self, vals):
        self.overrides.update(vals)

    def keys(self):
        keys = tuple(set(list(self.config.keys()) + list(self.overrides.keys())))
        return keys

    def is_false(self, key):
        if key not in self:
            return True
        val = self[key]
        return val in ['', 'false', '0', 'none', 'off']

    def class_from_config(self, cls, *args, **kwargs):
        return cls(**self(*args, **kwargs))
