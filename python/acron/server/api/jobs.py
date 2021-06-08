#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Job management submodule'''

import logging
from flask import Blueprint, current_app, jsonify, request
from flask_login import login_required
from acron.errors import ERRORS
from acron.utils import check_schedule, check_target, check_command, check_description
from acron.server.http import http_response
from acron.exceptions import (NoAccessError, NotFoundError, NotShareableError,
                              ProjectNotFoundError, SchedulerError)
from acron.server.utils import (
    default_log_line_request, dump_args,
    get_remote_hostname, ldap_groups_expansion)

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)', 'Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


# Blueprint storing all routes and function calls
BP_JOBS = Blueprint('jobs', __name__)


@dump_args
def create_job(scheduler=None, schedule=None, target=None, command=None, description=None):
    '''
    Forward a new job creation request to the backend.

    :param scheduler:   the scheduler backend
    :param schedule:    the schedule of the new job, crontab format
    :param target:      the node on which the job will be executed, FQDN
    :param command:     the command to launch on the target at the given schedul
    :param description: an optional description of the job
    :returns:           an HTTP payload
    '''
    try:
        if schedule is not None:
            check_schedule(schedule)
        if target is not None:
            check_target(target)
        if command is not None:
            check_command(command)
        if description is None:
            description = 'No description given'
        else:
            check_description(description)
        response = scheduler.create_job(schedule, target, command, description)
    except SchedulerError as error:
        logging.error('%s on /jobs/: %s', default_log_line_request(), error)
        return http_response(ERRORS['BACKEND_ERROR'])
    except AssertionError as error:
        logging.error('%s on /jobs/: %s', default_log_line_request(), error)
        return http_response(ERRORS['USER_ERROR'])
    except TypeError as error:
        logging.error('%s on /jobs/: %s', default_log_line_request(), error)
        return http_response(ERRORS['BACKEND_ERROR'])
    return jsonify(response)


@dump_args
def modify_all_jobs_meta(scheduler, meta):
    '''
    Forward a meta modification to all jobs request to the backend.

    :param scheduler: the scheduler backend
    :param meta:      the dictionary of user inputs
    :returns:         an HTTP payload
    '''
    try:
        response = scheduler.modify_all_jobs_meta(meta)
    except SchedulerError as error:
        logging.error('%s on /jobs/: %s', default_log_line_request(), error)
        return http_response(ERRORS['BACKEND_ERROR'])
    return jsonify(response)


@dump_args
def get_all_jobs(scheduler):
    '''
    Requests from the backend a list of all jobs from the current project.

    :param scheduler: the scheduler backend
    :returns:         an HTTP payload
    '''
    try:
        response = scheduler.get_jobs()
    except NotFoundError as error:
        logging.warning('%s on /jobs/: %s', default_log_line_request(), error)
        return http_response(ERRORS['NOT_FOUND'])
    except SchedulerError as error:
        logging.error('%s on /jobs/: %s', default_log_line_request(), error)
        return http_response(ERRORS['BACKEND_ERROR'])
    return jsonify(response)


@dump_args
def delete_all_jobs(scheduler):
    '''
    Requests from the backend to delete all the jobs in the project.

    :param scheduler: the scheduler backend
    :returns:         an HTTP payload
    '''
    try:
        response = scheduler.delete_jobs()
    except NotFoundError as error:
        logging.warning('%s on /jobs/: %s', default_log_line_request(), error)
        return http_response(ERRORS['NOT_FOUND'])
    except SchedulerError as error:
        logging.error('%s on /jobs/: %s', default_log_line_request(), error)
        return http_response(ERRORS['BACKEND_ERROR'])
    return jsonify(response)


#pylint: disable=R0913
@dump_args
def update_job(scheduler, job_id, schedule, target, command, description):
    '''
    Forward a job update request to the backend.

    :param scheduler:   the scheduler backend
    :param job_id:      the unique job identifier corresponding to the job to update
    :param schedule:    the schedule of the job, crontab format
    :param target:      the node on which job will be executed, FQDN
    :param command:     the command to launch on the target at the given schedule
    :param description: an optional description of the job
    :returns:         an HTTP payload
    '''
    try:
        if schedule is not None:
            check_schedule(schedule)
        response = scheduler.update_job(job_id, schedule, target, command, description)
    except AssertionError as error:
        logging.error('%s on /jobs/: %s', default_log_line_request(), error)
        return http_response(ERRORS['USER_ERROR'])
    except NotFoundError:
        logging.warning('%s on /jobs/: Job %s does not exist.', default_log_line_request(), job_id)
        return http_response(ERRORS['NOT_FOUND'])
    except SchedulerError as error:
        logging.error('%s on /jobs/%s: %s', default_log_line_request(), job_id, error)
        return http_response(ERRORS['BACKEND_ERROR'])
    return jsonify(response)


