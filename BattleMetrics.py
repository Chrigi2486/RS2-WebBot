from aiohttp import ClientSession


class BattleMetricsSession(ClientSession):
    rankurl = 'https://api.battlemetrics.com/servers/{}/rank-history?start={}T00%3A00%3A00.000Z&stop={}T00%3A00%3A00.000Z'
    leaderboardurl = 'https://api.battlemetrics.com/servers/{}/relationships/leaderboards/time?page%5Bsize%5D=100&page%5Brel%5D=next&page%5Boffset%5D=0&filter%5Bperiod%5D=AT'
    playersurl = 'https://api.battlemetrics.com/servers/5156787/player-count-history?start={}T{}%3A00%3A00.000Z&stop={}T{}%3A00%3A00.000Z&resolution=60'
    infourl = 'https://api.battlemetrics.com/servers/{}'

    def __init__(self, ID, *args, **kwargs):
        self.ID = ID
        super().__init__(*args, **kwargs)

    async def getinfo(self):
        async with self.get(self.infourl.format(self.ID)) as infopage:
            return await infopage.json()

    async def getranks(self, pdate, ndate):
        url = self.rankurl.format(self.ID, pdate, ndate)
        async with self.get(url) as ranks:
            return await ranks.json()

    async def getleaderboard(self):
        url = self.leaderboardurl.format(self.ID)
        async with self.get(url) as leaderboard:
            return await leaderboard.json()

    async def getplayers(self, pdate, ndate, hour):
        url = self.playersurl.format(self.ID, pdate, hour, ndate, hour)
        async with self.get(url) as players:
            return await players.json()
