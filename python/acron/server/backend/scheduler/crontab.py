#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Implementation of the Crontab backend client'''

from acron.exceptions import CrontabError
from acron.server.utils import dump_args
from . import Scheduler

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'


# pylint: disable=W0613
class Crontab(Scheduler):
    '''
    Implements a scheduler based on the native Linux Crontab.
    '''

    @staticmethod
    @dump_args
    def backend_status(config):
        '''
        Request the status of the backend

        :param config:        a dictionary containing all the config values
        :raises CrontabError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        raise CrontabError

    @staticmethod
    @dump_args
    def create_project(project_id, config):
        '''
        Create a new project.

        :param project_id:    identifier of the project
        :param config:        a dictionary containing all the config values
        :raises CrontabError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        raise CrontabError

    @staticmethod
    @dump_args
    def get_project(project_id, config):
        '''
        Get a project's definition.

        :param project_id:    identifier of the project
        :param config:        a dictionary containing all the config values
        :raises CrontabError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        raise CrontabError

    @staticmethod
    @dump_args
    def delete_project(project_id, config):
        '''
        Delete a project.

        :param project_id:    identifier of the project
        :param config:        a dictionary containing all the config values
        :raises CrontabError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        raise CrontabError

    @staticmethod
    @dump_args
    def get_projects(config):
        '''
        Get the definition of all projects.

        :param config:        a dictionary containing all the config values
        :raises CrontabError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        raise CrontabError

    @staticmethod
    @dump_args
    def delete_projects(config):
        '''
        Delete all projects.

        :param config:        a dictionary containing all the config values
        :raises CrontabError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        raise CrontabError

    @dump_args
    def create_job(self, schedule, target, command, description):
        '''
        Create a new job.

        :param schedule:      the schedule of the new job, crontab format
        :param target:        the node on which the job will be executed, FQDN
        :param command:       the command to launch on the target at the given schedule
        :param description:   an optional description of the job
        :raises CrontabError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        raise CrontabError

#pylint: disable=R0913
    @dump_args
    def update_job(self, job_id, schedule, target, command, description):
        '''
        Update an existing job.

        :param job_id:            the unique job identifier corresponding to the job to update
        :param schedule:          the schedule of the new job, crontab format
        :param target:            the node on which the job will be executed, FQDN
        :param command:           the command to launch on the target at the given schedule
        :param description:       an optional description of the job
        :raises JobNotFoundError: if the job doesn't exist
        :raises CrontabError:     on unexpected backend error
        :returns:                 a dictionary containing the backend's response
        '''
        raise CrontabError

    @dump_args
    def modify_job_meta(self, job_id, meta):
        '''
        Modify the meta of a job, like the description or if it is active.

        :param job_id:                the unique job identifier corresponding to the job to update
        :param meta:                  the dictionary of user inputs
        :raises JobNotFoundError:     if the job doesn't exist
        :raises ProjectNotFoundError: if the project doesn't exist
        :raises CrontabError:         on unexpected backend error
        :returns:                     a dictionary containing the backend's response
        '''
        raise CrontabError

    @dump_args
    def get_job(self, job_id):
        '''
        Get a job definition.

        :param job_id:                the unique job identifier corresponding to the job to update
        :raises JobNotFoundError:     if the job doesn't exist
        :raises ProjectNotFoundError: if the project doesn't exist
        :raises CrontabError:         on unexpected backend error
        :returns:                     a dictionary containing the backend's response
        '''
        raise CrontabError

    @dump_args
    def delete_job(self, job_id):
        '''
        Delete a job.

        :param job_id:            the unique job identifier corresponding to the job to update
        :raises JobNotFoundError: if the job doesn't exist
        :raises CrontabError:     on unexpected backend error
        :returns:                 a dictionary containing the backend's response
        '''
        raise CrontabError

    @dump_args
    def get_jobs(self):
        '''
        Get all job definitions in the current project.

        :raises ProjectNotFoundError: if the project doesn't exist
        :raises CrontabError:         on unexpected backend error
        :returns:                     a dictionary containing the backend's response
        '''
        raise CrontabError

    @dump_args
    def modify_all_jobs_meta(self, meta):
        '''
        Modify meta of all jobs in a project, like if the jobs are active.

        :param meta:                  the dictionary of user inputs
        :raises ProjectNotFoundError: if the project doesn't exist
        :raises CrontabError:         on unexpected backend error
        :returns:                     a dictionary containing the backend's response
        '''
        raise CrontabError

    @dump_args
    def delete_jobs(self):
        '''
        Delete all jobs in the current project.

        :raises ProjectNotFoundError: if the project doesn't exist
        :raises CrontabError:         on unexpected backend error
        :returns:                     a dictionary containing the backend's response
        '''
        raise CrontabError

    @dump_args
    def is_shareable(self):
        '''
        Get the shareable status of the current project.

        :raises ProjectNotFoundError: if the project doesn't exist
        :returns:                     a boolean
        '''
        return False
