#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Implementation of the Rundeck backend client'''

import logging
import os
from random import randint
import re
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
import requests
import yaml
from acron.exceptions import JobNotFoundError, ProjectNotFoundError, RundeckError
from acron.utils import replace_in_file
from acron.server.utils import dump_args, fqdnify, create_parent
from . import Scheduler

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'

def _cron2quartz(schedule):
    fields = re.split(r'\s+', schedule)
    if fields[2] == '*':
        if fields[4] == '*':
            # flaw: if both all monthdays and all weekdays are specified, weekday should be?
            fields[4] = '?'
        else:
            if fields[4] != '?':
                fields[2] = '?'

    # we fix the year to be '*' and the second to be random between 10s
    return ' '.join([str(randint(0, 10))] + fields + ['*'])

class Rundeck(Scheduler):
    '''
    Implements a scheduler based on Rundeck open source software.
    '''
    @dump_args
    def __init__(self, project_id, config):
        '''
        Constructor.

        :param project_id: the name of the project to take actions on
        :param config:     the configuration dictionary
        '''
        super().__init__(project_id, config)
        Rundeck._config(config)

    @staticmethod
    @dump_args
    def _config(config):
        '''
        Configures the API for Rundeck backend

        :param config:        a dictionary containing all the config values
        :raises RundeckError: on unexpected backend error
        '''
        os.environ['RD_CONF'] = config['SCHEDULER']['RD_CLI_CONF']

    @staticmethod
    @dump_args
    def backend_status(config):
        '''
        Request the status of the backend

        :param config:        a dictionary containing all the config values
        :raises RundeckError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        Rundeck._config(config)
        line_to_execute = 'rd system info'
        logging.debug('Popen: %s', line_to_execute)
        process = Popen([line_to_execute], universal_newlines=True,
                        stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate()
        if process.returncode != 0:
            logging.debug(err)
            raise RundeckError(err)
        return yaml.safe_load(out)

    @staticmethod
    @dump_args
    def create_project(project_id, config):
        '''
        Create a new project.

        :param project_id:    identifier of the project
        :param config:        a dictionary containing all the config values
        :raises RundeckError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        Rundeck._config(config)
        with NamedTemporaryFile() as properties:
            replace_in_file('__USERNAME__', project_id,
                            config['SCHEDULER']['PROJECT_PROPERTIES_SOURCE'], properties.name)
            replace_in_file('__PROJECTS_HOME__', config['SCHEDULER']['PROJECTS_HOME'],
                            properties.name)
            line_to_execute = 'rd projects create'
            line_to_execute += ' --project ' + project_id
            line_to_execute += ' --file ' + properties.name
            logging.debug('Popen: %s', line_to_execute)
            process = Popen([line_to_execute], universal_newlines=True,
                            stdout=PIPE, stderr=PIPE, shell=True)
            out, err = process.communicate()
            logging.debug(out.rstrip('\n'))
            if process.returncode != 0:
                logging.debug(err)
                raise RundeckError(err)
        with NamedTemporaryFile() as acls:
            replace_in_file('__USERNAME__', project_id,
                            config['SCHEDULER']['PROJECT_ACLS_SOURCE'], acls.name)
            line_to_execute = 'rd projects acls create'
            line_to_execute += ' --project ' + project_id
            line_to_execute += ' --file ' + acls.name
            line_to_execute += ' --name ' + project_id + '.aclpolicy'
            logging.debug('Popen: %s', line_to_execute)
            process = Popen([line_to_execute], universal_newlines=True,
                            stdout=PIPE, stderr=PIPE, shell=True)
            out, err = process.communicate()
            logging.debug(out.rstrip('\n'))
            if process.returncode != 0:
                logging.debug(err)
                raise RundeckError(err)
        with NamedTemporaryFile() as system_acls:
            replace_in_file('__USERNAME__', project_id,
                            config['SCHEDULER']['SYSTEM_ACLS_SOURCE'], system_acls.name)
            line_to_execute = 'rd system acls create'
            line_to_execute += ' --file ' + system_acls.name
            line_to_execute += ' --name ' + project_id + '.aclpolicy'
            logging.debug('Popen: %s', line_to_execute)
            process = Popen([line_to_execute], universal_newlines=True,
                            stdout=PIPE, stderr=PIPE, shell=True)
            out, err = process.communicate()
            logging.debug(out.rstrip('\n'))
            if process.returncode != 0:
                logging.debug(err)
                raise RundeckError(err)

    @staticmethod
    @dump_args
    def get_project(project_id, config):
        '''
        Get a project's definition.

        :param project_id:    identifier of the project
        :param config:        a dictionary containing all the config values
        :raises RundeckError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        Rundeck._config(config)
        raise RundeckError

    @staticmethod
    @dump_args
    def delete_project(project_id, config):
        '''
        Delete a project.

        :param project_id:            identifier of the project
        :param config:                a dictionary containing all the config values
        :raises ProjectNotFoundError: if the project does not exist
        :raises RundeckError:         on unexpected backend error
        :returns:                     a dictionary containing the backend's response
        '''
        Rundeck._config(config)
        line_to_execute = 'rd projects delete'
        line_to_execute += ' --confirm'
        line_to_execute += ' --project ' + project_id
        logging.debug('Popen: %s', line_to_execute)
        process = Popen([line_to_execute], universal_newlines=True, stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate()
        logging.debug(out.rstrip('\n'))
        if process.returncode == 2:
            logging.warning('Rundeck: admin tries to delete non existing project %s.', project_id)
            logging.debug(err)
            raise ProjectNotFoundError(err)
        if process.returncode != 0:
            logging.debug(err)
            raise RundeckError(err)
        payload = {
            'message': 'successfully deleted',
            'name': project_id
        }
        return payload

    @staticmethod
    @dump_args
    def get_projects(config):
        '''
        Get the definition of all projects.

        :param config:        a dictionary containing all the config values
        :raises RundeckError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        Rundeck._config(config)
        line_to_execute = 'rd projects list'
        line_to_execute += ' --outformat %name'
        logging.debug('Popen: %s', line_to_execute)
        process = Popen([line_to_execute], universal_newlines=True, stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate()
        logging.debug(out)
        if process.returncode != 0:
            logging.debug(err)
            raise RundeckError(err)
        projects_list = out.split('\n')
        return projects_list

    @staticmethod
    @dump_args
    def delete_projects(config):
        '''
        Delete all projects.

        :param config:        a dictionary containing all the config values
        :raises RundeckError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        Rundeck._config(config)
        raise RundeckError

    @staticmethod
    @dump_args
    def _project_exists(project_id, config):
        '''
        Perform a project lookup on the backend.

        :returns: True if the project exists, False otherwise
        '''
        Rundeck._config(config)
        line_to_execute = 'rd projects info'
        line_to_execute += ' --project ' + project_id
        logging.debug('Popen: %s', line_to_execute)
        process = Popen([line_to_execute], universal_newlines=True, stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate()
        logging.debug(out.rstrip('\n'))
        if process.returncode != 0:
            logging.debug(err)
            return False
        return True

    @staticmethod
    @dump_args
    def take_over_jobs(server_uuid, config):
        '''
        Take over all the jobs from another server.

        :param server_uuid:   the UUID of the server to take the jobs from
        :param config:        a dictionary containing all the config values
        :raises RundeckError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        params = {'server': {'uuid': server_uuid}}
        headers = {
            'X-Rundeck-Auth-Token': config['SCHEDULER']['API_KEY'],
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        path = config['SCHEDULER']['API_URL'] + '/scheduler/takeover'
        response = requests.put(path, json=params, headers=headers)
        if response.status_code == 200 and hasattr(response, 'json'):
            return response.json()
        raise RundeckError('Takeover failed. ' + response.text)

    @dump_args
    def _generate_job_name(self):
        '''
        Generates a new name that does not yet exist in the project.

        :returns: a string with the new job name
        '''
        path = os.path.join(self.config['SCHEDULER']['PROJECTS_HOME'], self.project_id, 'max_job_id')
        path_parent = os.path.abspath(os.path.join(path, os.pardir))
        if not os.path.exists(path_parent):
            logging.debug('%s does not exist, creating.', path_parent)
            os.makedirs(path_parent, 0o0775)
        if not os.path.exists(path):
            logging.debug('%s does not exist, creating with value 1.', path)
            with open(path, 'w') as max_job_id_file:
                max_job_id_file.write('1')
            max_job_id = 1
        else:
            with open(path, 'r') as max_job_id_file:
                max_job_id = int(max_job_id_file.read()) + 1
            with open(path, 'w') as max_job_id_file:
                max_job_id_file.write(str(max_job_id))
        return 'job' + '{:06d}'.format(max_job_id)

    @dump_args
    def _target_is_in_project(self, target):
        '''
        Check if the target host is already in the list of targets in the project.

        :param target:        host to check
        :raises RundeckError: on unexpected Rundeck error
        :returns:             True if the host is already in the list, False otherwise
        '''
        line_to_execute = 'rd nodes'
        line_to_execute += ' --project ' + self.project_id
        line_to_execute += ' --filter ' + target
        logging.debug('Popen: %s', line_to_execute)
        process = Popen([line_to_execute], universal_newlines=True, stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate()
        logging.debug(out.rstrip('\n'))
        if process.returncode != 0:
            logging.debug(err)
            raise RundeckError(err)
        host = re.search(target, out)
        if host is None:
            return False
        return True

    @dump_args
    def _add_target_to_project(self, target):
        '''
        Add a node to the user's project.

        :param target: FQDN of the host to add
        '''
        path = os.path.join(self.config['SCHEDULER']['PROJECTS_HOME'],
                            self.project_id, 'etc', 'resources.yaml')
        create_parent(path)
        logging.debug('Adding %s to %s.', target, path)
        with open(path, 'a+') as resources:
            resources.write('\n\n' +
                            target + ':\n' +
                            '  nodename: ' + target + '\n' +
                            '  hostname: ' + target + '\n' +
                            '  username: ' + self.project_id + '\n' +
                            '  tags: ""')

#pylint: disable=R0912, R0913, R0915
    @dump_args
    def _create_update_job(self, job_id, schedule, target, command, description):
        '''
        Update or create a job.

        :param job_id:            the unique job identifier corresponding to the job to update
        :param schedule:          the schedule of the new job, Quartz format
        :param target:            the node on which the job will be executed, FQDN
        :param command:           the command to launch on the target at the given schedule
        :param description:       an optional description of the job
        :raises JobNotFoundError: if the job to update doesn't exist
        :raises RundeckError:     on unexpected Rundeck error
        :returns:                 a dictionary containing the backend's response
        '''
        if not self._project_exists(self.project_id, self.config):
            self.create_project(self.project_id, self.config)
        if job_id is None: # new job
            job_id = self._generate_job_name()
            type_message = 'created'
        else: # update existing job
            job_properties = self.get_job(job_id)
            if schedule is None:
                schedule = ' '.join(job_properties['description'].split(' ')[0:5])
            if target is None:
                target = job_properties['nodefilters']['filter'].replace('name: ', '')
            if command is None:
                command = job_properties['sequence']['commands'][0]['exec']
            if description is None:
                description = ' '.join(job_properties['description'].split(' ')[5:])
            type_message = 'updated'
        target = fqdnify(target)
        crontab = _cron2quartz(schedule)
        if not self._target_is_in_project(target):
            self._add_target_to_project(target)
        with NamedTemporaryFile() as job_file:
            if description is None or description == "":
                description = ' No description given'
            replace_in_file('__PROJECT_NAME__', self.project_id,
                            self.config['SCHEDULER']['JOB_SOURCE'], job_file.name)
            replace_in_file('__DESCRIPTION__', schedule + ' ' + description, job_file.name)
            replace_in_file('__DOMAIN__', self.config['DOMAIN'], job_file.name)
            replace_in_file('__JOB_NAME__', job_id, job_file.name)
            replace_in_file('__TARGET_HOST__', target, job_file.name)
            replace_in_file('__COMMAND__', command, job_file.name)
            replace_in_file('__CRONTAB__', crontab, job_file.name)
            line_to_execute = 'rd jobs load'
            line_to_execute += ' --project ' + self.project_id
            line_to_execute += ' --file ' + job_file.name
            line_to_execute += ' --format yaml --duplicate update'
            logging.debug('Popen: %s', line_to_execute)
            process = Popen([line_to_execute], universal_newlines=True, stdout=PIPE, stderr=PIPE, shell=True)
            out, err = process.communicate()
        logging.debug(out.rstrip('\n'))
        if process.returncode != 0:
            logging.debug(err)
            raise RundeckError(err)
        payload = {'message': 'Job successfully ' + type_message + '.'}
        payload.update(self.get_job(job_id))
        return payload

    @dump_args
    def create_job(self, schedule, target, command, description):
        '''
        Create a new job.

        :param schedule:      the schedule of the new job, crontab format
        :param target:        the node on which the job will be executed, FQDN
        :param command:       the command to launch on the target at the given schedule
        :param description:   an optional description of the job
        :raises RundeckError: on unexpected Rundeck error
        :returns:             a dictionary containing the backend's response
        '''
        return self._create_update_job(None, schedule, target, command, description)

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
        :raises JobNotFoundError: if the job to update doesn't exist
        :raises RundeckError:     on unexpected Rundeck error
        :returns:                 a dictionary containing the backend's response
        '''
        return self._create_update_job(job_id, schedule, target, command, description)

    @dump_args
    def modify_job_meta(self, job_id, meta):
        '''
        Modify the meta of a job, like the description or if it is active.

        :param job_id:                the unique job identifier corresponding to the job to update
        :param meta:                  the dictionary of user inputs
        :raises JobNotFoundError:     if the job to update doesn't exist
        :raises ProjectNotFoundError: if the project doesn't exist
        :raises RundeckError:         on unexpected Rundeck error
        :returns:                     a dictionary containing the backend's response
        '''
        payload = {'name': job_id}
        if 'enable' in meta:
            if meta.get('enable') == 'True':
                line_to_execute = 'rd jobs reschedule'
                payload['message'] = 'Job successfully enabled.'
            else:
                line_to_execute = 'rd jobs unschedule'
                payload['message'] = 'Job successfully disabled.'
            line_to_execute += ' --project ' + self.project_id
            line_to_execute += ' --job ' + job_id
            logging.debug('Popen: %s', line_to_execute)
            process = Popen([line_to_execute], universal_newlines=True,
                            stdout=PIPE, stderr=PIPE, shell=True)
            out, err = process.communicate()
            logging.debug(out.rstrip('\n'))
            if process.returncode == 2:
                project_not_found = re.match('Error: project does not exist', err)
                if project_not_found:
                    logging.warning('Rundeck: user %s tries to access non existing project.', self.project_id)
                    logging.debug(err)
                    raise ProjectNotFoundError(err)
                logging.warning('Rundeck: user %s tries to access non existing job.', self.project_id)
                logging.debug(err)
                raise JobNotFoundError(err)
            if process.returncode != 0:
                logging.debug(err)
                raise RundeckError(err)
        return payload

    @dump_args
    def get_job(self, job_id):
        '''
        Get a job definition.

        :param job_id:                the unique job identifier corresponding to the job to update
        :raises JobNotFoundError:     if the job doesn't exist
        :raises ProjectNotFoundError: if the project doesn't exist
        :raises RundeckError:         on unexpected Rundeck error
        :returns:                     a dictionary containing the backend's response
        '''
        with NamedTemporaryFile() as job_file:
            line_to_execute = 'rd jobs list'
            line_to_execute += ' --project ' + self.project_id
            line_to_execute += ' --jobxact ' + job_id
            line_to_execute += ' --file ' + job_file.name
            line_to_execute += ' --format yaml'
            logging.debug('Popen: %s', line_to_execute)
            process = Popen([line_to_execute], universal_newlines=True, stdout=PIPE, stderr=PIPE, shell=True)
            out, err = process.communicate()
            logging.debug(out)
            if process.returncode == 2:
                logging.warning('Rundeck: user %s tries to access non existing project.', self.project_id)
                logging.debug(err)
                raise ProjectNotFoundError
            if process.returncode != 0:
                logging.debug(err)
                raise RundeckError(err)
            job_properties = yaml.safe_load(job_file)
            if not job_properties:
                logging.warning('Rundeck: user %s tries to access non existing job %s.',
                                self.project_id, job_id)
                raise JobNotFoundError
        return job_properties[0]

    @dump_args
    def delete_job(self, job_id):
        '''
        Delete a job.

        :param job_id:            the unique job identifier corresponding to the job to update
        :raises JobNotFoundError: if the job doesn't exist
        :raises RundeckError:     on unexpected Rundeck error
        :returns:                 a dictionary containing the backend's response
        '''
        line_to_execute = 'rd jobs purge'
        line_to_execute += ' --confirm'
        line_to_execute += ' --idlist ' + self.project_id + '-' + job_id
        logging.debug('Popen: %s', line_to_execute)
        process = Popen([line_to_execute], universal_newlines=True, stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate()
        logging.debug(out.rstrip('\n'))
        if process.returncode == 2:
            logging.warning('Rundeck: user %s tries to delete non existing job.', self.project_id)
            logging.debug(err)
            raise JobNotFoundError(err)
        if process.returncode != 0:
            logging.debug(err)
            raise RundeckError(err)
        payload = {
            'message': 'successfully deleted',
            'name': job_id
        }
        return payload

    @dump_args
    def get_jobs(self):
        '''
        Get all job definitions in the current project.

        :raises ProjectNotFoundError: if the project doesn't exist
        :raises RundeckError:         on unexpected Rundeck error
        :returns:                     a dictionary containing the backend's response
        '''
        with NamedTemporaryFile() as jobs_file:
            line_to_execute = 'rd jobs list'
            line_to_execute += ' --project ' + self.project_id
            line_to_execute += ' --file ' + jobs_file.name
            line_to_execute += ' --format yaml'
            logging.debug('Popen: %s', line_to_execute)
            process = Popen([line_to_execute], universal_newlines=True, stdout=PIPE, stderr=PIPE, shell=True)
            out, err = process.communicate()
            out = out.rstrip('\n')
            logging.debug(out)
            if process.returncode == 2:
                logging.warning('Rundeck: user %s tries to access non existing project.', self.project_id)
                logging.debug(err)
                raise ProjectNotFoundError(err)
            if process.returncode != 0:
                logging.debug(err)
                raise RundeckError(err)
            jobs_properties = yaml.safe_load(jobs_file)
        if not jobs_properties:
            payload = {'message': 'No jobs found in project ' + self.project_id + '.'}
        else:
            payload = jobs_properties
        return payload

    @dump_args
    def modify_all_jobs_meta(self, meta):
        '''
        Modify meta of all jobs in a project, like if the jobs are active.

        :param meta:                  the dictionary of user inputs
        :raises ProjectNotFoundError: if the project doesn't exist
        :raises RundeckError:         on unexpected Rundeck error
        :returns:                     a dictionary containing the backend's response
        '''
        if 'enable' in meta:
            if meta.get('enable') == 'True':
                line_to_execute = 'rd jobs reschedulebulk'
                payload = {'message': 'All jobs successfully enabled.'}
            else:
                line_to_execute = 'rd jobs unschedulebulk'
                payload = {'message': 'All jobs successfully disabled.'}
            line_to_execute += ' --project ' + self.project_id
            line_to_execute += ' --job job'
            line_to_execute += ' --confirm'
            logging.debug('Popen: %s', line_to_execute)
            process = Popen([line_to_execute], universal_newlines=True,
                            stdout=PIPE, stderr=PIPE, shell=True)
            out, err = process.communicate()
            logging.debug(out.rstrip('\n'))
            if process.returncode == 2:
                logging.debug(err)
                raise ProjectNotFoundError(err)
            if process.returncode != 0:
                logging.debug(err)
                raise RundeckError(err)
        return payload

    @dump_args
    def delete_jobs(self):
        '''
        Delete all jobs in the current project.

        :raises ProjectNotFoundError: if the project doesn't exist
        :raises RundeckError:         on unexpected Rundeck error
        :returns:                     a dictionary containing the backend's response
        '''
        line_to_execute = 'rd jobs purge'
        line_to_execute += ' --project ' + self.project_id
        line_to_execute += ' --confirm'
        line_to_execute += ' --job job'
        logging.debug('Popen: %s', line_to_execute)
        process = Popen([line_to_execute], universal_newlines=True, stdout=PIPE, stderr=PIPE, shell=True)
        out, err = process.communicate()
        logging.debug(out.rstrip('\n'))
        if process.returncode == 2:
            logging.warning('Rundeck: user %s tries to access non existing project.', self.project_id)
            logging.debug(err)
            raise ProjectNotFoundError(err)
        if process.returncode != 0:
            logging.debug(err)
            raise RundeckError(err)
        payload = {'message': 'All jobs successfully deleted.'}
        return payload

    @dump_args
    def is_sharable(self):
        '''
        Get the sharable status of the current project.

        :raises ProjectNotFoundError: if the project doesn't exist
        :returns:                     a boolean
        '''
        path = os.path.join(self.config['SCHEDULER']['PROJECTS_HOME'], self.project_id, 'shareable')
        path_parent = os.path.abspath(os.path.join(path, os.pardir))
        if not os.path.exists(path_parent):
            raise ProjectNotFoundError
        if os.path.exists(path):
            return True
        return False
