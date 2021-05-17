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
from flask import Flask, request, current_app
import flask_login
import pkg_resources
import yaml
from acron.exceptions import AcronError
from acron.server.api.session import User
from acron.server.auth import UserAuth
from .config import Config

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
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
        logging.error('Acron server could not be started. Please provide a supported scheduler backend.')
        raise AcronError
    logging.info('%s scheduler config loaded.', app.config['SCHEDULER']['TYPE'])


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
        logging.error('Acron server could not be started. Please provide a supported creds storage backend.')
        raise AcronError
    logging.info('%s creds storage config loaded.', app.config['CREDS']['TYPE'])

def register_blueprint(app):
    '''
    Register all the blueprints of the Flask application.

    :param app: the Flask application
    '''
    from .api.creds import BP_CREDS
    app.register_blueprint(BP_CREDS, url_prefix='/' + app.config['API_VERSION'] + '/creds')
    logging.info('/creds endpoint enabled.')

    from .api.jobs import BP_JOBS
    app.register_blueprint(BP_JOBS, url_prefix='/' + app.config['API_VERSION'] + '/jobs')
    logging.info('/jobs endpoint enabled.')

    from .api.projects import BP_PROJECTS
    app.register_blueprint(BP_PROJECTS, url_prefix='/' + app.config['API_VERSION'] + '/projects')
    logging.info('/projects endpoint enabled.')

    from .api.system import BP_SYSTEM
    app.register_blueprint(BP_SYSTEM, url_prefix='/' + app.config['API_VERSION'] + '/system')
    logging.info('/system endpoint enabled.')

    from .api.session import BP_SESSION
    app.register_blueprint(BP_SESSION, url_prefix='/' + app.config['API_VERSION'] + '/session')
    logging.info('/session endpoint enabled.')

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

    logging.info('DEV Acron server version %s started.', pkg_resources.require('acron')[0].version)
    logging.debug('DEV Started in DEBUG logging mode.')

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
    ''' flusk-login method implementation to get the user '''
    user = User()
    user.id = username
    return user

@LOGIN_MANAGER.request_loader
def request_loader(login_request):
    ''' flusk-login method request login '''
    username = login_request.remote_user
    user = User()
    user.id = username
    if current_app.config['ENABLE_2FA']:
        user.set_authenticated(int(time())
                               -current_app.user_auth.getauth(username)
                               < current_app.ttl)
    else:
        user.set_authenticated(True)
    return user

@LOGIN_MANAGER.unauthorized_handler
def unauthorized_handler():
    ''' flusk-login method unauthorised '''
    return 'Unauthorized\n'
