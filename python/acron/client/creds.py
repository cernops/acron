#
# (C) Copyright 2019-2021 CERN
#
# This  software  is  distributed  under  the  terms  of  the
#  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Credentials management functions'''

import errno
import os
from shutil import rmtree
import sys
from tempfile import mkdtemp
import requests
from requests_gssapi import HTTPSPNEGOAuth
from acron.exceptions import AcronError, AbortError, GPGError, KinitError, KTUtilError
from acron.utils import (get_current_user, gpg_add_public_key, gpg_encrypt_file, gpg_key_exist,
                         keytab_generator, krb_init_keytab)
from acron.constants import Endpoints, ReturnCodes
from .config import CONFIG
from .errors import ServerError

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)',
               'Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


def _handle_found_get(*_):
    '''
    Handle HTTP response status code 200 (OK)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''

    sys.stdout.write('Credentials are on the server and valid.\n')
    return ReturnCodes.OK


def _handle_found_put(*_):
    '''
    Handle HTTP response status code 200 (OK)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''

    sys.stdout.write('Credentials successfully uploaded to the server.\n')
    return ReturnCodes.OK


def _handle_found_delete(*_):
    '''
    Handle HTTP response status code 200 (OK)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''

    sys.stdout.write('Credentials successfully deleted.\n')
    return ReturnCodes.OK


def _handle_no_access(*_):
    '''
    Handle HTTP response status code 401 (Unauthorized) and 403 (Forbidden)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''

    ServerError.error_no_access_job()
    return ReturnCodes.NOT_ALLOWED


def _handle_not_found(*_):
    '''
    Handle HTTP response status code 404 (Not Found)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''

    return_code = ReturnCodes.NOT_FOUND

    ServerError.error_creds_not_found()

    return return_code


def _handle_internal_error(*_):
    '''
    Handle HTTP response status code 500 (Internal Server Error)

    :params *_: Ignore parameters passed
    :returns:   the API's return value
    '''

    ServerError.error_creds_expired()
    return ReturnCodes.CREDS_INVALID


def _handle_invalid(response):
    '''
    Handle unrecognized HTTP response status code generically

    :params response: HTTP response from server
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


def _handle_invalid_get(response):
    '''
    Handle unrecognized HTTP response status code generically

    :params response: HTTP response from server
    :returns:         the API's return value
    '''
    print_error_fallback = True
    try:
        if (hasattr(response, 'json') and hasattr(response.json(), 'keys') and
                'message' in response.json().keys()):
            sys.stderr.write(response.json()['message'] + '\n')
            print_error_fallback = False
            return_code = ReturnCodes.NO_VALID_CREDS
    finally:
        return_code = ReturnCodes.BACKEND_ERROR
        if print_error_fallback:
            ServerError.error_unknown(response.text)

    return return_code


# pylint: disable=W0613
def creds_delete(parser_args):
    '''
    Delete credentials request to the API.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    try:
        response = requests.delete(
            CONFIG['ACRON_SERVER_FULL_URL'] + Endpoints.CREDS_TRAILING_SLASH,
            auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])

        http_status_code_switcher = {
            200: _handle_found_delete,
            401: _handle_no_access,
            403: _handle_no_access,
            404: _handle_not_found,
        }

        handler = http_status_code_switcher.get(
            response.status_code, _handle_invalid)

        return_code = handler(response)
    except (AbortError, KeyboardInterrupt):
        sys.stderr.write('\nAbort.\n')
        return_code = ReturnCodes.ABORT
    except AcronError as error:
        ServerError.error_unknown(str(error))
        return_code = ReturnCodes.BACKEND_ERROR
    return return_code


def creds_get(parser_args):
    '''
    Get credentials status request to the API.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    try:
        response = requests.get(
            CONFIG['ACRON_SERVER_FULL_URL'] + Endpoints.CREDS_TRAILING_SLASH,
            auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])

        http_status_code_switcher = {
            200: _handle_found_get,
            401: _handle_no_access,
            403: _handle_no_access,
            404: _handle_not_found,
            500: _handle_internal_error
        }

        handler = http_status_code_switcher.get(
            response.status_code, _handle_invalid_get)

        return_code = handler(response)
    except (AbortError, KeyboardInterrupt):
        sys.stderr.write('\nAbort.\n')
        return_code = ReturnCodes.ABORT
    except AcronError as error:
        ServerError.error_unknown(str(error))
        return_code = ReturnCodes.BACKEND_ERROR
    return return_code


