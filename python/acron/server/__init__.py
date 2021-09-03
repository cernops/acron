#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Main acron launcher'''

import logging
from time import time
from flask import Flask, current_app
import flask_login
import pkg_resources
import yaml
from acron.exceptions import AcronError
from acron.server.api.session import User
from acron.server.auth import UserAuth
from acron.constants import Endpoints
from .config import Config

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)',
               'Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'

LOGIN_MANAGER = flask_login.LoginManager()


def scheduler_config(app):
    '''
    Load the configuration for the scheduler backend.

    :param app: the Flask application
    '''
    if app.config['SCHEDULER']['TYPE'] == 'Crontab':
        with open(app.config['SCHEDULER']['CONFIG'] + 'crontab.config', 'r') as config:
            cfg = yaml.safe_load(config)
            app.config['SCHEDULER'].update(cfg)
    elif app.config['SCHEDULER']['TYPE'] == 'Nomad':
        with open(app.confi['SCHEDULER']['CONFIG'] + 'nomad.config', 'r') as config:
            cfg = yaml.safe_load(config)
            app.config['SCHEDULER'].update(cfg)
    elif app.config['SCHEDULER']['TYPE'] == 'Rundeck':
        with open(app.config['SCHEDULER']['CONFIG'] + 'rundeck.config', 'r') as config:
            cfg = yaml.safe_load(config)
            app.config['SCHEDULER'].update(cfg)
    else:
        logging.error(
            'Acron server could not be started. Please provide a supported scheduler backend.')
        raise AcronError
    logging.info('%s scheduler config loaded.',
                 app.config['SCHEDULER']['TYPE'])


def creds_config(app):
    '''
    Load the configuration for the CREDS backend.

    :param app: the Flask application
    '''
    cfg = {}
    if app.config['CREDS']['TYPE'] == 'File':
        with open(app.config['CREDS']['CONFIG'] + 'file.config', 'r') as config:
            cfg = yaml.safe_load(config)
            app.config['CREDS'].update(cfg)
    elif app.config['CREDS']['TYPE'] == 'Vault':
        with open(app.config['CREDS']['CONFIG'] + 'vault.config', 'r') as config:
            cfg = yaml.safe_load(config)
            app.config['CREDS'].update(cfg)
    else:
        logging.error(
            'Acron server could not be started. Please provide a supported creds storage backend.')
        raise AcronError
    logging.info('%s creds storage config loaded.',
                 app.config['CREDS']['TYPE'])


