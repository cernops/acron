#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Implementation of the File storage backend client'''

import logging
from subprocess import Popen, PIPE
from acron.errors import ERRORS
from acron.exceptions import ArgsMalformedError, CredsNoFileError, FileError
from acron.server.utils import dump_args
from . import Creds

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'


class File(Creds):
    '''
    Implements a credentials manager based on the native Linux file manager.
    '''
    @dump_args
    def update_creds(self, source_path):
        '''
        Create or replace existing encrypted credentials.

        :param source_path:         location of the file on the system
        :except ArgsMalformedError: if the keytab is not valid
        :except FileError:          on backend failure
        '''
        process = Popen(['sudo', '-u', 'acron', '/usr/libexec/acron/store_creds',
                         self.project_id, source_path],
                        universal_newlines=True, stdout=PIPE, stderr=PIPE)
        _, err = process.communicate()
        if process.returncode != 0:
            logging.error('File creds storage: could not update creds. %s\n', err)
            if process.returncode == ERRORS['BAD_ARGS']:
                raise ArgsMalformedError(err)
            raise FileError(err)

    @dump_args
    def get_creds(self):
        '''
        Retrieve the credentials.

        :raises CredsNoFileError: if no creds are stored
        :raises FileError:        if creds could not be delivered
        :returns:                 the path to the unencrypted credentials
        '''
        process = Popen(['sudo', '-u', 'acron', '/usr/libexec/acron/get_creds', self.project_id],
                        universal_newlines=True, stdout=PIPE, stderr=PIPE)
        out, err = process.communicate()
        if process.returncode != 0:
            if process.returncode == ERRORS['NO_VALID_CREDS']:
                raise CredsNoFileError(err)
            raise FileError(err)
        return out.rstrip('\n')

    @dump_args
    def delete_creds(self):
        '''
        Delete existing credentials.

        :raises CredsNoFileError: if no creds are stored
        :raises FileError:        if creds could not be deleted
        '''
        process = Popen(['sudo', '-u', 'acron', '/usr/libexec/acron/delete_creds', self.project_id],
                        universal_newlines=True, stdout=PIPE, stderr=PIPE)
        _, err = process.communicate()
        if process.returncode != 0:
            if process.returncode == ERRORS['NOT_FOUND']:
                raise CredsNoFileError(err)
            raise FileError(err)
