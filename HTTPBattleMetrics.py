from urllib.parse import quote as _uriquote


class Route:
    BASE = 'https://api.battlemetrics.com/servers/{battlemetricsid}'

    def __init__(self, method, battlemetricsid, path, **parameters):
        self.BASE = self.BASE.format(battlemetricsid=battlemetricsid)
        self.path = path
        self.method = method
        url = (self.BASE + self.path)
        if parameters:
            self.url = url.format(**{k: _uriquote(v) if isinstance(v, str) else v for k, v in parameters.items()})
        else:
            self.url = url

        # major parameters:
        self.channel_id = parameters.get('channel_id')
        self.guild_id = parameters.get('guild_id')

    @property
    def bucket(self):
        # the bucket is just method + path w/ major parameters
        return '{0.channel_id}:{0.guild_id}:{0.path}'.format(self)
