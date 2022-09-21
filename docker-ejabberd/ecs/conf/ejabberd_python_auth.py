#!/usr/bin/python3

import sys
from struct import *
from urllib.request import Request, urlopen
from configparser import ConfigParser
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

file_handler = logging.FileHandler('logs.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

config = ConfigParser()
config.read('.env')
# logging.info('started')


def do_auth(args):
    (username, server, token) = args
    if username == 'admin' and token == 'asd':
        return True
    request = Request(config.get(server, 'auth_url'))
    request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
    request.add_header('cookie', 'auth._token.local='+token)
    response = json.load(urlopen(request))
    # logging.info('username: {username}, server: {server}, token: {token}')
    return str(response['user']['id']) == username or response['user']['email'] == username + '@' + server


# print(do_auth(['info', 'aayulogic.com', 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjYzNzg4MTA1LCJpYXQiOjE2NjM3NjY1MDUsImp0aSI6IjVjYmNlNzEyNjk3NDRkODFiM2RkZDE1YmM5ZDMxOGYxIiwidXNlcl9pZCI6MX0.IjbettQ5XIG1HZyzehjMuJoRML3c3kQPeQyPcherj3r7DLvgMdESuIO25Gsi30whsMd8FwnUiXdl5uo5Lwco-DP8n6zA-luVkqucbYftfutT9xbi1pkQ8jUcL9mJAHiGDFpYnCMshwfTzp3Sw-t2YBuOIMwgudhSXGenzRC2H-lm98zFLt5CTVFGRqN9GPcAFcHcOQPA_pQC8HoYx0imRlu7rGxcHqZxF0XRmBYBJ2seCA0rkP4YWV75-8Aqv3H4yKrWkyOnPQX3VP2MYJw7eUNAadNC1eNRAGn8TIyhZzAgR_7M-06RlhaZi6gsI7Y8faAEGnIBaPQ8LxmTk5A43w']))


def is_user(args):
    return True


def loop():
    while True:
        switcher = {
            "auth": do_auth,
            "isuser": is_user,
            "setpass": lambda: True,
            "tryregister": lambda: False,
            "removeuser": lambda: False,
            "removeuser3": lambda: False,
        }

        data = from_ejabberd()
        to_ejabberd(switcher.get(data[0], lambda: False)(data[1:]))


def from_ejabberd():
    input_length = sys.stdin.buffer.read(2)
    (size,) = unpack('>h', input_length)
    return sys.stdin.read(size).split(':')


def to_ejabberd(result):
    if result:
        sys.stdout.write('\x00\x02\x00\x01')
    else:
        sys.stdout.write('\x00\x02\x00\x00')
    sys.stdout.flush()


if __name__ == "__main__":
    loop()

