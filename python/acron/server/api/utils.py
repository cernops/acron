#
# (C) Copyright 2021 CERN
#
# This software is distributed under the terms of the GNU General Public Licence version 3
# (GPL Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Shared methods between API modules'''

__author__ = 'Rodrigo Bermudez Schettino (CERN)'
__credits__ = ['Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'

import logging
from flask import current_app, request
from acron.server.log import Logger, LogLevel
from acron.server.utils import (dump_args, get_remote_hostname)
from acron.exceptions import NotShareableError


@dump_args
def _check_shared_project_access(endpoint, user, project, scheduler_class):
    '''
    Performs an ACL lookup to determine if a particular user can access a shared project.

    :raises NoAccessError:        if the user is not authorized
    :raises NotShareableError:    if the project is not shareable
    :raises ProjectNotFoundError: if the project is not found
    :returns:                     a Scheduler object initialized with the shared project
    '''
    scheduler = scheduler_class(project, current_app.config)
    if not scheduler.is_shareable(user):
        msg = f'project {project} is not shareable.'
        Logger.log_request(endpoint, LogLevel.WARNING, msg)
        raise NotShareableError
    return scheduler


@dump_args
def get_scheduler_class():
    '''
    Check the config and returns the corresponding scheduler class.

    :raises ValueError: if the scheduler in the config is not a supported one
    :returns:           the scheduler class
    '''
    if current_app.config['SCHEDULER']['TYPE'] == 'Rundeck':
        from acron.server.backend.scheduler.rundeck import Rundeck
        return Rundeck
    elif current_app.config['SCHEDULER']['TYPE'] == 'Nomad':
        from acron.server.backend.scheduler.nomad import Nomad
        return Nomad
    elif current_app.config['SCHEDULER']['TYPE'] == 'Crontab':
        from acron.server.backend.scheduler.crontab import Crontab
        return Crontab

    logging.warning('User %s (%s) requests %s scheduler backend: backend not implemented.',
                    request.remote_user, get_remote_hostname(),
                    current_app.config['SCHEDULER']['TYPE'])
    raise ValueError(
        'Only scheduler backends currently supported are: Rundeck, Nomad and Crontab')


@dump_args
def setup_scheduler(endpoint):
    '''
    Instantiate the Scheduler class based on the config.

    :returns: a Scheduler instance
    '''
    scheduler_class = get_scheduler_class()

    if 'project' in request.args and request.args.get('project') != request.remote_user:
        return _check_shared_project_access(endpoint=endpoint,
                                            user=request.remote_user,
                                            project=request.args.get(
                                                'project'),
                                            scheduler_class=scheduler_class)

    return scheduler_class(request.remote_user, current_app.config)
