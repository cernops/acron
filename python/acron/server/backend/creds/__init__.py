#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Creds interface class'''

from abc import ABC, abstractmethod
import logging
from acron.server.utils import dump_args, get_remote_hostname

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)',
               'Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


class Creds(ABC):
    '''
    Base credential management class. Acts as interface for the different creds backends.
    '''
    @dump_args
    def __init__(self, project_id, config):
        '''
        Constructor

        :param project_id: identifier of the project to manage
        :param config:     a dictionary containing all the config values
        '''
        self.project_id = project_id
        self.config = config

    @abstractmethod
    def update_creds(self, source_path):
        '''
        Create or replace existing encrypted credentials.

        :param source_path:         location of the file on the system
        :except ArgsMalformedError: if the credentials file is not valid
        :except CredsError:         on backend failure
        '''

    @abstractmethod
    def get_creds(self):
        '''
        Retrieve the credentials.

        :raises CredsNoFileError: if no creds are stored
        :raises CredsError:       if creds could not be delivered
        :returns:                 the path to the unencrypted credentials
        '''

    @abstractmethod
    def delete_creds(self):
        '''
        Delete existing credentials.

        :raises CredsNoFileError: if no creds are stored
        :raises CredsError:       if creds could not be deleted
        '''
