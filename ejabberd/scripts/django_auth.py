# Tunnel - TODO
#
# (C) 2010 Luke Slater, Steve 'Ashcrow' Milner
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Authenticate XMPP user.
"""

import logging
import struct
import sys

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, check_password
from django.conf import settings


class Command(BaseCommand):
    """
    Acts as an auth service for ejabberd through ejabberds external auth
    option. See contrib/ejabberd/ejabber.cfg for an example configuration.
    """

    help = "Runs an ejabberd auth service"

    def __init__(self, *args, **kwargs):
        """
        Creation of the ejabberd atuh bridge service.

        :Parameters:
           - `args`: all non-keyword arguments
           - `kwargs`: all keyword arguments
        """
        BaseCommand.__init__(self, *args, **kwargs)
        logging.basicConfig(
            level=settings.TUNNEL_EJABBERD_AUTH_GATEWAY_LOG_LEVEL,
            format='%(asctime)s %(levelname)s %(message)s',
            filename=settings.TUNNEL_EJABBERD_AUTH_GATEWAY_LOG,
            filemode='a')
        logging.info(('ejabberd_auth_bridge process started'
            ' (more than one is common)'))

    def _generate_response(self, success=False):
        """
        Creates and sends a response back to the ejabberd server.

        :Parameters
           - `success`: boolean if we should respond successful or not
        """
        result = 0
        if success:
            result = 1
        sys.stdout.write(struct.pack('>hh', 2, result))
        sys.stdout.flush()

    def _handle_isuser(self, username):
        """
        Handles the isuer ejabberd command.

        :Parameters:
           - `username`: the user name to verify exists
        """
        try:
            user = User.objects.get(username=username)
            self._generate_response(True)
        except User.DoesNotExist:
            self._generate_response(False)

    def _handle_auth(self, username, password):
        """
        Handles authentication of the user.

        :Parameters:
           - `username`: the username to verify
           - `password`: the password to verify with the user
        """
        try:
            user = User.objects.get(username=username)
            if check_password(password, user.password):
                self._generate_response(True)
                logging.info(username + ' has logged in')
                profile = user.get_profile()
                # Tunnel specific .....
                if not profile.logged_in:
                    try:
                        profile.logged_in = True
                        profile.save()
                    except Exception, ex:
                        # Couldn't update the profile ...
                        logging.warn("Could not save profile:" + str(ex))
                    logging.debug('Updated ' + username + ' profile status')
                # End Tunnel specific
            else:
                self._generate_response(False)
                logging.info(username + ' failed auth')
        except User.DoesNotExist:
            self._generate_response(False)
            logging.info(username + ' is not a valid user')

    def handle(self, **options):
        """
        How to check if a user is valid

        :Parameters:
           - `options`: keyword arguments
        """
        try:
            # Serve forever
            while True:
                # Verify the information checks out
                try:
                    length = sys.stdin.read(2)
                    size = struct.unpack('>h', length)[0]
                    logging.debug('Got data of size ' + str(size))
                    input = sys.stdin.read(size).split(':')
                    operation = input.pop(0)
                except Exception, ex:
                    # It wasn't even in the right format if we get here ...
                    self._generate_response(False)
                    continue
                if operation == 'auth':
                    logging.info(
                        'Auth request being processed for ' + input[1])
                    self._handle_auth(input[0], input[2])
                elif operation == 'isuser':
                    logger.info('Asked if ' + input[0] + ' is a user')
                    self._handle_isuser()
                elif operation == 'setpass':
                    logger.info('Asked if to change password for ' + input[0])
                    # Do not support this (Tunnel specific)
                    self._generate_repsonse(False)
        except KeyboardInterrupt:
            raise SystemExit(0)

    def __del__(self):
        """
        What to do when we are shut off.
        """
        logging.info('ejabberd_auth_bridge process stopped')