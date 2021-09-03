#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Scheduler interface class'''

from abc import ABC, abstractmethod
import logging
from acron.server.utils import dump_args, get_remote_hostname

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)',
               'Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


class Scheduler(ABC):
    '''
    Base scheduler class. Acts as interface for the different scheduler backends.
    '''
    @dump_args
    def __init__(self, project_id, config):
        '''
        Constructor

        :param project_id: identifier of the project to manage
        :param config:     a dictionary containing all the config values
        '''
        self.project_id = project_id
        self.config = config

    @staticmethod
    @abstractmethod
    def backend_status(config):
        '''
        Request the status of the backend

        :param config:          a dictionary containing all the config values
        :raises SchedulerError: on unexpected backend error
        :returns:               a dictionary containing the backend's response
        '''

    @abstractmethod
    def get_project_name(self):
        '''
        Get a project's name.

        :returns: a dictionary containing the backend's response
        '''

    @abstractmethod
    def get_project_users(self):
        '''
        Get a project's users.

        :raises ProjectNotFoundError: if the project doesn't exist
        :raises SchedulerError:       on unexpected backend error
        :returns:                     a dictionary containing the backend's response
        '''

    @abstractmethod
    def share_project(self, userm, perms):
        '''
        Share project with another user.

        :param user:                  username
        :param perms:                 project permissions
        :raises ProjectNotFoundError: if the project doesn't exist
        :raises UserNotFoundError:    if the user doesn't exist
        :returns:                     a dictionary containing the backend's response
        '''

    @staticmethod
    @abstractmethod
    def delete_project(project_id, config):
        '''
        Delete a project.

        :param project_id:      identifier of the project
        :param config:          a dictionary containing all the config values
        :raises SchedulerError: on unexpected backend error
        :returns:               a dictionary containing the backend's response
        '''

    @abstractmethod
    def get_projects(self, user):
        '''
        Get the definition of all projects.

        :param user:            name of the user
        :raises SchedulerError: on unexpected backend error
        :returns:               a dictionary containing the backend's response
        '''

    # pylint: disable=too-many-arguments
    @abstractmethod
    def create_job(self, job_id, schedule, target, command, description):
        '''
        Create a new job.

        :param job_id:          the unique job identifier corresponding to the job to create
        :param schedule:        the schedule of the new job, crontab format
        :param target:          the node on which the job will be executed, FQDN
        :param command:         the command to launch on the target at the given schedule
        :param description:     an optional description of the job
        :raises ArgsMalformedError: on wrong job_id
        :raises SchedulerError: on unexpected backend error
        :returns:               a dictionary containing the backend's response
        '''

    #pylint: disable=R0913
    @abstractmethod
    def update_job(self, job_id, schedule, target, command, description):
        '''
        Update an existing job.

        :param job_id:            the unique job identifier corresponding to the job to update
        :param schedule:          the schedule of the new job, crontab format
        :param target:            the node on which the job will be executed, FQDN
        :param command:           the command to launch on the target at the given schedule
        :param description:       an optional description of the job
        :raises JobNotFoundError: if the job doesn't exist
        :raises SchedulerError:   on unexpected backend error
        :returns:                 a dictionary containing the backend's response
        '''

    @abstractmethod
    def modify_job_meta(self, job_id, meta):
        '''
        Modify the meta of a job, like the description or if it is active.

        :param job_id:                the unique job identifier corresponding to the job to update
        :param meta:                  the dictionary of user inputs
        :raises JobNotFoundError:     if the job doesn't exist
        :raises ProjectNotFoundError: if the project doesn't exist
        :raises SchedulerError:       on unexpected backend error
        :returns:                     a dictionary containing the backend's response
        '''

    @abstractmethod
    def get_job(self, job_id):
        '''
        Get a job definition.

        :param job_id:                the unique job identifier corresponding to the job to update
        :raises JobNotFoundError:     if the job doesn't exist
        :raises ProjectNotFoundError: if the project doesn't exist
        :raises SchedulerError:       on unexpected backend error
        :returns:                     a dictionary containing the backend's response
        '''

    @abstractmethod
    def delete_job(self, job_id):
        '''
        Delete a job.

        :param job_id:            the unique job identifier corresponding to the job to update
        :raises JobNotFoundError: if the job doesn't exist
        :raises SchedulerError:   on unexpected backend error
        :returns:                 a dictionary containing the backend's response
        '''

    @abstractmethod
    def get_jobs(self):
        '''
        Get all job definitions in the current project.

        :raises ProjectNotFoundError: if the project doesn't exist
        :raises SchedulerError:       on unexpected backend error
        :returns:                     a dictionary containing the backend's response
        '''

    @abstractmethod
    def modify_all_jobs_meta(self, meta):
        '''
        Modify meta of all jobs in a project, like if the jobs are active.

        :param meta:                  the dictionary of user inputs
        :raises ProjectNotFoundError: if the project doesn't exist
        :raises SchedulerError:       on unexpected backend error
        :returns:                     a dictionary containing the backend's response
        '''

    @abstractmethod
    def delete_jobs(self):
        '''
        Delete all jobs in the current project.

        :raises ProjectNotFoundError: if the project doesn't exist
        :raises SchedulerError:       on unexpected backend error
        :returns:                     a dictionary containing the backend's response
        '''

    @abstractmethod
    def is_shareable(self, user):
        '''
        Get the shareable status of the current project.

        :param user: check if project is shared with user given
        :raises ProjectNotFoundError: if the project doesn't exist
        :returns:                     a boolean
        '''
