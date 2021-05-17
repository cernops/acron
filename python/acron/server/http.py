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
from acron.errors import ERRORS

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

    if error == ERRORS['OK']:
        payload = generate_http_payload(200)
    elif error == ERRORS['BAD_ARGS']:
        payload = generate_http_payload(400, '''The parameters you specified were not complete or wrong, \
please check your input and try again.''')
    elif error == ERRORS['NO_VALID_CREDS']:
        payload = generate_http_payload(400, '''There are no valid credentials stored on the server. \
Either because you did not provide any or because the ones currently stored expired. \
Your current or future jobs will not work until you upload valid credentials.''')
    elif error == ERRORS['NOT_ALLOWED']:
        payload = generate_http_payload(403, '''The server could not authenticate you. Please check that you
have a valid Kerberos ticket.''')
    elif error == ERRORS['LDAP_ERROR']:
        payload = generate_http_payload(403, '''Connection to the LDAP server timed out, \
access rights to the requested resource could not be verified. Please try again''')
    elif error == ERRORS['NOT_FOUND']:
        payload = generate_http_payload(404, '''The resource you requested could not be found, \
please verify your path and try again.''')
    elif error == ERRORS['BACKEND_ERROR']:
        payload = generate_http_payload(500, '''The server was not able to process your request. \
Please try again or open a ticket towards the Acron service if it persists.''')
    else:
        payload = generate_http_payload(520, 'Unknown error!')

    return payload
