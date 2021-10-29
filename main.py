import os
from RS2WebBot import app


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6969, loop=app.client.loop, certfile=os.get_env('CERTFILE'), keyfile=os.get_env('KEYFILE'))
