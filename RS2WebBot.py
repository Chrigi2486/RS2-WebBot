import os
import sys
from flask import Flask, request, jsonify
from discord_interactions import verify_key_decorator

sys.path.insert(0, os.path.dirname(__file__))

CLIENT_PUBLIC_KEY = os.getenv('CLIENT_PUBLIC_KEY')

BOT_TOKEN = os.getenv('BOT_TOKEN')

app = Flask(__name__)


@app.route('/', methods=['GET'])
def status():
    return 'RS2-Web-Bot up and running'


@app.route('/', methods=['POST'])
@verify_key_decorator(CLIENT_PUBLIC_KEY)
def handle_command():
    if request.json['type'] == 2:
        return jsonify({'type': 4, 'data': {'content': 'Hi'}})


if __name__ == '__main__':
    app.run()
