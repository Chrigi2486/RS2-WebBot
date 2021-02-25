import os
from flask import Flask, request, jsonify
from discord_interactions import verify_key_decorator

CLIENT_PUBLIC_KEY = os.getenv('CLIENT_PUBLIC_KEY')


class RS2WebBot(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.route('/integrations', methods=['POST'])(self.handle_command)

    @verify_key_decorator(CLIENT_PUBLIC_KEY)
    def handle_command(self):
        if request.json['type'] == 2:
            print(dict(request.json))
            return jsonify({'type': 4, 'data': {'content': 'Hi'}})
