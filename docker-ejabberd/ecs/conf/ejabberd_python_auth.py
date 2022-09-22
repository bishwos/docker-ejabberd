#!/usr/bin/python3

import sys
import traceback
from struct import *
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from configparser import ConfigParser
import json
import logging
import random

LOG_FILE = '/home/ejabberd/logs/logs.log'
ENV_FILE = '/home/ejabberd/conf/.env'
ADMIN_USER = 'admin'
ADMIN_PASSWORD = 'asd'


# This module get input through stdinput from_ejabberd().
# Switches to appropriate method described in the data.
# Outputs to_ejabberd(). This is done in a perpetual loop().
def main():
    global config
    configure_logger()
    config: ConfigParser = ConfigParser()

    config.read('%s' % ENV_FILE)
    sys.excepthook = exc_handler
    logging.info('Started')
    # TODO: Print contents of .env file. Fail if .env doesn't exists
    loop()
    # To test code, comment loop and uncomment line below
    # print(do_auth(['info', 'aayulogic.com', '']))


def loop():
    while True:
        switcher = {
            "auth": do_auth,
            "isuser": lambda: True,
            "setpass": lambda: True,
            "tryregister": lambda: False,
            "removeuser": lambda: False,
            "removeuser3": lambda: False,
        }

        data = from_ejabberd()
        to_ejabberd(switcher.get(data[0], lambda: False)(data[1:]))


def configure_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    # Ejabberd initiates multiple processes at the same time.
    # This caused a race condition when checking if log file is in use.
    log_file_name = LOG_FILE + str(random.randint(0, 10))
    file_handler = logging.FileHandler(log_file_name)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def do_auth(args):
    (username, server, token) = args
    logging.info(f'username: {username}, server: {server}, token: {token}')
    if username == ADMIN_USER and token == ADMIN_PASSWORD:
        return True
    # noinspection PyBroadException
    try:
        try:
            request = Request(config.get(server, 'auth_url'))
            request.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
            request.add_header('cookie', 'auth._token.local=' + token)
            response = json.load(urlopen(request))
            return str(response['user']['id']) == username or response['user']['email'] == username + '@' + server
        except HTTPError as err:
            if err.code == 401:
                return False
            raise err
    except BaseException:
        logging.debug('username: {username}, server: {server}')
        logging.debug('Exception Occurred', exc_info=True)
    return False


def exc_handler(exctype, value, tb):
    logging.info(''.join(traceback.format_exception(exctype, value, tb)))


# read from stdin: AABBBBBBBBB.....
# A: 2 bytes of length data (a short in network byte order)
# B: a string of length found in A that contains operation in plain text operation are as follows:
# auth:User:Server:Password (check if a username/password pair is correct)
# isuser:User:Server (check if it’s a valid user)
# setpass:User:Server:Password (set user’s password)
# tryregister:User:Server:Password (try to register an account)
# removeuser:User:Server (remove this account)
# removeuser3:User:Server:Password (remove this account if the password is correct)
def from_ejabberd():
    input_length = sys.stdin.buffer.read(2)
    # > Big-endian, h short
    (size,) = unpack('>h', input_length)
    return sys.stdin.read(size).split(':')


# write to stdout: AABB
# A: the number 2 (coded as a short, which is bytes length of following result)
# B: the result code (coded as a short), should be 1 for success/valid, or 0 for failure/invalid
def to_ejabberd(result):
    if result:
        sys.stdout.write('\x00\x02\x00\x01')
    else:
        sys.stdout.write('\x00\x02\x00\x00')
    sys.stdout.flush()


if __name__ == "__main__":
    main()
