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
from acron.errors import ERRORS
from acron.exceptions import AcronError, AbortError, GPGError, KinitError, KTUtilError
from acron.utils import (get_current_user, gpg_add_public_key, gpg_encrypt_file, gpg_key_exist,
                         keytab_generator, krb_init_keytab)
from .config import CONFIG

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'


def error_no_access():
    '''
    Error message when user has no access to the service.
    '''
    sys.stderr.write('You do not have access.\nPlease check that you have a valid ')
    sys.stderr.write('Kerberos ticket and that you are registered to the service ')
    sys.stderr.write(f"({CONFIG['AUTHORIZED_USER_GROUP']} group).\n")

def error_creds_expired():
    '''
    Error message when user credentials have expired.
    '''
    sys.stderr.write('Your uploaded credentials are no longer valid.')
    sys.stderr.write('They may have expired, or your password may have been changed recently. ')
    sys.stderr.write('Please update them using the "acron creds upload -g" command.')


def error_unknown(message):
    '''
    Error message when an unknown error occured.

    :param message: raw message returned by the server
    '''
    sys.stderr.write('An unknown error occured, please try again or ')
    sys.stderr.write('contact the support with the following information:\n')
    sys.stderr.write(message)


# pylint: disable=W0613
def creds_delete(parser_args):
    '''
    Delete credentials request to the API.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    try:
        response = requests.delete(
            CONFIG['ACRON_SERVER_FULL_URL'] + 'creds/',
            auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])
        if response.status_code == 200:
            sys.stdout.write('Credentials successfully deleted.\n')
            return_code = ERRORS['OK']
        elif response.status_code in [401, 403]:
            error_no_access()
            return_code = ERRORS['NOT_ALLOWED']
        elif response.status_code == 404:
            sys.stdout.write('No credentials on the server, nothing to delete.\n')
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


def creds_get(parser_args):
    '''
    Get credentials status request to the API.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    try:
        response = requests.get(
            CONFIG['ACRON_SERVER_FULL_URL'] + 'creds/',
            auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])
        if response.status_code == 200:
            sys.stdout.write('Credentials are on the server and valid.\n')
            return_code = ERRORS['OK']
        elif response.status_code in [401, 403]:
            error_no_access()
            return_code = ERRORS['NOT_ALLOWED']
        elif response.status_code == 500:
            error_creds_expired()
            return_code = ERRORS['CREDS_INVALID']
        else:
            if (hasattr(response, 'json') and hasattr(response.json(), 'keys') and
                    'message' in response.json().keys()):
                sys.stderr.write(response.json()['message'] + '\n')
                return_code = ERRORS['NO_VALID_CREDS']
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


