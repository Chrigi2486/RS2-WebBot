from aiohttp import ClientSession
from bs4 import BeautifulSoup as BS
from hashlib import sha1


class WebAdminSession(ClientSession):
    def __init__(self, WAURL, *args, **kwargs):
        self.WAURL = WAURL
        super().__init__(*args, **kwargs)


    async def login(self, logindata):

        async def gettoken():
            async with self.get(self.WAURL) as loginpage:
                self.cookie_jar.update_cookies(loginpage.cookies)
                # self.cookies = loginpage.cookies
                return(BS(await loginpage.text(), 'html.parser').find(attrs = {'name': 'token'})['value'])

        def hashpassword():
            logindata['password_hash'] = '$sha1$' + sha1((logindata['password'] + logindata['username']).encode('utf-8')).hexdigest()
            logindata['password'] = ''

        async def postlogindata():
            async with self.post(f'{self.WAURL}/ServerAdmin/current', data=logindata) as homepage:
                if BS(await homepage.text(), 'html.parser').html.title.string == 'Rising Storm 2: Vietnam WebAdmin - Current Game':
                    return(True)
                return(False)

        try:
            logindata['token'] = await gettoken()
        except:
            raise ServerOffline()
        if 'password_hash' not in logindata.keys():
            hashpassword()

        if not await postlogindata():
            raise IncorrectLogindata()


    async def kick(self, player):
        await self.get(f"{self.WAURL}/ServerAdmin/current/players?action=kick?playerid={player['playerID']}?playerkey={player['playerKey']}?__Reason={player['reason']}?NotifyPlayers=0?__IdType=0?__ExpUnit=Never")

    async def ban(self, player):
        await self.get(f"{self.WAURL}/ServerAdmin/current/players?action=banid?playerid={player['playerID']}?playerkey={player['playerKey']}?__Reason={player['reason']}?NotifyPlayers=0?__IdType=0?__ExpUnit=Never")
        await self.addban(player)

    async def addban(self, player):
        await self.get(f"{self.WAURL}/ServerAdmin/policy/bans?action=add?__UniqueId={player['steamID']}?__Reason={player['reason']}?NotifyPlayers=0?__IdType=1?__ExpUnit=Never")

    async def reset(self):
        await self.get(f'{self.WAURL}/ServerAdmin/current?action=resetCampaign')

    async def change_map(self, maptype, givenmap):
        await self.get(f'{self.WAURL}/ServerAdmin/current/change?gametype={maptype}?map={givenmap}?action=change')


    async def info(self):
        async with self.get(f'{self.WAURL}/ServerAdmin/current') as infopage:
            infopagetext = await infopage.text()
            players = BS(infopagetext, 'html.parser').select('#currentRules > dd:nth-child(6)')[0].string.split(' ')[0]
            currentmap = BS(infopagetext, 'html.parser').select('#currentGame > dd:nth-child(7) > code')[0].string
            ranked = BS(infopagetext, 'html.parser').find(class_='ranked').string.split(' ')[1]
            if ranked == 'No':
                ranked = False
            else:
                ranked = True

        return({'players': players, 'map': currentmap, 'ranked': ranked})





class ServerOffline(Exception):
    pass

class IncorrectLogindata(Exception):
    pass
