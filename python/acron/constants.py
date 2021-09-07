#
# (C) Copyright 2021 CERN
#
# This software is distributed under the terms of the GNU General Public Licence version 3
# (GPL Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Shared constants'''

__author__ = 'Rodrigo Bermudez Schettino (CERN)'
__credits__ = ['Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


def _convert_to_trailing_slash(endpoint):
    '''
    Replace leading slash by a trailing one

    Example:
        '/jobs' -> 'jobs/'

    :param endpoint:
    :returns:
    '''
    # Done in two steps:
    # 1. Remove leading slash
    # 2. Add trailing slash
    return endpoint.replace('/', '') + '/'


# pylint: disable=too-few-public-methods
class ReturnCodes:
    '''
    Return codes for client responses
    '''
    # pylint: disable=invalid-name
    OK = 0
    BAD_ARGS = 1
    NO_VALID_CREDS = 2
    NOT_ALLOWED = 3
    LDAP_ERROR = 4
    NOT_FOUND = 5
    BACKEND_ERROR = 6
    USER_ERROR = 7
    ABORT = 8
    CREDS_INVALID = 9
    SSH_ERROR = 10


# pylint: disable=too-few-public-methods
class Endpoints:
    '''
    Constants for API endpoints
    '''
    CREDS = '/creds'
    JOBS = '/jobs'
    PROJECTS = '/projects'
    PROJECT = '/project'
    SYSTEM = '/system'
    SESSION = '/session'

    CREDS_TRAILING_SLASH = _convert_to_trailing_slash(CREDS)
    JOBS_TRAILING_SLASH = _convert_to_trailing_slash(JOBS)
    SESSION_TRAILING_SLASH = _convert_to_trailing_slash(SESSION)
    PROJECTS_TRAILING_SLASH = _convert_to_trailing_slash(PROJECTS)
    PROJECT_TRAILING_SLASH = _convert_to_trailing_slash(PROJECT)


class ProjectPerms:
    '''
    Constants for project permissions (ACL)
    '''
    READ_ONLY = 'ro'
    READ_WRITE = 'rw'
    ALL = [READ_ONLY, READ_WRITE]
    NAME_MAP = {READ_ONLY: 'read-only', READ_WRITE: 'read and write'}