# pylint: disable=R0912, R0915
def creds_put(parser_args):
    '''
    Create, update or upload credentials request to the API.

    :param parser_args: dictionary containing the user input from the parser
    :returns:           the API's return value
    '''
    return_code = ERRORS['OK']
    username = get_current_user()
    try:
        if parser_args.file:
            if not os.path.isfile(parser_args.file):
                sys.stderr.write('The file ' + parser_args.file + ' does not exist!\n')
                sys.stderr.write('Please verify your entry and try again.')
                raise ValueError
            keytab = parser_args.file
        elif parser_args.generate:
            sys.stdout.write('Where do you want to save the keytab on disk ')
            sys.stdout.write('(press Enter to confirm or enter new path)?\n')
            default_path = os.path.expandvars(os.path.expanduser(CONFIG['KEYTAB_DEFAULT_PATH']))
            default_path += "/" + username + '.keytab'
            answer = input('(' + default_path + ') ')
            if answer == '':
                keytab = default_path
            else:
                keytab = answer
            if not os.path.isdir(os.path.abspath(os.path.join(keytab, os.pardir))):
                sys.stderr.write('Parent folder does not exist, please create it first.\n')
                raise AbortError
            if os.path.isfile(keytab):
                sys.stdout.write('A file with the same name already exists. ')
                answer = input('Replace it? [y/N] ')
                if answer in ['y', 'yes']:
                    os.remove(keytab)
                elif answer in ['n', 'no', '']:
                    sys.stderr.write('OK, so we will add credentials to the exiting keytab file...\n')#pylint: disable=line-too-long
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
                sys.stderr.write('Generating keytab entry for principal %s@%s\n' % (username, realm))#pylint: disable=line-too-long
                keytab_generator(username, realm, CONFIG['KEYTAB_ENCRYPTION_TYPES'], keytab,
                                 flavor=CONFIG['KRB_CLIENTS_FLAVOR'],
                                 script=CONFIG['CUSTOM_KEYTAB_GENERATOR'] if 'CUSTOM_KEYTAB_GENERATOR' in CONFIG else None)#pylint: disable=line-too-long
            sys.stdout.write('Keytab successfully created at ' + os.path.expanduser(keytab) + '\n')
        krb_init_keytab(keytab, username)
        sys.stdout.write(' +=====+ ' + 'Your keytab is ready to be sent to the Acron server. \n')#pylint: disable=line-too-long
        sys.stdout.write(' |  I  | ' + 'Please be aware that you are delegating your credentials \n')#pylint: disable=line-too-long
        sys.stdout.write(' |  I  | ' + 'to the Acron service. By doing so, you authorize the \n')#pylint: disable=line-too-long
        sys.stdout.write(' |  .  | ' + 'Acron service to impersonate you during the execution of \n')#pylint: disable=line-too-long
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
            sys.stdout.write('It looks like the acron public GPG key has not yet ')
            sys.stdout.write('been added to your keyring.\n')
            valid_answers = ['y', 'yes', 'n', 'no', '']
            answer = 'not valid'
            while answer not in valid_answers:
                answer = input('Add it now? [y/N] ')
                if answer.lower() in ['y', 'yes']:
                    sys.stdout.write('Adding the acron public key in your gnupg keyring...')
                    gpg_add_public_key(CONFIG['GPG_BINARY_PATH'], CONFIG['GPG_PUBLIC_KEY_PATH'])#pylint: disable=line-too-long
                    sys.stdout.write('Key successfully added\n')
                elif answer.lower() in ['n', 'no', '']:
                    raise AbortError

        temp_dir = mkdtemp()
        keytab_encrypted = os.path.join(temp_dir, 'keytab.gpg')
        sys.stdout.write('Encrypting the keytab... ')
        gpg_encrypt_file(keytab, keytab_encrypted, CONFIG['GPG_BINARY_PATH'], CONFIG['GPG_PUBLIC_KEY_NAME'])#pylint: disable=line-too-long
        sys.stdout.write('Keytab successfully encrypted\n')
        files = {'keytab': open(keytab_encrypted, 'rb')}
        sys.stdout.write('Sending the keytab to the server...\n')
        response = requests.put(
            CONFIG['ACRON_SERVER_FULL_URL'] + 'creds/', files=files,
            auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])
        if response.status_code == 200:
            sys.stdout.write('Credentials successfully uploaded to the server.\n')
        elif response.status_code in [401, 403]:
            error_no_access()
            return_code = ERRORS['NOT_ALLOWED']
        else:
            if (hasattr(response, 'json') and hasattr(response.json(), 'keys') and
                    'message' in response.json().keys()):
                sys.stderr.write(response.json()['message'] + '\n')
            else:
                error_unknown(response.content)
            return_code = ERRORS['BACKEND_ERROR']

    except OSError as error:
        if error.errno == errno.ENOENT:
            pass
        else:
            sys.stderr.write('File already exists and can not be deleted. ' + str(error) + '\n')
            return_code = ERRORS['BACKEND_ERROR']
    except KTUtilError as error:
        sys.stderr.write('Error in keytab creation: ' + str(error) + '\n')
        sys.stderr.write('This can be caused by:\n')
        sys.stderr.write('  * a ktutil version not supporting salted encryption types (eg on RHEL7/CentOS7)\n')#pylint: disable=line-too-long
        sys.stderr.write('  * a mistyped password\n')
        sys.stderr.write('  * something else\n')
        sys.stderr.write('If the problem persists, please inform the service managers.\n')
        return_code = ERRORS['BACKEND_ERROR']
    except KinitError as error:
        sys.stderr.write('Error in keytab verification: ' + str(error) + '\n')
        sys.stderr.write('This can be caused by:\n')
        sys.stderr.write('  * a ktutil version not supporting salted encryption types (eg on RHEL7/CentOS7)\n')#pylint: disable=line-too-long
        sys.stderr.write('  * a mistyped password\n')
        sys.stderr.write('Check if you entered the correct password or retry on a more recent OS.\n')#pylint: disable=line-too-long
        return_code = ERRORS['BAD_ARGS']
    except GPGError as error:
        sys.stderr.write('Error whilst encyphering your keytab: ' + str(error) + '\n')
        sys.stderr.write('Please try again or raise a ticket towards the Acron\n')
        sys.stderr.write('service if the error persists.\n')
        return_code = ERRORS['BACKEND_ERROR']
    except ValueError:
        return_code = ERRORS['BAD_ARGS']
    except (AbortError, KeyboardInterrupt):
        sys.stderr.write('\nAbort.\n')
    except AcronError as error:
        error_unknown(str(error))
        return_code = ERRORS['BACKEND_ERROR']
    finally:
        try:
            rmtree(temp_dir)
        except NameError:
            pass # exception occured before temp_dir was assigned

    return return_code
