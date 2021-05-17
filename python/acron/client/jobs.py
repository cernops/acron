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
from acron.errors import ERRORS
from acron.exceptions import AcronError, AbortError
from .config import CONFIG

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'


def error_no_access():
    '''
    Error message when user has no access to the project.
    '''
    sys.stderr.write('You do not have access.\nPlease check that you have a valid\n')
    sys.stderr.write('Kerberos ticket, that you are registered to the service and\n')
    sys.stderr.write('that you have access rights to the project.\n')


def error_job_not_found():
    '''
    Error message when the requested job can not be found.
    '''
    sys.stderr.write('This job does not exist. Please check the job name and try again.\n')


def error_project_not_found():
    '''
    Error message when the requested project can not be found.
    '''
    sys.stderr.write('This project does not exist. Please create a job first to initialise the project.\n')


def error_unknown(message):
    '''
    Error message when an unknown error occured.

    :param message: raw message returned by the server
    '''
    sys.stderr.write('An unknown error occured, please try again or ')
    sys.stderr.write('contact the support with the following information:\n')
    sys.stderr.write(message + '\n')


# pylint: disable=R0912
def jobs_delete(parser_args):
    '''
    Delete job request to the API.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    try:
        if jobs_get(parser_args) == ERRORS['NOT_FOUND']:
            raise AbortError
        valid_answers = ['y', 'yes', 'n', 'no', '']
        answer = 'not valid'
        while answer not in valid_answers:
            answer = input('Are you sure you want to delete ? [y/N] ')
            if answer.lower() in ['y', 'yes']:
                pass
            elif answer.lower() in ['n', 'no', '']:
                raise AbortError
        params = None if 'project' not in parser_args else {'project': parser_args.project}
        path = CONFIG['ACRON_SERVER_FULL_URL'] + 'jobs/'
        if parser_args.job_id:
            path += parser_args.job_id
        response = requests.delete(path, params=params, auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])
        if response.status_code == 200:
            if parser_args.job_id:
                sys.stdout.write('Job ' + response.json()['name'] + ': ' + response.json()['message'] + '\n')
            else:
                sys.stdout.write(response.json()['message'])
            return_code = ERRORS['OK']
        elif response.status_code in [401, 403]:
            error_no_access()
            return_code = ERRORS['NOT_ALLOWED']
        elif response.status_code == 404:
            if parser_args.job_id:
                error_job_not_found()
            else:
                error_project_not_found()
            return_code = ERRORS['NOT_FOUND']
        else:
            if (hasattr(response, 'json') and hasattr(response.json(), 'keys') and
                    'message' in response.json().keys()):
                sys.stderr.write(response.json()['message'] + '\n')
            else:
                error_unknown(response.content)
            return_code = ERRORS['BACKEND_ERROR']
    except (AbortError, KeyboardInterrupt):
        sys.stderr.write('\nAbort.\n')
        return_code = ERRORS['ABORT']
    except AcronError as error:
        error_unknown(str(error))
        return_code = ERRORS['BACKEND_ERROR']
    return return_code


def _write_job_to_console(job_properties):
    '''
    Write a job to the console.

    :param job_properties: a dictionary containing the job's properties
    '''
    sys.stdout.write('#' + ' '.join(job_properties['description'].split(' ')[5:]) + '\n')
    sys.stdout.write(('#' if not job_properties['scheduleEnabled'] else '') + job_properties['name'] + ': ')
    sys.stdout.write(' '.join(job_properties['description'].split(' ')[0:5]) + ' ')
    sys.stdout.write(job_properties['nodefilters']['filter'].replace('name: ', '') + ' ')
    sys.stdout.write(job_properties['sequence']['commands'][0]['exec'] + '\n')


def jobs_get(parser_args):
    '''
    Get job information request to the API.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    try:
        params = None if 'project' not in parser_args else {'project': parser_args.project}
        path = CONFIG['ACRON_SERVER_FULL_URL'] + 'jobs/'
        if parser_args.job_id:
            path += parser_args.job_id
        response = requests.get(path, params=params, auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])
        if response.status_code == 200:
            if not parser_args.job_id:
                if hasattr(response, 'json') and isinstance(response.json(), dict):
                    sys.stdout.write(response.json()['message'] + '\n')
                else:
                    sys.stdout.write('Found ' + str(len(response.json())) + ' job(s) in the project:\n')
                    for job_properties in response.json():
                        _write_job_to_console(job_properties)
            else:
                _write_job_to_console(response.json())
            return_code = ERRORS['OK']
        elif response.status_code in [401, 403]:
            error_no_access()
            return_code = ERRORS['NOT_ALLOWED']
        elif response.status_code == 404:
            if parser_args.job_id:
                error_job_not_found()
            else:
                error_project_not_found()
            return_code = ERRORS['NOT_FOUND']
        else:
            if (hasattr(response, 'json') and hasattr(response.json(), 'keys') and
                    'message' in response.json().keys()):
                sys.stderr.write(response.json()['message'] + '\n')
            else:
                error_unknown(response.content)
            return_code = ERRORS['BACKEND_ERROR']

    except (AbortError, KeyboardInterrupt):
        sys.stderr.write('\nAbort.\n')
        return_code = ERRORS['ABORT']
    except AcronError as error:
        error_unknown(str(error))
        return_code = ERRORS['BACKEND_ERROR']
    return return_code