@dump_args
def modify_job_meta(scheduler, job_id, meta):
    '''
    Forward a job meta modification request to the backend.

    :param scheduler: the scheduler backend
    :param job_id:    the unique job identifier corresponding to the job to update
    :param meta:      the dictionary of user inputs
    :returns:         an HTTP payload
    '''
    try:
        response = scheduler.modify_job_meta(job_id, meta)
    except NotFoundError as error:
        logging.warning('%s on /jobs/: %s', default_log_line_request(), error)
        return http_response(ERRORS['NOT_FOUND'])
    except SchedulerError as error:
        logging.error('%s on /jobs/%s: %s', default_log_line_request(), job_id, error)
        return http_response(ERRORS['BACKEND_ERROR'])
    return jsonify(response)


@dump_args
def get_job(scheduler, job_id):
    '''
    Request from the backend the definition of a job.

    :param scheduler: the scheduler backend
    :param job_id:    the unique job identifier corresponding to the job definition requested
    :returns:         an HTTP payload
    '''
    try:
        response = scheduler.get_job(job_id)
    except NotFoundError as error:
        logging.warning('%s on /jobs/: %s', default_log_line_request(), error)
        return http_response(ERRORS['NOT_FOUND'])
    except SchedulerError as error:
        logging.error('%s on /jobs/%s: %s', default_log_line_request(), job_id, error)
        return http_response(ERRORS['BACKEND_ERROR'])
    return jsonify(response)


@dump_args
def delete_job(scheduler, job_id):
    '''
    Request from the backend the deletion of a job.

    :param scheduler: the scheduler backend
    :param job_id:    the unique job identifier corresponding to the job to delete
    :returns:         an HTTP payload
    '''
    try:
        response = scheduler.delete_job(job_id)
    except NotFoundError as error:
        logging.warning('%s on /jobs/: %s', default_log_line_request(), error)
        return http_response(ERRORS['NOT_FOUND'])
    except SchedulerError as error:
        logging.error('%s on /jobs/%s: %s', default_log_line_request(), job_id, error)
        return http_response(ERRORS['BACKEND_ERROR'])
    return jsonify(response)


@dump_args
def get_scheduler_class():
    '''
    Check the config and returns the corresponding scheduler class.

    :raises ValueError: if the scheduler in the config is not a supported one
    :returns:           the scheduler class
    '''
    if current_app.config['SCHEDULER']['TYPE'] == 'Rundeck':
        from acron.server.backend.scheduler.rundeck import Rundeck
        scheduler_class = Rundeck
    elif current_app.config['SCHEDULER']['TYPE'] == 'Nomad':
        from acron.server.backend.scheduler.nomad import Nomad
        scheduler_class = Nomad
    elif current_app.config['SCHEDULER']['TYPE'] == 'Crontab':
        from acron.server.backend.scheduler.crontab import Crontab
        scheduler_class = Crontab
    else:
        logging.warning('User %s (%s) requests %s scheduler backend: backend not implemented.',
                        request.remote_user, get_remote_hostname(),
                        current_app.config['SCHEDULER']['TYPE'])
        raise ValueError('Only scheduler backends currently supported are: Rundeck, Nomad and Crontab')

    return scheduler_class


@dump_args
def check_shared_project_access(user, project, scheduler_class):
    '''
    Performs an ACL lookup to dertermine is a particular user can access a shared project.

    :raises NoAccessError:    if the user is not authorized
    :raises NotShareableError: if the project is not shareable
    :returns:                 a Scheduler object initialized with the shared project
    '''
    scheduler = scheduler_class(project, current_app.config)
    if scheduler.is_shareable():
        users_with_access_to_project = ldap_groups_expansion(
            'acron-' + project)
        if user not in users_with_access_to_project:
            logging.warning('%s on /jobs/: project %s is shareable, but user %s not in e-group members %s.',
                            default_log_line_request(), project, user, users_with_access_to_project)
            raise NoAccessError
    else:
        logging.warning('%s on /jobs/: project %s is not shareable.',
                        default_log_line_request(), project)
        raise NotShareableError
    return scheduler


