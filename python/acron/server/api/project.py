#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Project management submodule'''

from flask import Blueprint, request, jsonify
from flask_login import login_required
from acron.server.utils import dump_args
from acron.server.constants import HttpMethods
from acron.server.log import Logger, LogLevel
from acron.server.http import http_response
from acron.exceptions import (NoAccessError, NotShareableError,
                              ProjectNotFoundError, ArgsMalformedError, UserNotFoundError)
from acron.constants import Endpoints, ReturnCodes
from .utils import setup_scheduler

__author__ = 'Rodrigo Bermudez Schettino (CERN)'
__credits__ = ['Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


# Blueprint storing all routes and function calls
BP_PROJECT = Blueprint('project', __name__)


def _log_project_request(level=LogLevel.INFO, msg=''):
    '''
    Log requests to project endpoint

    :param level: severity level, see LogLevel.
    :param msg: message to log
    '''
    Logger.log_request(Endpoints.PROJECT, level, msg)


@dump_args
def _get_project_name(scheduler):
    '''
    Request from the backend the name of the current project.

    :param scheduler: the scheduler backend
    :returns:         the backend's response
    '''
    try:
        return jsonify(scheduler.get_project_name())
    except ProjectNotFoundError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_FOUND)


@dump_args
def _get_project_users(scheduler):
    '''
    Request from the backend the users in the current project.

    :param scheduler: the scheduler backend
    :returns:         the backend's response
    '''
    try:
        return jsonify(scheduler.get_project_users())
    except ProjectNotFoundError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_FOUND)
    except NotShareableError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_ALLOWED)


@dump_args
def _share_project(scheduler, user, perms):
    '''
    Request from the backend to share the current project with another user.

    :param scheduler: the scheduler backend
    :param user:      username
    :param perms:     project permissions
    :returns:         the backend's response
    '''
    try:
        return jsonify(scheduler.share_project(user, perms))
    except ProjectNotFoundError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_FOUND)
    except NotShareableError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_ALLOWED)
    except ArgsMalformedError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.BAD_ARGS)
    except UserNotFoundError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_FOUND)


@dump_args
def _undo_share_project(scheduler, user):
    '''
    Request from the backend to delete project share for user.

    :param scheduler: the scheduler backend
    :param user:      username
    :returns:         the backend's response
    '''
    try:
        return jsonify(scheduler.undo_share_project(user))
    except ProjectNotFoundError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_FOUND)
    except ArgsMalformedError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.BAD_ARGS)
    except UserNotFoundError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_FOUND)


@dump_args
def _delete_project(scheduler):
    '''
    Request from the backend the deletion of the current project.

    :param scheduler: the scheduler backend
    :returns:         the backend's response
    '''
    try:
        return jsonify(scheduler.delete_project(scheduler.project_id, scheduler.config))
    except ProjectNotFoundError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_FOUND)


@BP_PROJECT.route('/users', methods=[HttpMethods.GET])
def project_users():
    '''
    Launcher for project with named user action

    GET: get project users
    '''
    try:
        scheduler = setup_scheduler(Endpoints.PROJECT)
    except (NoAccessError, NotShareableError) as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_ALLOWED)
    except ProjectNotFoundError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_FOUND)

    _log_project_request(level=LogLevel.INFO)

    if not request.method == HttpMethods.GET:
        error_method_not_allowed = 'Method not allowed!'
        _log_project_request(LogLevel.CRITICAL, error_method_not_allowed)
        raise ValueError(f'Critical error: {error_method_not_allowed}]')

    return _get_project_users(scheduler)


@BP_PROJECT.route('/', methods=[HttpMethods.GET, HttpMethods.DELETE])
@login_required
def project():
    '''
    Launcher for unnamed project actions

    GET: get list of users in project
    DELETE: delete project
    '''
    try:
        scheduler = setup_scheduler(Endpoints.PROJECT)
    except (NoAccessError, NotShareableError) as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_ALLOWED)
    except ProjectNotFoundError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_FOUND)

    error_method_not_allowed = 'Method not allowed!'
    _log_project_request(level=LogLevel.INFO)

    if request.method == HttpMethods.GET:
        return _get_project_name(scheduler)

    if request.method == HttpMethods.DELETE:
        return _delete_project(scheduler)

    _log_project_request(LogLevel.CRITICAL, error_method_not_allowed)
    raise ValueError(f'Critical error: {error_method_not_allowed}]')


@BP_PROJECT.route('/user/<string:user_id>', methods=[HttpMethods.PUT, HttpMethods.DELETE])
def project_named_user(user_id):
    '''
    Launcher for project with named user action

    PUT: add user with identifier user_id to project with specified permissions
    '''
    try:
        scheduler = setup_scheduler(Endpoints.PROJECT)
    except (NoAccessError, NotShareableError) as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_ALLOWED)
    except ProjectNotFoundError as err:
        _log_project_request(LogLevel.ERROR, err)
        return http_response(ReturnCodes.NOT_FOUND)

    _log_project_request(level=LogLevel.INFO)

    if not (request.method == HttpMethods.PUT or request.method == HttpMethods.DELETE):
        error_method_not_allowed = 'method not allowed!'
        _log_project_request(LogLevel.CRITICAL, error_method_not_allowed)
        raise ValueError(f'Critical error: {error_method_not_allowed}]')

    # Check if any required arguments are missing in PUT request
    required_arg = 'project_permissions'
    if request.method == HttpMethods.PUT and required_arg not in request.args:
        _log_project_request(
            LogLevel.ERROR, f'Missing argument in request: {required_arg}.')
        return http_response(ReturnCodes.BAD_ARGS)

    if request.method == HttpMethods.DELETE:
        _log_project_request(LogLevel.INFO,
                             f'Unshare project with user {user_id}')

        return _undo_share_project(scheduler, user_id)

    # Save request arguments to variables
    project_permissions = request.args.get('project_permissions')

    _log_project_request(LogLevel.INFO,
                         f'Share project with user {user_id}, permissions {project_permissions} ')

    return _share_project(scheduler, user_id, project_permissions)
