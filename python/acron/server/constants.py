#
# (C) Copyright 2021 CERN
#
# This software is distributed under the terms of the GNU General Public Licence version 3
# (GPL Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Shared constants server-side'''

__author__ = 'Rodrigo Bermudez Schettino (CERN)'
__credits__ = ['Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


# pylint: disable=too-few-public-methods
class HttpMethods:
    '''
    Constants for HTTP verbs/methods
    '''
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'


# pylint: disable=too-few-public-methods
class ConfigFilenames:
    '''
    Constants for config filenames
    '''
    MAX_JOB_ID = 'max_job_id'
    SHAREABLE = 'shareable'


# pylint: disable=too-few-public-methods
class OpenModes:
    '''
    Constants for opening files
    '''
    READ = 'r'
    READ_WRITE = 'r+'
    WRITE = 'w'
