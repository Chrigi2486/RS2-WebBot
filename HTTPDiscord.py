import requests


class HTTPDiscord:

    BASE_URL = 'https://discord.com/api/v8'
    GUILDS_URL = BASE_URL + '/users/@me/guilds'
    SEND_MESSAGE_URL = BASE_URL + '/channels/{channel_ID}/messages'

    def __init__(self, BOT_TOKEN, CLIENT_ID):
        self.BOT_TOKEN = BOT_TOKEN
        self.CLIENT_ID = CLIENT_ID
        self.AUTH_HEADERS = {'Authorization': f'Bot {self.BOT_TOKEN}'}

    def request(self, action, URL, json=None):
        if action == 'POST':
            return requests.post(URL, json=json, headers=self.AUTH_HEADERS)
        if action == 'GET':
            return requests.get(URL, headers=self.AUTH_HEADERS)

    def get_guilds(self):
        return self.request('GET', self.GUILDS_URL).json()

    def send_message(self, channel_ID, message):
        message = message.to_dict()
        self.request('POST', self.SEND_MESSAGE_URL.format(**{'channel_ID': channel_ID}) json=message)
