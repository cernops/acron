#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''HTTP payload handler'''

from flask import jsonify
from acron.constants import ReturnCodes

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'


def generate_http_payload(status_code, message=None):
    '''
    Generates an HTTP payload.

    :param status_code: the HTTP status code
    :param message:     the message attached to the status code, can be empty
    :returns:           an HTTP payload that can be returned to the client
    '''
    payload = {}
    if message:
        payload['message'] = message
    response = jsonify(payload)
    response.status_code = status_code
    return response


def http_response(error):
    '''
    Returns ready-to-use HTTP payloads matching the given Acron error.

    :param error: an Acron error of Errors type
    :returns:     an HTTP payload that can be returned to the client
    '''
    payload = None

    # Used for status code 400
    msg_bad_args = '''The parameters you specified were not complete or wrong, \
please check your input and try again.'''
    # Used for status code 400
    msg_no_valid_creds = '''There are no valid credentials stored on the server. \
Either because you did not provide any or because the ones currently stored expired. \
Your current or future jobs will not work until you upload valid credentials.'''
    # Used for status code 403
    msg_not_allowed = '''The server could not authenticate you. Please check that you
have a valid Kerberos ticket.'''
    # Used for status code 403
    msg_ldap_error = '''Connection to the LDAP server timed out, \
access rights to the requested resource could not be verified. Please try again'''
    # Used for status code 404
    msg_not_found = '''The resource you requested could not be found, \
please verify your path and try again.'''
    # Used for status code 500
    msg_backend_error = '''The server was not able to process your request. \
Please try again or open a ticket towards the Acron service if it persists.'''
    # Used for status code 520
    msg_unknown_error = 'Unknown error!'

    error_switcher = {
        ReturnCodes.OK: [200, None],
        ReturnCodes.BAD_ARGS: [400, msg_bad_args],
        ReturnCodes.USER_ERROR: [400, msg_bad_args],
        ReturnCodes.NO_VALID_CREDS: [400, msg_no_valid_creds],
        ReturnCodes.NOT_ALLOWED: [403, msg_not_allowed],
        ReturnCodes.LDAP_ERROR: [403, msg_ldap_error],
        ReturnCodes.NOT_FOUND: [404, msg_not_found],
        ReturnCodes.BACKEND_ERROR: [500, msg_backend_error]
    }

    status_code_and_message = error_switcher.get(
        error, [520, msg_unknown_error])

    status_code = status_code_and_message[0]
    message = status_code_and_message[1]

    payload = generate_http_payload(status_code, message)

    return payload
