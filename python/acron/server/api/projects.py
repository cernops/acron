#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Projects management submodule'''

from flask import Blueprint, jsonify, request
from flask_login import login_required
from acron.server.utils import dump_args
from acron.server.constants import HttpMethods
from acron.server.http import http_response
from acron.server.log import Logger, LogLevel
from acron.exceptions import (NoAccessError, NotFoundError, NotShareableError,
                              ProjectNotFoundError, SchedulerError)
from acron.constants import Endpoints, ReturnCodes
from .utils import setup_scheduler

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)',
               'Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


# Blueprint storing all routes and function calls
BP_PROJECTS = Blueprint('projects', __name__)


def _log_projects_request(level=LogLevel.INFO, msg=''):
    '''
    Log requests to projects endpoint

    :param level: severity level, see LogLevel.
    :param msg: message to log
    '''
    Logger.log_request(Endpoints.PROJECTS, level, msg)


@dump_args
def _get_all_projects(scheduler):
    '''
    Request from the backend a list of all the projects.

    :param scheduler: the scheduler backend
    :returns:         the backend's response
    '''
    try:
        response = scheduler.get_projects(request.remote_user)
    except NotFoundError as error:
        _log_projects_request(LogLevel.WARNING, error)
        return http_response(ReturnCodes.NOT_FOUND)
    except SchedulerError as error:
        _log_projects_request(LogLevel.ERROR, error)
        return http_response(ReturnCodes.BACKEND_ERROR)
    return jsonify(response)


@BP_PROJECTS.route('/', methods=[HttpMethods.GET])
@login_required
def projects():
    '''
    Launcher for unnamed projects actions
    GET: get the list of all projects
    '''
    try:
        scheduler = setup_scheduler(Endpoints.PROJECTS)
    except (NoAccessError, NotShareableError):
        return http_response(ReturnCodes.NOT_ALLOWED)
    except ProjectNotFoundError:
        return http_response(ReturnCodes.NOT_FOUND)

    error_method_not_allowed = 'Method not allowed!'

    _log_projects_request(LogLevel.INFO)

    if request.method == HttpMethods.GET:
        return _get_all_projects(scheduler)

    _log_projects_request(LogLevel.CRITICAL, error_method_not_allowed)
    raise ValueError(f'Critical error: {error_method_not_allowed}')
