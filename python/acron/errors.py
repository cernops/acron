#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Error handling submodule'''

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'


ERRORS = {
    'OK' : 0,
    'BAD_ARGS' : 1,
    'NO_VALID_CREDS' : 2,
    'NOT_ALLOWED' : 3,
    'LDAP_ERROR' : 4,
    'NOT_FOUND' : 5,
    'BACKEND_ERROR' : 6,
    'USER_ERROR' : 7,
    'ABORT' : 8,
    'CREDS_INVALID' : 9,
    'SSH_ERROR' : 10
}
