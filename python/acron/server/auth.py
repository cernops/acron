#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Main acron launcher'''

import logging
import memcache

__author__ = 'Ulrich Schwickerath (CERN)'
__credits__ = ['Ulrich Schwickerath (CERN)',
               'Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


class UserAuth():
    ''' store session info and interface with memcached '''

    def __init__(self, config):
        ''' initialise class'''
        self.config = config
        self._user_is_authenticated = {}
        self.ttl = None
        self.memcache_client = self._setup_memcache()

    def _setup_memcache(self):
        ''' initialise memcached access '''
        logging.debug("Initialising memcached")
        servers = self.config['MEMCACHED_HOSTS'].replace(" ", "").split(',')
        serverport = self.config['MEMCACHED_PORT']
        try:
            self.ttl = int(self.config['MEMCACHED_TTL'])
        except KeyError:
            self.ttl = 3600
        logging.debug("Set Memcached TTL to %d.", self.ttl)
        serverlist = []
        for server in servers:
            serverlist.append((server, serverport))
            self._user_is_authenticated = {}
        return memcache.Client(serverlist)

    def setauth(self, username, timestamp):
        ''' set auth timestamp '''
        logging.debug("Setting auth for user %s to timestamp %s",
                      username, str(timestamp))
        self._user_is_authenticated[username] = timestamp
        self.memcache_client.set(username, timestamp, time=self.ttl)

    def getauth(self, username):
        ''' return contents of cache '''
        cached = self.memcache_client.get(username)
        if cached is None:
            cached = 0
        self._user_is_authenticated[username] = cached
        logging.debug("Auth status for user %s is %s",
                      username, self._user_is_authenticated[username])
        return self._user_is_authenticated[username]