@dump_args
def setup_scheduler():
    '''
    Instantiate the Scheduler class based on the config.

    :returns: a Scheduler instance
    '''
    scheduler_class = get_scheduler_class()
    if 'project' in request.args and request.args.get('project') != request.remote_user:
        scheduler = check_shared_project_access(
            request.remote_user,
            request.args.get('project'),
            scheduler_class)
    else:
        scheduler = scheduler_class(request.remote_user, current_app.config)

    return scheduler


#pylint: disable=R0911
@BP_JOBS.route('/', methods=['GET', 'POST', 'PATCH', 'DELETE'])
@login_required
def jobs():
    '''
    Launcher for unnamed jobs actions
    POST: create a new job, job id will be automatically generated
    GET: get the list of all jobs in the project
    DELETE: delete all the jobs in the project
    '''
    try:
        scheduler = setup_scheduler()
    except (NoAccessError, NotShareableError):
        return http_response(ERRORS['NOT_ALLOWED'])
    except ProjectNotFoundError:
        return http_response(ERRORS['NOT_FOUND'])

    logging.info('%s on /jobs/.', default_log_line_request())

    if request.method == 'POST':
        if 'schedule' not in request.args or \
           'target' not in request.args or \
           'command' not in request.args:
            logging.warning('%s on /jobs/: Missing arguments.', default_log_line_request())
            logging.debug('%s on /jobs/: schedule: "%s", target: "%s", command: "%s"',
                          default_log_line_request(), str(request.args.get('schedule')),
                          str(request.args.get('target')), str(request.args.get('command')))
            return http_response(ERRORS['BAD_ARGS'])

        schedule = request.args.get('schedule')
        target = request.args.get('target')
        command = request.args.get('command')
        description = request.args.get('description')

        logging.info('schedule: %s, target: %s, command: %s, description: %s',
                     schedule, target, command, description)

        return create_job(scheduler, schedule, target, command, description)

    if request.method == 'PATCH':
        return modify_all_jobs_meta(scheduler, request.args)

    if request.method == 'GET':
        return get_all_jobs(scheduler)

    if request.method == 'DELETE':
        return delete_all_jobs(scheduler)

    logging.critical('%s on /jobs/: Method not allowed!', default_log_line_request())
    raise ValueError('Critical error: method not allowed!')


#pylint: disable=R0911
@BP_JOBS.route('/<string:job_id>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
@login_required
def named_job(job_id):
    '''
    Launcher for named jobs actions
    PUT: update the job identified by job-id
    GET: get the details of the job identified by job-id
    DELETE: delete the job identified by job-id
    '''
    if job_id == '' or len(job_id) > current_app.config['JOB_ID_MAX_LENGTH']:
        logging.warning('%s on /jobs/%s: job_id empty or too long.',
                        default_log_line_request(), job_id)
        return http_response(ERRORS['BAD_ARGS'])
    try:
        scheduler = setup_scheduler()
    except (NoAccessError, NotShareableError):
        return http_response(ERRORS['NOT_ALLOWED'])
    except ProjectNotFoundError:
        return http_response(ERRORS['NOT_FOUND'])

    logging.info('%s on /jobs/%s.', default_log_line_request(), job_id)

    if request.method == 'PUT':
        if not 'schedule' in request.args and \
           not 'target' in request.args and \
           not 'command' in request.args and \
           not 'description' in request.args:
            logging.warning('%s on /jobs/%s: Missing arguments.', default_log_line_request(), job_id)
            logging.debug('%s on /jobs/: schedule: %s, target: %s, command: %s, description: %s',
                          default_log_line_request(), str(request.args.get('schedule')),
                          str(request.args.get('target')), str(request.args.get('command')),
                          str(request.args.get('description')))
            return http_response(ERRORS['BAD_ARGS'])

        schedule = request.args.get('schedule')
        target = request.args.get('target')
        command = request.args.get('command')
        description = request.args.get('description')

        logging.info('schedule: %s, target: %s, command: %s, description: %s',
                     schedule, target, command, description)

        return update_job(scheduler, job_id, schedule, target, command, description)

    if request.method == 'PATCH':
        return modify_job_meta(scheduler, job_id, request.args)

    if request.method == 'GET':
        return get_job(scheduler, job_id)

    if request.method == 'DELETE':
        return delete_job(scheduler, job_id)

    logging.critical('%s on /jobs/%s: Method not allowed!', default_log_line_request(), job_id)
    raise ValueError('Critical error: method not allowed!')
