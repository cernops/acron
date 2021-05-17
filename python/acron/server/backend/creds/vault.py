#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Implementation of the Vault storage backend client'''

from acron.exceptions import VaultError
from acron.server.utils import dump_args
from . import Creds

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'


# pylint: disable=R0201, W0613
class Vault(Creds):
    '''
    Implements a scheduler based on the native Linux Crontab.
    '''
    @dump_args
    def update_creds(self, source_path):
        '''
        Create or replace existing encrypted credentials.

        :param source_path:         location of the file on the system
        :except ArgsMalformedError: if the keytab is not valid
        :except VaultError:         on backend failure
        '''
        raise VaultError

    @dump_args
    def get_creds(self):
        '''
        Retrieve the credentials.

        :raises CredsNoFileError: if no creds are stored
        :raises VaultError:       if creds could not be delivered
        :returns:                 the path to the unencrypted credentials
        '''
        raise VaultError

    @dump_args
    def delete_creds(self):
        '''
        Delete existing credentials.

        :raises CredsNoFileError: if no creds are stored
        :raises VaultError:       if creds could not be deleted
        '''
        raise VaultError