# pylint: disable=R0912, R0915, too-many-locals
def creds_put(parser_args):
    '''
    Create, update or upload credentials request to the API.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    return_code = ReturnCodes.OK
    username = get_current_user()
    try:
        if parser_args.file:
            if not os.path.isfile(parser_args.file):
                sys.stderr.write(
                    'The file ' + parser_args.file + ' does not exist!\n')
                sys.stderr.write('Please verify your entry and try again.')
                raise ValueError
            creds_file = parser_args.file
        elif parser_args.generate:
            sys.stdout.write('Where do you want to save the keytab on disk ')
            sys.stdout.write('(press Enter to confirm or enter new path)?\n')
            default_path = os.path.expandvars(
                os.path.expanduser(CONFIG['KEYTAB_DEFAULT_PATH']))
            default_path += "/" + username + '.keytab'
            answer = input('(' + default_path + ') ')
            if answer == '':
                creds_file = default_path
            else:
                creds_file = answer
            if not os.path.isdir(os.path.abspath(os.path.join(creds_file, os.pardir))):
                sys.stderr.write(
                    'Parent folder does not exist, please create it first.\n')
                raise AbortError
            if os.path.isfile(creds_file):
                sys.stdout.write('A file with the same name already exists. ')
                answer = input('Replace it? [y/N] ')
                if answer in ['y', 'yes']:
                    os.remove(creds_file)
                elif answer in ['n', 'no', '']:
                    sys.stderr.write(
                        'OK, so we will add credentials to the existing keytab file...\n')
                else:
                    sys.stderr.write('Please provide a valid answer.\n')
                    raise ValueError
            realms = []
            if isinstance(CONFIG['DOMAIN'], list):
                for realm in CONFIG['DOMAIN']:
                    realms.append(realm.upper())
            else:
                realms.append(CONFIG['DOMAIN'].upper())
            for realm in realms:
                sys.stderr.write('Generating keytab entry for principal %s@%s\n' %
                                 (username, realm))
                keytab_generator(username, realm, CONFIG['KEYTAB_ENCRYPTION_TYPES'], creds_file,
                                 flavor=CONFIG['KRB_CLIENTS_FLAVOR'],
                                 script=CONFIG['CUSTOM_KEYTAB_GENERATOR'] if 'CUSTOM_KEYTAB_GENERATOR' in CONFIG else None)  # pylint: disable=line-too-long
            sys.stdout.write('Keytab successfully created at ' +
                             os.path.expanduser(creds_file) + '\n')
        krb_init_keytab(creds_file, username)
        sys.stdout.write(
            ' +=====+ ' + 'Your credentials are ready to be sent to the Acron server. \n')
        sys.stdout.write(
            ' |  I  | ' + 'Please be aware that you are delegating your credentials \n')
        sys.stdout.write(
            ' |  I  | ' + 'to the Acron service. By doing so, you authorize the \n')
        sys.stdout.write(
            ' |  .  | ' + 'Acron service to impersonate you during the execution of \n')
        sys.stdout.write(' +=====+ ' + 'tasks scheduled for this account. \n')
        answer = input('Do you agree to those terms? [y/N] ')
        if answer in ['y', 'yes']:
            pass
        elif answer in ['n', 'no', '']:
            raise AbortError
        else:
            sys.stderr.write('Please provide a valid answer.\n')
            raise ValueError

        if not gpg_key_exist(CONFIG['GPG_BINARY_PATH'], CONFIG['GPG_PUBLIC_KEY_NAME']):
            sys.stdout.write(
                'It looks like the acron public GPG key has not yet ')
            sys.stdout.write('been added to your keyring.\n')
            valid_answers = ['y', 'yes', 'n', 'no', '']
            answer = 'not valid'
            while answer not in valid_answers:
                answer = input('Add it now? [y/N] ')
                if answer.lower() in ['y', 'yes']:
                    sys.stdout.write(
                        'Adding the acron public key in your gnupg keyring...')
                    gpg_add_public_key(
                        CONFIG['GPG_BINARY_PATH'], CONFIG['GPG_PUBLIC_KEY_PATH'])
                    sys.stdout.write('Key successfully added\n')
                elif answer.lower() in ['n', 'no', '']:
                    raise AbortError

        temp_dir = mkdtemp()
        creds_file_encrypted = os.path.join(temp_dir, 'keytab.gpg')
        sys.stdout.write('Encrypting credentials file... ')
        gpg_encrypt_file(creds_file, creds_file_encrypted,
                         CONFIG['GPG_BINARY_PATH'], CONFIG['GPG_PUBLIC_KEY_NAME'])
        sys.stdout.write('Credentials file successfully encrypted\n')
        files = {'keytab': open(creds_file_encrypted, 'rb')}
        sys.stdout.write('Sending credentials file to the server...\n')
        response = requests.put(
            CONFIG['ACRON_SERVER_FULL_URL'] + Endpoints.CREDS_TRAILING_SLASH, files=files,
            auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])

        http_status_code_switcher = {
            200: _handle_found_put,
            401: _handle_no_access,
            403: _handle_no_access,
            404: _handle_not_found,
        }

        handler = http_status_code_switcher.get(
            response.status_code, _handle_invalid)

        return_code = handler(response)

    except OSError as error:
        if error.errno == errno.ENOENT:
            pass
        else:
            sys.stderr.write(
                'File already exists and can not be deleted. ' + str(error) + '\n')
            return_code = ReturnCodes.BACKEND_ERROR
    except KTUtilError as error:
        sys.stderr.write('Error in keytab creation: ' + str(error) + '\n')
        sys.stderr.write('This can be caused by:\n')
        sys.stderr.write(
            '  * a ktutil version not supporting salted encryption types (e.g. on RHEL7/CentOS7)\n')
        sys.stderr.write('  * a mistyped password\n')
        sys.stderr.write('  * something else\n')
        sys.stderr.write(
            'If the problem persists, please inform the service managers.\n')
        return_code = ReturnCodes.BACKEND_ERROR
    except KinitError as error:
        sys.stderr.write('Error in keytab verification: ' + str(error) + '\n')
        sys.stderr.write('This can be caused by:\n')
        sys.stderr.write(
            '  * a ktutil version not supporting salted encryption types (e.g. on RHEL7/CentOS7)\n')
        sys.stderr.write('  * a mistyped password\n')
        sys.stderr.write(
            'Check if you entered the correct password or retry on a more recent OS.\n')
        return_code = ReturnCodes.BAD_ARGS
    except GPGError as error:
        sys.stderr.write(
            'Error whilst encyphering your credentials file: ' + str(error) + '\n')
        sys.stderr.write(
            'Please try again or raise a ticket towards the Acron\n')
        sys.stderr.write('service if the error persists.\n')
        return_code = ReturnCodes.BACKEND_ERROR
    except ValueError:
        return_code = ReturnCodes.BAD_ARGS
    except (AbortError, KeyboardInterrupt):
        sys.stderr.write('\nAbort.\n')
    except AcronError as error:
        ServerError.error_unknown(str(error))
        return_code = ReturnCodes.BACKEND_ERROR
    finally:
        try:
            rmtree(temp_dir)
        except NameError:
            pass  # exception occurred before temp_dir was assigned

    return return_code