def register_blueprint(app):
    '''
    Register all the blueprints of the Flask application.

    :param app: the Flask application
    '''

    def log_enabled_endpoint(endpoint, api_version):
        '''
        Log that endpoint has been enabled.

        :param endpoint: URL postfix of endpoint
        '''
        logging.info(
            f'{endpoint} endpoint enabled for API version {api_version}.')

    def _list_supported_api_versions(api_version, start_api_version=None):
        '''
        List API versions in an interval.

        :param api_version:       Current API version with format vNUMBER, e.g., v3
        :param start_api_version: Start API version with format vNUMBER, e.g., v1

        :returns: List of backwards compatible API versions, e.g., v1, v2, v3
        '''
        if not start_api_version:
            start_api_version = 'v0'

        # For API version v1, version number is 1
        # Cast string to integer in two steps for easier debugging
        latest_version_number = api_version[1:]
        latest_version_number = int(latest_version_number)

        start_version_number = start_api_version[1:]
        start_version_number = int(start_version_number)

        # Verify API version numbers
        assert start_version_number <= latest_version_number, (
            f'_list_supported_api_versions: Start API version number is larger than latest ' +
            f'{start_version_number} <= {latest_version_number}')

        # For latest_version_number 3 and start_version_number 1, it returns [1, 2, 3]
        # The range in mathematical notation is (start_version_number, latest_version_number]
        # Therefore, we +1 the latest_version_number, to include the api_version.
        supported_version_numbers = list(
            range(start_version_number, latest_version_number+1))

        # Convert from numbers to API versions.
        # Add prefix to api_versions
        # Input: [1, 2, 3]           list(int)
        # Output: ['v1', 'v2', 'v3'] list(str)
        supported_api_versions = list(
            map(lambda version_number: 'v' + str(version_number), supported_version_numbers))

        # Verify that at least the current API is being registered
        assert len(supported_api_versions) > 0, ("_list_supported_api_versions: " +
                                                 f'Wrong arguments given api_version {api_version} and ' +
                                                 f'start_api_version {start_api_version}.' +
                                                 f'Not registering endpoint.')

        return supported_api_versions

    def register_bckwrds_comp_endpoint(blueprint, endpoint):
        '''
        Register backwards compatible endpoint.
        It infers which versions should be supported.

        :param blueprint: Blueprint def. corresponding to endpoint
        :param endpoint: URL postfix of endpoint
        '''
        api_version = app.config['API_VERSION']
        backwards_comp_api_versions = _list_supported_api_versions(
            api_version)

        logging.info(
            f'Registering backwards compatible endpoint {endpoint} ' +
            f'for API versions {backwards_comp_api_versions}.')

        # bc_version stands for backwards compatible version
        for bc_version in backwards_comp_api_versions:
            register_endpoint(blueprint, endpoint, api_version=bc_version)

    def register_restricted_endpoint(blueprint, endpoint, start_api_version):
        '''
        Register endpoint, which is not backwards compatible.
        If start_api_version is lower than api_version, then the endpoint is
        supported for the versions in between.

        :param start_api_version: When the restricted feature was introduced
        :param blueprint:         Blueprint def. corresponding to endpoint
        :param endpoint:          URL postfix of endpoint
        '''
        api_version = app.config['API_VERSION']
        supported_api_versions = _list_supported_api_versions(
            api_version, start_api_version=start_api_version)

        logging.info(
            f'Registering restricted endpoint {endpoint} ' +
            f'for API versions {supported_api_versions}.')

        for supported_version in supported_api_versions:
            register_endpoint(blueprint, endpoint,
                              api_version=supported_version)

    def register_endpoint(blueprint, endpoint, api_version=app.config['API_VERSION']):
        '''
        Log that endpoint has been enabled.

        :param blueprint: Blueprint def. corresponding to endpoint
        :param endpoint: URL postfix of endpoint
        '''
        app.register_blueprint(blueprint, url_prefix='/' +
                               api_version + endpoint)
        log_enabled_endpoint(endpoint, api_version)

    from .api.creds import BP_CREDS
    from .api.jobs import BP_JOBS
    from .api.projects import BP_PROJECTS
    from .api.project import BP_PROJECT
    from .api.system import BP_SYSTEM
    from .api.session import BP_SESSION

    # Always compatible
    register_bckwrds_comp_endpoint(BP_CREDS, Endpoints.CREDS)
    register_bckwrds_comp_endpoint(BP_JOBS, Endpoints.JOBS)
    register_bckwrds_comp_endpoint(BP_SYSTEM, Endpoints.SYSTEM)
    register_bckwrds_comp_endpoint(BP_SESSION, Endpoints.SESSION)

    # Restricted API endpoints (non-backwards compatible)
    register_restricted_endpoint(BP_PROJECTS, Endpoints.PROJECTS,
                                 start_api_version=app.config['PROJECTS_API_VERSION'])
    register_restricted_endpoint(BP_PROJECT, Endpoints.PROJECT,
                                 start_api_version=app.config['PROJECTS_API_VERSION'])


def create_app(config_class=Config):
    '''
    Main application factory. Initializes the Flask framework and load the Blueprints.

    :param config_class: config class holding the default parameters
    :returns: the ready-to-use app
    '''
    app = Flask(__name__)
    app.config.from_object(config_class)
    with open(config_class.CONFIG_FILE, 'r') as config:
        app.config.update(yaml.safe_load(config))

    logging.basicConfig(filename=app.config['LOG_FILE'],
                        level=app.config['LOG_LEVEL'],
                        format='%(asctime)s %(levelname)-8s  %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    logging.info('Acron server version %s started.',
                 pkg_resources.require('acron')[0].version)
    logging.debug('Started in DEBUG logging mode.')

    app.secret_key = app.config['SECRET_KEY']
    app.ttl = app.config['TTL']
    app.user_is_authenticated = {}
    app.user_auth = UserAuth(app.config)

    LOGIN_MANAGER.init_app(app)

    scheduler_config(app)
    creds_config(app)
    register_blueprint(app)

    return app


@LOGIN_MANAGER.user_loader
def user_loader(username):
    ''' flask-login method implementation to get the user '''
    user = User()
    user.id = username
    return user


@LOGIN_MANAGER.request_loader
def request_loader(login_request):
    ''' flask-login method request login '''
    username = login_request.remote_user
    user = User()
    user.id = username
    if current_app.config['ENABLE_2FA']:
        user.set_authenticated(int(time())
                               - current_app.user_auth.getauth(username)
                               < current_app.ttl)
    else:
        user.set_authenticated(True)
    return user


@LOGIN_MANAGER.unauthorized_handler
def unauthorized_handler():
    ''' flask-login method unauthorised '''
    return 'Unauthorized\n'