def jobs_post(parser_args):
    '''
    Create a new job or update an existing one.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    try:
        if (not parser_args.schedule and not parser_args.target and
                not parser_args.command and not parser_args.description):
            sys.stderr.write('Please specify at least one of schedule, target, ')
            sys.stderr.write('command or description to update.\n')
            raise AbortError
        if parser_args.description is None:
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
        path = CONFIG['ACRON_SERVER_FULL_URL'] + 'jobs/'
        if hasattr(parser_args, 'job_id'):
            path += parser_args.job_id
            response = requests.put(path, params=params, auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])
        else:
            response = requests.post(path, params=params, auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])
        if response.status_code == 200:
            _write_job_to_console(response.json())
            return_code = ERRORS['OK']
        elif response.status_code in [401, 403]:
            error_no_access()
            return_code = ERRORS['NOT_ALLOWED']
        elif response.status_code == 404:
            error_job_not_found()
            return_code = ERRORS['NOT_FOUND']
        elif response.status_code == 503:
            sys.stderr.write('The backend is currently not available. Try again later.\n')
            return_code = ERRORS['BACKEND_ERROR']
        elif response.status_code == 500:
            sys.stderr.write('BUG: The backend experienced an error. Please report this issue, quoting the full command and time stamp.\n')#pylint:disable=line-too-long
            return_code = ERRORS['BACKEND_ERROR']
        else:
            if (hasattr(response, 'json') and hasattr(response.json(), 'keys') and
                    'message' in response.json().keys()):
                sys.stderr.write(response.json()['message'] + '\n')
            else:
                error_unknown(response.content)
            return_code = ERRORS['BACKEND_ERROR']

    except (AbortError, KeyboardInterrupt):
        sys.stderr.write('\nAbort.\n')
        return_code = ERRORS['ABORT']
    except AcronError as error:
        error_unknown(str(error))
        return_code = ERRORS['BACKEND_ERROR']
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
        path = CONFIG['ACRON_SERVER_FULL_URL'] + 'jobs/'
        if parser_args.job_id:
            path += parser_args.job_id
        response = requests.patch(path, params=params, auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])
        if response.status_code == 200:
            if parser_args.job_id:
                sys.stdout.write('Job ' + response.json()['name'] + ': ')
                sys.stdout.write(response.json()['message'] + '\n')
            else:
                sys.stdout.write(response.json()['message'] + '\n')
            return_code = ERRORS['OK']
        elif response.status_code in [401, 403]:
            error_no_access()
            return_code = ERRORS['NOT_ALLOWED']
        elif response.status_code == 404:
            if parser_args.job_id:
                error_job_not_found()
            else:
                error_project_not_found()
            return_code = ERRORS['NOT_FOUND']
        else:
            if (hasattr(response, 'json') and hasattr(response.json(), 'keys') and
                    'message' in response.json().keys()):
                sys.stderr.write(response.json()['message'] + '\n')
            else:
                error_unknown(response.content)
            return_code = ERRORS['BACKEND_ERROR']

    except (AbortError, KeyboardInterrupt):
        sys.stderr.write('\nAbort.\n')
        return_code = ERRORS['ABORT']
    except AcronError as error:
        error_unknown(str(error))
        return_code = ERRORS['BACKEND_ERROR']
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
