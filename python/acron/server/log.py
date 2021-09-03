#
# (C) Copyright 2021 CERN
#
# This software is distributed under the terms of the GNU General Public Licence version 3
# (GPL Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Logging module'''

__author__ = 'Rodrigo Bermudez Schettino (CERN)'
__credits__ = ['Rodrigo Bermudez Schettino (CERN)', 'Philippe Ganz (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'

import logging
from .utils import default_log_line_request


# pylint: disable=too-few-public-methods
class LogLevel:
    '''
    Constants for logging
    '''

    INFO = 'i'
    WARNING = 'w'
    ERROR = 'e'
    CRITICAL = 'c'


# pylint: disable=too-few-public-methods
class Logger:
    '''
    Log messages with unified formatting
    '''

    @staticmethod
    def log_request(endpoint, level=LogLevel.INFO, msg=''):
        '''
        Log error in projects

        :param endpoint: HTTP endpoint where request was received
        :param level: severity level, see LogLevel.
        :param msg: message to log
        '''

        out = f'{default_log_line_request()} on {endpoint}: {msg}'

        if level == LogLevel.INFO:
            return logging.info(out)

        if level == LogLevel.WARNING:
            return logging.warning(out)

        if level == LogLevel.ERROR:
            return logging.error(out)
