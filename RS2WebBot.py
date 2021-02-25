import os
from flask import Flask, request, jsonify
from discord_interactions import verify_key_decorator

CLIENT_PUBLIC_KEY = os.getenv('CLIENT_PUBLIC_KEY')


app = Flask(__name__)


@app.route('/', methods=['GET'])
def status():
    return 'RS2-Web-Bot up and running'


@app.route('/interactions', methods=['POST'])
@verify_key_decorator(CLIENT_PUBLIC_KEY)
def handle_command():
    if request.json['type'] == 2:
        print(dict(request.json))
        return jsonify({'type': 4, 'data': {'content': 'Hi'}})


if __name__ == '__main__':
    app.run()
