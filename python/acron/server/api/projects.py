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

import logging
from flask import Blueprint, current_app, request
from flask_login import login_required
from acron.server.utils import default_log_line_request, dump_args
from .jobs import get_scheduler_class

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'


# Blueprint storing all routes and function calls
BP_PROJECTS = Blueprint('projects', __name__)


@dump_args
def create_project(scheduler):
    '''
    Forward a new user creation request to the backend.

    :param scheduler: the scheduler backend
    :returns:         the backend's response
    '''
    return scheduler.create_project()


@dump_args
def get_project(scheduler):
    '''
    Request from the backend the information about the current project.

    :param scheduler: the scheduler backend
    :returns:         the backend's response
    '''
    return scheduler.get_project()


@dump_args
def delete_project(scheduler):
    '''
    Request from the backend the deletion of the current project.

    :param scheduler: the scheduler backend
    :returns:         the backend's response
    '''
    return scheduler.delete_project()


@dump_args
def get_all_projects(scheduler):
    '''
    Request from the backend a list of all the projects.

    :param scheduler: the scheduler backend
    :returns:         the backend's response
    '''
    return scheduler.get_projects()


@dump_args
def delete_all_projects(scheduler):
    '''
    Request from the backend the deletion of all projects.

    :param scheduler: the scheduler backend
    :returns:         the backend's response
    '''
    return scheduler.delete_projects()


@BP_PROJECTS.route('/', methods=['GET', 'DELETE'])
@login_required
def projects():
    '''
    Launcher for unnamed projects actions
    GET: get the list of all projects
    DELETE: delete all the projects
    '''
    scheduler_class = get_scheduler_class()
    scheduler = scheduler_class(request.remote_user, current_app.config)
    logging.info('%s on /projects/.', default_log_line_request())

    if request.method == 'GET':
        return get_all_projects(scheduler)

    if request.method == 'DELETE':
        return delete_all_projects(scheduler)

    logging.critical('%s on /projects/: Method not allowed!', default_log_line_request())
    raise ValueError('Critical error: method not allowed!')


@BP_PROJECTS.route('/<string:project_id>', methods=['PUT', 'GET', 'DELETE'])
@login_required
def named_projects(project_id):
    '''
    Launcher for named projects actions
    PUT: create the project project_id if it doesn't already exist
    GET: get the details the project project_id
    DELETE: delete the project project_id
    '''
    scheduler_class = get_scheduler_class()
    scheduler = scheduler_class(project_id, current_app.config)
    logging.info('%s on /projects/%s.', default_log_line_request(), project_id)

    if request.method == 'PUT':
        return create_project(scheduler)

    if request.method == 'GET':
        return get_project(scheduler)

    if request.method == 'DELETE':
        return delete_project(scheduler)

    logging.critical('%s on /projects/%s: Method not allowed!', default_log_line_request(), project_id)
    raise ValueError('Critical error: method not allowed!')
