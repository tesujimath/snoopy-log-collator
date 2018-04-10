class ConfigError(Exception):

    def __init__(self, filename, msg):
        self.filename = filename
        self.msg = msg

    def __str__(self):
        return('Configuration error %s: %s' % (self.filename, self.msg))

def read_config_file(args):
    filename = None
    if args.config:
        filename = args.config
        if not os.path.exists(filename):
            raise ConfigError('%s' % filename, 'file not found')
    else:
        env_config = 'PUBLIC_WRAPPERS_CONFIG'
        attempt_files = ([os.environ[env_config]] if env_config in os.environ else []) + [
            os.path.expanduser('~/.public-wrappers.toml'),
            '/etc/public-wrappers.toml',
        ]
        for attempt in attempt_files:
            if os.path.exists(attempt):
                filename = attempt
                break
        if filename is None:
            raise ConfigError('', [], 'none of %s found' % ', '.join(attempt_files))

    with open(filename, 'rb') as f:
        try:
            obj = toml.load(f)
        except toml.TomlError as e:
            raise ConfigError(filename, [], 'TOML error at line %d' % e.line)
    return ConfigObject(filename, [], obj)
