#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Jobs management functions'''

import sys
import requests
from requests_gssapi import HTTPSPNEGOAuth
from acron.exceptions import AcronError, AbortError
from acron.constants import Endpoints, ReturnCodes
from .config import CONFIG
from .errors import ServerError

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)',
               'Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


def _write_job_to_console(job_properties):
    '''
    Write job to the console.

    :param job_properties: a dictionary containing the job's properties
    '''
    sys.stdout.write(
        '#' + ' '.join(job_properties['description'].split(' ')[5:]) + '\n')
    sys.stdout.write(
        ('#' if not job_properties['scheduleEnabled'] else '') + job_properties['name'] + ': ')
    sys.stdout.write(
        ' '.join(job_properties['description'].split(' ')[0:5]) + ' ')
    sys.stdout.write(job_properties['nodefilters']
                     ['filter'].replace('name: ', '') + ' ')
    sys.stdout.write(job_properties['sequence']['commands'][0]['exec'] + '\n')


def _handle_found(response, *_):
    '''
    Handle HTTP response status code 200 (OK)

    :params response: HTTP response from server
    :params *_:       Ignore parameters passed
    :returns:         the API's return value
    '''

    _write_job_to_console(response.json())
    return ReturnCodes.OK


def _handle_found_with_name(response, parser_args):
    '''
    Handle HTTP response status code 200 (OK)

    :params response:    HTTP response from server
    :params parser_args: user-given arguments
    :returns:            the API's return value
    '''

    return_code = ReturnCodes.OK

    if parser_args.job_id:
        sys.stdout.write(
            'Job ' + response.json()['name'] + ': ')

    sys.stdout.write(response.json()['message'] + '\n')

    return return_code


def _handle_found_get(response, parser_args):
    '''
    Handle HTTP response status code 200 (OK)

    :params response:    HTTP response from server
    :params parser_args: user-given arguments
    :returns:            the API's return value
    '''

    return_code = ReturnCodes.OK

    if not parser_args.job_id:
        if hasattr(response, 'json') and isinstance(response.json(), dict):
            sys.stdout.write(response.json()['message'] + '\n')
        else:
            sys.stdout.write(
                'Found ' + str(len(response.json())) + ' job(s) in the project:\n')
            for job_properties in response.json():
                _write_job_to_console(job_properties)

        return return_code

    _write_job_to_console(response.json())
    return return_code


def _handle_bad_request_post(*_):
    '''
    Handle HTTP response status code 400 (Bad Request)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''

    ServerError.error_job_already_exists()
    return ReturnCodes.BAD_ARGS


def _handle_no_access(*_):
    '''
    Handle HTTP response status code 401 (Unauthorized) and 403 (Forbidden)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''

    ServerError.error_no_access_job()
    return ReturnCodes.NOT_ALLOWED


def _handle_not_found(_, parser_args):
    '''
    Handle HTTP response status code 404 (Not Found)

    :params _:           Ignore first parameter
    :params parser_args: user-given arguments
    :returns:            the API's return value
    '''

    return_code = ReturnCodes.NOT_FOUND

    if parser_args.job_id:
        ServerError.error_job_not_found()
        return return_code

    ServerError.error_project_not_found()

    return return_code


def _handle_internal_error(*_):
    '''
    Handle HTTP response status code 500 (Internal Server Error)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''

    sys.stderr.write(
        'The backend is currently not available. Try again later.\n')
    return ReturnCodes.BACKEND_ERROR


def _handle_unavailable(*_):
    '''
    Handle HTTP response status code 503 (Service Unavailable)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''

    sys.stderr.write(
        'The backend is currently not available. Try again later.\n')
    return ReturnCodes.BACKEND_ERROR


def _handle_invalid(response, *_):
    '''
    Handle unrecognized HTTP response status code generically

    :params response: HTTP response from server
    :params *_:       Ignore parameters passed
    :returns:         the API's return value
    '''
    print_error_fallback = True
    try:
        if (hasattr(response, 'json') and hasattr(response.json(), 'keys') and
                'message' in response.json().keys()):
            sys.stderr.write(response.json()['message'] + '\n')
            print_error_fallback = False
    finally:
        if print_error_fallback:
            ServerError.error_unknown(response.text)

    return ReturnCodes.BACKEND_ERROR


