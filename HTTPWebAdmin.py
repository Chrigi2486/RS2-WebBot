from urllib.parse import quote as _uriquote
from bs4 import BeautifulSoup


class Route:
    BASE = 'http://{webadminip}/ServerAdmin'

    def __init__(self, method, webadminip, path, **parameters):
        self.BASE = self.BASE.format(webadminip=webadminip)
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


class Parser:

    @staticmethod
    def parse_page_title(resp):
        return BeautifulSoup(resp, 'html.parser').html.title.string

    @staticmethod
    def parse_login_page(resp):
        html = BeautifulSoup(resp, 'html.parser')
        token = html.find(attrs={'name': 'token'})['value']
        return token

    @staticmethod
    def parse_current(resp):
        html = BeautifulSoup(resp, 'html.parser')
        name = html.select('#currentGame > dd:nth-child(2)')[0].contents[0][:-2]
        players = html.select('#currentRules > dd:nth-child(6)')[0].string.split(' ')[0]
        currentmap = html.select('#currentGame > dd:nth-child(7) > code')[0].string
        ranked = html.find(class_='ranked').string.split(' ')[1]
        north = html.select('#teams > tbody > tr.even')[0].find_all('td')
        south = html.select('#teams > tbody > tr.odd')[0].find_all('td')
        scorelist = html.select('#players > tbody')[0]
        scorelist = None if scorelist.find('em') else scorelist
        ranked = not ranked == 'No'
        teams = {'North': {'size': int(north[2].string), 'attacking': (north[3].string == 'Yes'), 'won': int(north[4].string), 'score': int(north[5].string)}, 'South': {'size': int(south[2].string), 'attacking': (south[3].string == 'Yes'), 'won': int(south[4].string), 'score': int(south[5].string)}}

        def parse_player(player):
            return player.find_all('td')[1].string, {'score': int(player.find_all('td')[3].string), 'kills': int(player.find_all('td')[4].string)}

        playerstats = ({} if not scorelist else {parse_player(player)[0]: parse_player(player)[1] for player in scorelist.find_all('tr')})
        return {'name': name, 'players': players, 'map': currentmap, 'ranked': ranked, 'playerstats': playerstats, 'teams': teams}

    @staticmethod
    def parse_player_list(resp):
        playerlist = BeautifulSoup(resp, 'html.parser').select('#players > tbody')[0]
        if playerlist.find('em'):
            return
        players = []
        for playerinfo in playerlist.find_all('tr'):
            player = {
                'name': playerinfo.find_all('input')[2]['value'],
                'ID': playerinfo.find_all('input')[0]['value'],
                'key': playerinfo.find_all('input')[1]['value'],
                'platformID': playerinfo.find_all('td')[5].string,
                'IP': playerinfo.find_all('td')[3].string,
                'uniqueID': playerinfo.find_all('td')[4].string
            }
            players.append(player)
        return players

    @staticmethod
    def parse_chat(resp):
        chatmessages = BeautifulSoup(resp, 'html.parser').find_all(class_='chatmessage')
        messages = []
        for chatmessage in chatmessages:
            try:
                color = int(chatmessage.find(class_='teamcolor').get('style').split(' ')[1][:-1].replace('#', '0x'), 0)
            except:
                color = 0x9400D3
            message = {
                'username': chatmessage.find(class_='username').string,
                'content': chatmessage.find(class_='message').string,  # TODO: Add @ADMIN
                'team': chatmessage.find(class_='teamnotice').string if chatmessage.find(class_='teamnotice') else '',
                'color': color
            }
            messages.append(message)
        return messages
