from RS2WebBot import app


if __name__ == '__main__':
    context = ('ssl_crt.crt', 'ssl_key.key')
    app.run(host='0.0.0.0', port=443, loop=app.client.loop, ssl_context=context)
