#
# (C) Copyright 2021 CERN
#
# This software is distributed under the terms of the GNU General Public Licence version 3
# (GPL Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Project management functions'''

import sys
import requests
from requests_gssapi import HTTPSPNEGOAuth
from acron.exceptions import AcronError, AbortError
from acron.constants import Endpoints, ProjectPerms, ReturnCodes
from .config import CONFIG
from .errors import ServerError
from .utils import confirm

__author__ = 'Rodrigo Bermudez Schettino (CERN)'
__credits__ = ['Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


def _unwrap_response_message(response):
    '''
    Extract message from HTTP response object

    :params response: HTTP response from server
    :returns: response message if it exists, None otherwise
    '''
    if (hasattr(response, 'json') and
        isinstance(response.json(), dict) and
        hasattr(response.json(), 'keys') and
            'message' in response.json().keys()):
        return response.json()['message'] + '\n'

    return None


def _handle_found(response, *_):
    '''
    Handle HTTP response status code 200 (OK)

    :params response:    HTTP response from server
    :returns:            the API's return value
    '''
    response_msg = _unwrap_response_message(response)
    if response_msg:
        sys.stdout.write(response_msg)

    return ReturnCodes.OK


def _handle_bad_request(*_):
    '''
    Handle HTTP response status code 400 (Bad Request)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''

    ServerError.error_user_not_found()
    return ReturnCodes.BAD_ARGS


def _handle_no_access(*_):
    '''
    Handle HTTP response status code 401 (Unauthorized) and 403 (Forbidden)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''

    ServerError.error_no_access()
    return ReturnCodes.NOT_ALLOWED


def _handle_not_found_project(*_):
    '''
    Handle HTTP response status code 404 (Not Found)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''
    ServerError.error_project_not_found()
    return ReturnCodes.NOT_FOUND


def _handle_not_found(*_):
    '''
    Handle HTTP response status code 404 (Not Found)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''
    ServerError.error_project_or_user_not_found()
    return ReturnCodes.NOT_FOUND


def _handle_internal_server(*_):
    '''
    Handle HTTP response status code 500 (Internal Server Error)

    :params *_: Ignore parameters passed
    :returns:         the API's return value
    '''
    ServerError.error_internal_server()
    return ReturnCodes.BACKEND_ERROR


def _handle_invalid(response, *_):
    '''
    Handle unrecognized HTTP response status code generically

    :params response: HTTP response from server
    :returns:         the API's return value
    '''
    print_error_fallback = True
    try:
        response_msg = _unwrap_response_message(response)
        if response_msg:
            sys.stderr.write(response_msg)
            print_error_fallback = False
    finally:
        if print_error_fallback:
            ServerError.error_unknown(response.text)

    return ReturnCodes.BACKEND_ERROR


def projects_get(parser_args):
    '''
    Get projects information request to the API.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    try:
        default_endpoint = Endpoints.PROJECT_TRAILING_SLASH + 'users'
        # Set variables to default values
        params = None
        path = CONFIG['ACRON_SERVER_FULL_URL'] + default_endpoint

        if hasattr(parser_args, 'all') and parser_args.all:
            path = path.replace(
                default_endpoint, Endpoints.PROJECTS_TRAILING_SLASH)

        response = requests.get(
            path, params=params, auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])

        http_status_code_switcher = {
            200: _handle_found,
            401: _handle_no_access,
            403: _handle_no_access,
            404: _handle_not_found_project,
            500: _handle_internal_server,
        }

        handler = http_status_code_switcher.get(
            response.status_code, _handle_invalid)

        return_code = handler(response, parser_args)

    except (AbortError, KeyboardInterrupt):
        sys.stderr.write('\nAbort.\n')
        return_code = ReturnCodes.ABORT
    except AcronError as error:
        ServerError.error_unknown(str(error))
        return_code = ReturnCodes.BACKEND_ERROR
    return return_code


def projects_share(parser_args):
    '''
    Share project with user

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    try:
        # Set variables to default values
        path = CONFIG['ACRON_SERVER_FULL_URL'] + \
            Endpoints.PROJECT_TRAILING_SLASH + 'user/' + parser_args.user_id

        if hasattr(parser_args, 'delete') and parser_args.delete:
            response = requests.delete(
                path,
                auth=HTTPSPNEGOAuth(),
                verify=CONFIG['SSL_CERTS'])
        else:
            acl = ProjectPerms.READ_ONLY

            if hasattr(parser_args, 'write') and parser_args.write:
                acl = ProjectPerms.READ_WRITE

            response = requests.put(
                path,
                params={'project_permissions': acl},
                auth=HTTPSPNEGOAuth(),
                verify=CONFIG['SSL_CERTS'])

        http_status_code_switcher = {
            200: _handle_found,
            400: _handle_bad_request,
            401: _handle_no_access,
            403: _handle_no_access,
            404: _handle_not_found,
            500: _handle_internal_server,
        }

        handler = http_status_code_switcher.get(
            response.status_code, _handle_invalid)

        return_code = handler(response, parser_args)

    except (AbortError, KeyboardInterrupt):
        sys.stderr.write('\nAbort.\n')
        return_code = ReturnCodes.ABORT
    except AcronError as error:
        ServerError.error_unknown(str(error))
        return_code = ReturnCodes.BACKEND_ERROR
    return return_code


def projects_delete(parser_args):
    '''
    Delete user project

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    try:
        if not confirm("WARNING: Are you sure you want to delete your project, its shares and its jobs?"):
            raise AbortError
        # Set variables to default values
        path = CONFIG['ACRON_SERVER_FULL_URL'] + \
            Endpoints.PROJECT_TRAILING_SLASH

        response = requests.delete(
            path,
            auth=HTTPSPNEGOAuth(),
            verify=CONFIG['SSL_CERTS'])

        http_status_code_switcher = {
            200: _handle_found,
            400: _handle_bad_request,
            401: _handle_no_access,
            403: _handle_no_access,
            404: _handle_not_found_project,
            500: _handle_internal_server,
        }

        handler = http_status_code_switcher.get(
            response.status_code, _handle_invalid)

        return_code = handler(response, parser_args)

    except (AbortError, KeyboardInterrupt):
        sys.stderr.write('\nAbort.\n')
        return_code = ReturnCodes.ABORT
    except AcronError as error:
        ServerError.error_unknown(str(error))
        return_code = ReturnCodes.BACKEND_ERROR
    return return_code