# pylint: disable=R0912
def jobs_delete(parser_args):
    '''
    Delete job request to the API.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    try:
        if jobs_get(parser_args) == ReturnCodes.NOT_FOUND:
            raise AbortError
        valid_answers = ['y', 'yes', 'n', 'no', '']
        answer = 'not valid'
        while answer not in valid_answers:
            answer = input('Are you sure you want to delete? [y/N] ')
            if answer.lower() in ['y', 'yes']:
                pass
            elif answer.lower() in ['n', 'no', '']:
                raise AbortError
        params = None if 'project' not in parser_args else {
            'project': parser_args.project}
        path = CONFIG['ACRON_SERVER_FULL_URL'] + Endpoints.JOBS_TRAILING_SLASH
        if parser_args.job_id:
            path += parser_args.job_id
        response = requests.delete(
            path, params=params, auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])

        http_status_code_switcher = {
            200: _handle_found_with_name,
            401: _handle_no_access,
            403: _handle_no_access,
            404: _handle_not_found,
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


def jobs_get(parser_args):
    '''
    Get job information request to the API.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    try:
        params = None if 'project' not in parser_args else {
            'project': parser_args.project}
        path = CONFIG['ACRON_SERVER_FULL_URL'] + Endpoints.JOBS_TRAILING_SLASH
        if parser_args.job_id:
            path += parser_args.job_id
        response = requests.get(
            path, params=params, auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])

        http_status_code_switcher = {
            200: _handle_found_get,
            401: _handle_no_access,
            403: _handle_no_access,
            404: _handle_not_found,
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


def jobs_put(parser_args):
    '''
    Update an existing job

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    return jobs_post(parser_args, is_create=False)


def jobs_post(parser_args, is_create=True):
    '''
    Create a new job or update an existing one.

    :param parser_args: dictionary containing the user input from the parser
    :param is_create:   flag to identify if user is creating or updating job
    :returns:           the API's return value
    '''
    try:
        if (not parser_args.schedule and not parser_args.target and
                not parser_args.command and not parser_args.description):
            sys.stderr.write(
                'Please specify at least one of schedule, target, ')
            sys.stderr.write('command or description to update.\n')
            raise AbortError
        # This use case should not occur because the param job_id is required
        # to update a job
        if not is_create and not hasattr(parser_args, 'job_id'):
            sys.stderr.write('Job id is required to update a job.\n')
            raise AbortError
        if parser_args.description is None and is_create:
            sys.stderr.write('WARNING: no job description has been given.\n')
        if parser_args.target in CONFIG['TARGET_TRANSFORM']:
            parser_args.target = CONFIG['TARGET_TRANSFORM'][parser_args.target]
        params = {
            'schedule': parser_args.schedule,
            'target': parser_args.target,
            'command': parser_args.command,
            'project': parser_args.project,
            'description': parser_args.description
        }
        path = CONFIG['ACRON_SERVER_FULL_URL'] + Endpoints.JOBS_TRAILING_SLASH

        if is_create:
            response = requests.post(
                path, params=params, auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])
        else:
            path += parser_args.job_id
            params['job_id'] = parser_args.job_id
            response = requests.put(
                path, params=params, auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])

        http_status_code_switcher = {
            200: _handle_found,
            400: _handle_bad_request_post,
            401: _handle_no_access,
            403: _handle_no_access,
            404: _handle_not_found,
            500: _handle_internal_error,
            503: _handle_unavailable
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


def jobs_enable_disable(enable, parser_args):
    '''
    Make the actual HTTP request to the server

    :param enable: boolean containing the value to send
    :returns:      the API's return value
    '''
    try:
        params = {'enable': enable}
        if 'project' in parser_args:
            params['project'] = parser_args.project
        path = CONFIG['ACRON_SERVER_FULL_URL'] + Endpoints.JOBS_TRAILING_SLASH
        if parser_args.job_id:
            path += parser_args.job_id
        response = requests.patch(
            path, params=params, auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])

        http_status_code_switcher = {
            200: _handle_found_with_name,
            401: _handle_no_access,
            403: _handle_no_access,
            404: _handle_not_found,
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


def jobs_enable(parser_args):
    '''
    Enable job request to the API.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    return jobs_enable_disable(True, parser_args)


def jobs_disable(parser_args):
    '''
    Disable job request to the API.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    return jobs_enable_disable(False, parser_args)
