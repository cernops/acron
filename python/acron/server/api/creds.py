#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Credentials management submodule'''

import logging
import os
from shutil import rmtree
from tempfile import mkdtemp
from flask import Blueprint, current_app, request
from flask_login import login_required
from acron.errors import ERRORS
from acron.server.http import http_response
from acron.server.utils import default_log_line_request, dump_args, get_remote_hostname
from acron.server.utils import krb_init_keytab
from acron.exceptions import (ArgsMissingError, ArgsMalformedError, CredsError,
                              CredsNoFileError, KinitError)

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)', 'Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


# Blueprint storing all routes and function calls
BP_CREDS = Blueprint('creds', __name__)


@dump_args
def update_creds(creds_storage):
    '''
    Check uploaded file for validity and forward it to the backend creds storage.

    :param creds_storage: the creds storage backend
    :returns:             an HTTP payload
    '''
    status_code = ERRORS['OK']

    try:
        if 'creds' not in request.files:
            raise ArgsMissingError('User did not provide a credentials file')

        temp_dir = mkdtemp()
        os.chmod(temp_dir, 0o0755)
        keytab_encrypted_path = os.path.join(temp_dir, 'keytab.gpg')
        keytab_encrypted = open(keytab_encrypted_path, 'wb+')
        os.chmod(keytab_encrypted_path, 0o0644)

        file_uploaded = request.files['creds']
        if not file_uploaded or file_uploaded.filename == '':
            raise ArgsMalformedError('User provided an empty keytab')
        file_uploaded.save(keytab_encrypted)
        file_uploaded.close()
        keytab_encrypted.close()
        if (os.stat(keytab_encrypted_path).st_size > current_app.config['CREDS']['KEYTAB_MAX_LENGTH'] or
                os.stat(keytab_encrypted_path).st_size == 0):
            raise ArgsMalformedError('User provided a wrongly formatted keytab')

        creds_storage.update_creds(keytab_encrypted_path)

    except (ArgsMissingError, ArgsMalformedError) as error:
        logging.warning('%s on /creds/: %s', default_log_line_request(), error)
        status_code = ERRORS['BAD_ARGS']
    except CredsError as error:
        logging.error('%s on /creds/: %s', default_log_line_request(), error)
        status_code = ERRORS['BACKEND_ERROR']

    finally:
        rmtree(temp_dir)

    return http_response(status_code)


@dump_args
def get_creds_status(creds_storage):
    '''
    Retrieve the file from the backend storage and check if the creds are still valid.

    :param creds_storage: the creds storage backend
    :returns:             an HTTP payload
    '''
    status_code = ERRORS['OK']

    try:
        file_local = creds_storage.get_creds()
        krb_init_keytab(file_local, request.remote_user)

    except CredsNoFileError:
        logging.warning('%s on /creds/: Creds backend does not have the users credentials.',
                        default_log_line_request())
        status_code = ERRORS['NO_VALID_CREDS']
    except KinitError:
        logging.warning('%s on /creds/: Kerberos keytab initialization failed.', default_log_line_request())
        status_code = ERRORS['CREDS_INVALID']
    except CredsError as error:
        logging.error('%s on /creds/: Creds backend failed to deliver creds. %s',
                      default_log_line_request(), error)
        status_code = ERRORS['BACKEND_ERROR']

    return http_response(status_code)


@dump_args
def delete_creds(creds_storage):
    '''
    Make a request to the backend to delete the given creds.

    :param creds_storage: the creds storage backend
    :returns:             an HTTP payload
    '''
    status_code = ERRORS['OK']

    try:
        creds_storage.delete_creds()
    except CredsNoFileError:
        logging.warning('%s on /creds/: Creds backend does not have the users credentials.',
                        default_log_line_request())
        status_code = ERRORS['NOT_FOUND']
    except CredsError as error:
        logging.error('%s on /creds/: Creds backend encountered an error. %s',
                      default_log_line_request(), error)
        status_code = ERRORS['BACKEND_ERROR']

    return http_response(status_code)


@dump_args
def setup_creds_storage():
    '''
    Instantiate the Creds class based on the config.

    :returns: a Creds instance
    '''
    if current_app.config['CREDS']['TYPE'] == 'File':
        from acron.server.backend.creds.file import File
        creds_class = File
    elif current_app.config['CREDS']['TYPE'] == 'Vault':
        from acron.server.backend.creds.vault import Vault
        creds_class = Vault
    else:
        logging.warning('User %s (%s) requests %s file backend: backend not implemented.',
                        request.remote_user, get_remote_hostname(),
                        current_app.config['CREDS']['TYPE'])
        raise ValueError('Only file backends currently supported are: File and Vault')

    return creds_class(request.remote_user, current_app.config)


@BP_CREDS.route('/', methods=['PUT', 'GET', 'DELETE'])
@login_required
def creds():
    '''
    Launcher for credentials actions
    PUT: create or update credentials
    GET: get status of stored credentials
    DELETE: delete stored credentials, does nothing if no credentials stored
    '''
    creds_storage = setup_creds_storage()
    logging.info('%s on /creds/.', default_log_line_request())

    if request.method == 'PUT':
        return update_creds(creds_storage)

    if request.method == 'GET':
        return get_creds_status(creds_storage)

    if request.method == 'DELETE':
        return delete_creds(creds_storage)

    logging.critical('%s on /creds/: Method not allowed!', default_log_line_request())
    raise ValueError('Critical error: method not allowed!')
