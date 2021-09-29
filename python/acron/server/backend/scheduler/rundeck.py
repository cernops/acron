#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
#pylint: disable=too-many-lines
'''Implementation of the Rundeck backend client'''

import logging
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
import requests
import yaml
from acron.exceptions import (JobNotFoundError, ProjectNotFoundError,
                              RundeckError, UserNotFoundError,
                              NotShareableError, ArgsMalformedError)
from acron.utils import replace_in_file
from acron.constants import ProjectPerms
from acron.server.utils import (dump_args, fqdnify, create_parent,
                                _cron2quartz, _execute_command,
                                _get_project_home_path, _delete_shareable_file)
from acron.server.constants import ConfigFilenames, OpenModes
from acron.notifications import email_user
from . import Scheduler

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)',
               'Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


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
    def _exec_cmd_raise_err_if_fails(cmd, project_id=None, disable_check_job_found=True):
        '''
        Open subprocess and execute command.
        Raise error if exit code is not 0.
        :param cmd: Command to execute as string
        :raises RundeckError: on unexpected backend error
        :returns: Tuple of return code and error message, if any
        '''
        returncode, out, err = _execute_command(cmd)

        if project_id is not None and returncode == 2:
            project_not_found = re.match(
                'Error: project does not exist', err)
            if project_not_found or disable_check_job_found:
                logging.warning(
                    'Rundeck: user %s tries to access non existing project.', project_id)
                logging.debug(err)
                raise ProjectNotFoundError(err)

            if not disable_check_job_found:
                logging.warning(
                    'Rundeck: user %s tries to access non existing job.', project_id)
                logging.debug(err)
                raise JobNotFoundError(err)

        # Omitting logging statement here because the function _execute_command
        # already includes this.
        if returncode != 0:
            raise RundeckError(err)

        return returncode, out, err

    @dump_args
    def _get_project_home_path(self, project_id, filename):
        '''
        Get path to shareable file in a specific project
        :param project_id: ID of project to construct path with
        :param filename:   name of file to get path to
        :returns: path to file for project_id
        :returns: absolute path to parent directory of file for project_id
        '''
        path, path_parent = _get_project_home_path(
            self.config, project_id, filename)
        return path, path_parent

    @dump_args
    def _get_shareable_path(self):
        '''
        Get path to project's shareable config file
        '''
        path, _ = self._get_project_home_path(
            self.project_id, ConfigFilenames.SHAREABLE)
        return path

    @dump_args
    def _ensure_config_file_exists(self, filename, default_value=''):
        '''
        Ensures config file exists. Creates parent directory, if needed.

        :param filename:        name of file to get path to
        :param default_value:   initialization value of file, in case it is created

        :returns: True if file already existed, False otherwise
        '''
        project_id = self.project_id
        path, path_parent = self._get_project_home_path(project_id, filename)
        create_parent(path_parent)
        if not os.path.exists(path):
            logging.debug(
                f'{path} does not exist, creating with value {default_value}.')
            Path(path_parent).mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as path:
                path.write(default_value)
            return False

        return True

    @dump_args
    def _ensure_project_exists(self, project_id):
        '''
        Ensures config file exists. Creates parent directory, if needed.
        :param project_id:      ID of project to construct path with
        :returns: True if project already existed, False otherwise
        '''
        if not self._project_exists(project_id, self.config):
            logging.debug(
                f'Project {project_id} does not exist yet. Creating to ensure it exists')
            self.create_project(project_id, self.config)
            return False

        logging.debug(f'Ensured project {project_id} already exists.')
        return True

    @staticmethod
    @dump_args
    def _backend_obj_exists(obj_val, obj_name_singular, config, long_option_name=None):
        '''
        Perform a generic lookup on the backend.
        :param obj_val:        name of backend object for lookup
        :param obj_name_singular: name of object as string,
                                  should be consistent with rd's top-level commands
        :returns:                 True if the user exists, False otherwise
        '''
        obj_name_plural = f'{obj_name_singular}s'
        if not long_option_name:
            long_option_name = obj_name_singular

        logging.debug(
            f'Performing {obj_name_singular} lookup on the backend ' +
            f'for {obj_name_singular} {obj_val}')
        Rundeck._config(config)
        cmd = f'rd {obj_name_plural} info'
        cmd += f' --{long_option_name} ' + obj_val

        returncode, _, _ = _execute_command(cmd)
        obj_exists = returncode == 0
        logging.debug(
            f'{obj_name_singular} {obj_val} exists on the backend: {obj_exists}')
        return obj_exists

    @staticmethod
    @dump_args
    def _job_exists(project, job_id, config):
        '''
        Perform a job lookup on the backend.
        :param project:
        :param job:
        :returns:    True if the job exists, False otherwise
        '''
        job_uuid = f'{project}-{job_id}'
        return Rundeck._backend_obj_exists(
            obj_val=job_uuid, obj_name_singular='job', config=config, long_option_name='id')

    @staticmethod
    @dump_args
    def _user_exists(user, config):
        '''
        Perform a user lookup on the backend.
        :param user:
        :returns:    True if the user exists, False otherwise
        '''
        return Rundeck._backend_obj_exists(
            obj_val=user, obj_name_singular='user', config=config)

    @staticmethod
    @dump_args
    def _project_exists(project_id, config):
        '''
        Perform a project lookup on the backend.
        :returns: True if the project exists, False otherwise
        '''
        return Rundeck._backend_obj_exists(
            obj_val=project_id, obj_name_singular='project', config=config)

    @dump_args
    def _generate_job_name(self):
        '''
        Generates a new name that does not yet exist in the project.
        :returns: a string with the new job name
        '''
        if not self._ensure_config_file_exists(ConfigFilenames.MAX_JOB_ID, default_value='1'):
            max_job_id = 1
        else:
            path, _ = self._get_project_home_path(
                self.project_id, ConfigFilenames.MAX_JOB_ID)
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
        cmd = f'rd nodes --project {self.project_id} --filter {target}'
        _, out, _ = Rundeck._exec_cmd_raise_err_if_fails(cmd)
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
        filename = os.path.join('etc', 'resources.yaml')
        path, _ = self._get_project_home_path(self.project_id, filename)
        create_parent(path)
        logging.debug('Adding %s to %s.', target, path)
        with open(path, 'a+') as resources:
            resources.write('\n\n' +
                            target + ':\n' +
                            '  nodename: ' + target + '\n' +
                            '  hostname: ' + target + '\n' +
                            '  username: ' + self.project_id + '\n' +
                            '  tags: ""')

    @dump_args
    def _get_shareable_projects(self, user):
        '''
        Get all shareable projects to user.
        :param user: name of the user
        :returns: object with project (key) and permissions (value)
        '''
        project_names = Rundeck.list_projects(self.config)
        projects_permissions = {}
        for project_name in project_names:
            # Check if project's shareable file exists
            path, _ = self._get_project_home_path(
                project_name, ConfigFilenames.SHAREABLE)

            if not os.path.exists(path):
                logging.debug(
                    f'Shareable file for project {project_name}' +
                    f'under {path} does not exist')
                continue

            with open(path, OpenModes.READ) as shareable_config:
                # Iterate lines of shareable file
                for user_acl_pair in shareable_config:
                    if user in user_acl_pair:
                        # Split gets permissions only from line. Username is redundant
                        # Strip removes trailing new line from permissions
                        projects_permissions[project_name] = user_acl_pair.split(':')[
                            1].strip()

        return projects_permissions

    @dump_args
    def _delete_user_share_from_project(self, user):
        ''''
        Delete user share from project's shareable file on filesystem
        :param user: username
        :returns:    Tuple with updated ACL list for project and boolean
        '''
        # Default value
        was_project_shared_with_user = False

        # Check if project is shareable
        # Safety check only, after the previous func calls, this file should exist already.
        self.is_shareable(user=self.project_id)

        # Get path to project's shareable config file
        path = self._get_shareable_path()

        logging.debug(f'Reading existing project permissions in {path}')
        with open(path, OpenModes.READ) as project_shared_with_file:
            user_acl_list = project_shared_with_file.readlines()

        # Delete existing project permissions for user, if any
        for line in user_acl_list:
            if line.startswith(f'{user}: '):
                was_project_shared_with_user = True
                logging.debug(f'Deleting existing user permissions for {user} "' + line.strip("\n") +
                              f'" in project {self.project_id} in file {path}')
                user_acl_list.remove(line)
        return user_acl_list, was_project_shared_with_user

    @dump_args
    def _overwrite_project_acl(self, user_acl_list):
        '''
        Overwrite project permissions in shareable file with given parameter

        :param user_acl_list: List of lines in shareable file

        :returns:             Updated ACL list
        '''
        user_acl_list_str = str(user_acl_list)

        # Get path to project's shareable config file
        path = self._get_shareable_path()
        logging.debug(
            f'Writing new ACL list to {path}:\n' + user_acl_list_str)

        # Write updated project permissions
        with open(path, OpenModes.WRITE) as project_shared_with_file:
            project_shared_with_file.writelines(user_acl_list)

        logging.debug(
            f'Contents of file {path}:' + '\n' + user_acl_list_str)

        return user_acl_list

    @dump_args
    def _append_new_project_permissions(self, user_acl_list, user, perms):
        '''
        Append new project permissions to shareable file

        :param user_acl_list: List of lines in shareable file
        :param user:          username to share project with
        :param perms:         Permissions to give user in project

        :returns:             Updated ACL list
        '''
        user_project_perms = f'{user}: {perms}\n'

        logging.debug(
            f'Append new project permissions for user {user_project_perms}')
        user_acl_list.append(user_project_perms)

        return self._overwrite_project_acl(user_acl_list)

    @staticmethod
    @dump_args
    def _get_job_ids(project_id):
        '''
        Get job ids in a project
        :param project:       Name of the project
        :raises RundeckError: on unexpected Rundeck error
        :returns:             Comma separated list of job ids
        '''
        cmd = f'rd jobs list --project {project_id}'
        cmd += ' --outformat %id'
        _, out, _ = Rundeck._exec_cmd_raise_err_if_fails(cmd)

        # Rundeck returns extra trailing empty line; delete
        job_ids = out.replace('\n\n', '')
        # Comma separated list of jobs
        job_ids = job_ids.replace('\n', ',')
        return job_ids

    # pylint: disable=R0912, R0913, R0915

    @dump_args
    def _create_update_job(self, job_id, schedule, target, command, description, is_create):
        '''
        Create or update a job.

        :param job_id:            the unique job identifier corresponding to the job to update
        :param schedule:          the schedule of the new job, Quartz format
        :param target:            the node on which the job will be executed, FQDN
        :param command:           the command to launch on the target at the given schedule
        :param description:       an optional description of the job
        :param is_create:         specifies if create or update job requested
        :raises ArgsMalformedError: on wrong job_id
        :raises JobNotFoundError: if the job to update doesn't exist
        :raises RundeckError:     on unexpected Rundeck error
        :returns:                 a dictionary containing the backend's response
        '''
        self._ensure_project_exists(self.project_id)
        if is_create:  # new job
            # Increase count of jobs regardless of wether job_id was provided
            default_job_id = self._generate_job_name()
            if job_id is None:
                job_id = default_job_id
            type_message = 'created'

            if self._job_exists(self.project_id, job_id, self.config):
                logging.error(
                    f'Error on job creation, job_id {job_id} provided by the user already exists.')
                raise ArgsMalformedError
        else:  # update existing job
            job_properties = self.get_job(job_id)
            if schedule is None:
                schedule = ' '.join(
                    job_properties['description'].split(' ')[0:5])
            if target is None:
                target = job_properties['nodefilters']['filter'].replace(
                    'name: ', '')
            if command is None:
                command = job_properties['sequence']['commands'][0]['exec']
            if description is None:
                description = ' '.join(
                    job_properties['description'].split(' ')[5:])
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
            replace_in_file('__DESCRIPTION__', schedule +
                            ' ' + description, job_file.name)
            replace_in_file('__DOMAIN__', self.config['DOMAIN'], job_file.name)
            replace_in_file('__JOB_NAME__', job_id, job_file.name)
            replace_in_file('__TARGET_HOST__', target, job_file.name)
            replace_in_file('__COMMAND__', command, job_file.name)
            replace_in_file('__CRONTAB__', crontab, job_file.name)
            cmd = 'rd jobs load'
            cmd += ' --project ' + self.project_id
            cmd += ' --file ' + job_file.name
            cmd += ' --format yaml --duplicate update'
            Rundeck._exec_cmd_raise_err_if_fails(cmd)
        payload = {'message': 'Job successfully ' + type_message + '.'}
        payload.update(self.get_job(job_id))
        return payload

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
        cmd = 'rd system info'
        _, out, _ = Rundeck._exec_cmd_raise_err_if_fails(cmd)
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
            cmd = 'rd projects create'
            cmd += ' --project ' + project_id
            cmd += ' --file ' + properties.name
            Rundeck._exec_cmd_raise_err_if_fails(cmd)

        with NamedTemporaryFile() as acls:
            replace_in_file('__USERNAME__', project_id,
                            config['SCHEDULER']['PROJECT_ACLS_SOURCE'], acls.name)
            cmd = 'rd projects acls create'
            cmd += ' --project ' + project_id
            cmd += ' --file ' + acls.name
            cmd += ' --name ' + project_id + '.aclpolicy'
            Rundeck._exec_cmd_raise_err_if_fails(cmd)

        with NamedTemporaryFile() as system_acls:
            replace_in_file('__USERNAME__', project_id,
                            config['SCHEDULER']['SYSTEM_ACLS_SOURCE'], system_acls.name)
            cmd = 'rd system acls create'
            cmd += ' --file ' + system_acls.name
            cmd += ' --name ' + project_id + '.aclpolicy'
            Rundeck._exec_cmd_raise_err_if_fails(cmd)

    @dump_args
    def get_project_name(self):
        '''
        Get project's name.
        :returns: a dictionary containing the backend's response
        '''
        return {'message': self.project_id}

    @dump_args
    def get_project_users(self):
        '''
        Get a project's users.

        :raises ProjectNotFoundError: if the project doesn't exist
        :returns: a dictionary containing the backend's response
        '''
        payload_project_unshared = {
            'message': f'Your project {self.project_id} hasn\'t been shared yet.'}
        # Check if project exists in backend
        project_exists = self._project_exists(self.project_id, self.config)
        # Check if file with access permissions exists
        path, _ = self._get_project_home_path(
            self.project_id, ConfigFilenames.SHAREABLE)
        shareable_exists = os.path.exists(path)

        if not project_exists:
            logging.error(f'Project {self.project_id} doesn\'t exist')
            raise ProjectNotFoundError

        if not shareable_exists:
            logging.debug(f'Shareable file {path} does not exist.')
            return payload_project_unshared

        logging.debug(
            f'Project {self.project_id} and file {path} exist. Proceeding to read {path}')
        logging.debug(
            f'Reading contents of file {path} to get users'
            + f'and their ACL regarding project {self.project_id}')

        if not self.is_shareable(user=self.project_id):
            raise NotShareableError

        with open(path, OpenModes.READ) as project_shared_with_file:
            user_acl_list = project_shared_with_file.read()

        if not user_acl_list:
            logging.debug(f'Shareable file {path} exists but is empty.')
            return payload_project_unshared

        logging.debug(f'Contents of file {path}:\n{user_acl_list}')

        response_msg = f'Your project {self.project_id} is shared with:\n\n'
        response_msg += str(user_acl_list)
        payload = {'message': response_msg}
        return payload

    @dump_args
    def share_project(self, user, perms):
        '''
        Share project with another user.

        :param user:                  username
        :param perms:                 project permissions
        :raises ProjectNotFoundError: if the project doesn't exist
        :raises UserNotFoundError:    if the user doesn't exist
        :returns:                     a dictionary containing the backend's response
        '''
        if user == self.project_id:
            logging.debug(f'User {user} is owner of project {self.project_id}')
            raise ArgsMalformedError

        if not self._user_exists(user, self.config):
            raise UserNotFoundError

        if perms not in ProjectPerms.ALL:
            logging.error(f'Project permissions given {perms}' +
                          f'are invalid. Valid ones are one of the following: {ProjectPerms.ALL}')
            raise ArgsMalformedError

        # Ensure project and its config file exist
        self._ensure_project_exists(self.project_id)
        self._ensure_config_file_exists(
            ConfigFilenames.SHAREABLE, default_value='')
        response_msg = ''

        user_acl_list, was_project_shared_with_user = self._delete_user_share_from_project(
            user)

        if was_project_shared_with_user:
            response_msg += f'Project {self.project_id} was already shared with {user}.\n'

        user_acl_list = self._append_new_project_permissions(
            user_acl_list, user, perms)

        subject_start = f'Acron project {self.project_id} is now shared with'
        body_start = f'Project {self.project_id} is now shared with'
        logging.debug(
            f'Notifying project admin {self.project_id} that project {self.project_id}' +
            f' is now shared with user {user} with {ProjectPerms.NAME_MAP[perms]} permissions.')
        subject = f'{subject_start} {user}'
        body = (f'{body_start} {user} with {ProjectPerms.NAME_MAP[perms]} permissions. ' +
                f'If this wasn\'t you, please contact the service administrators.')
        email_user(self.project_id, subject, body)
        logging.debug(
            f'Notifying user {user} that project {self.project_id} is now shared' +
            f' with {ProjectPerms.NAME_MAP[perms]} permissions.')
        subject = f'{subject_start} you'
        body = (
            f'{body_start} you with {ProjectPerms.NAME_MAP[perms]} permissions.' +
            f'Remember, "with great power comes great responsibility".')
        response_msg += f'Updated permissions. Project is now shared with:\n\n'
        response_msg += ''.join(user_acl_list)
        payload = {'message': response_msg}
        return payload

    @dump_args
    def undo_share_project(self, user):
        '''
        Delete project share for user.

        :param user:                  username
        :raises ProjectNotFoundError: if the project doesn't exist
        :raises ArgsMalformedError:   if the user is the owner of the project
        :raises UserNotFoundError:    if the user doesn't exist
        :returns:                     a dictionary containing the backend's response
        '''
        if user == self.project_id:
            logging.debug(f'User {user} is owner of project {self.project_id}')
            raise ArgsMalformedError

        if not self._user_exists(user, self.config):
            raise UserNotFoundError

        # Check if project exists in backend
        if not self._project_exists(self.project_id, self.config):
            logging.error(f'Project {self.project_id} doesn\'t exist')
            raise ProjectNotFoundError

        response_msg = ''
        user_acl_list, was_project_shared_with_user = self._delete_user_share_from_project(
            user)
        if not was_project_shared_with_user:
            response_msg += f'Project {self.project_id} was not previously' + \
                f' shared with {user}.\n'

        user_acl_list = self._overwrite_project_acl(user_acl_list)
        subject_start = f'Acron project {self.project_id} is no longer shared with'
        body_start = f'Project {self.project_id} is no longer shared with'
        logging.debug(
            f'Notifying project admin {self.project_id} that project share for user {user} was revoked.')
        subject = f'{subject_start} {user}'
        body = (f'{body_start} {user}. ' +
                f'If this wasn\'t you, please contact the service administrators.')
        email_user(self.project_id, subject, body)
        logging.debug(
            f'Notifying user {user} that project share for project {self.project_id} was revoked.')
        subject = f'{subject_start} you'
        body = f'{body_start} you.'
        email_user(user, subject, body)
        response_msg += f'Project is now shared with:\n\n'
        response_msg += ''.join(user_acl_list)
        payload = {'message': response_msg}
        return payload

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
        if not Rundeck._project_exists(project_id, config):
            logging.warning(
                'Rundeck: admin tries to delete non existing project %s.', project_id)
            raise ProjectNotFoundError()

        Rundeck._config(config)
        _delete_shareable_file(project_id, config)
        logging.debug(
            f'Deleting system ACL definition for {project_id}.aclpolicy')
        cmd = 'rd system acls delete'
        cmd += ' --name ' + project_id + '.aclpolicy'
        Rundeck._exec_cmd_raise_err_if_fails(cmd)
        logging.debug(
            f'Deleting project ACL definition for {project_id}.aclpolicy')
        cmd = 'rd projects acls delete'
        cmd += ' --project ' + project_id
        cmd += ' --name ' + project_id + '.aclpolicy'
        Rundeck._exec_cmd_raise_err_if_fails(cmd)
        cmd = 'rd projects delete'
        cmd += ' --confirm'
        cmd += ' --project ' + project_id
        returncode, _, err = _execute_command(cmd)
        if returncode == 2:
            logging.debug(err)
            raise ProjectNotFoundError(err)
        if returncode != 0:
            logging.debug(err)
            raise RundeckError(err)
        payload = {
            'message': 'successfully deleted',
            'name': project_id
        }
        return payload

    @dump_args
    def get_projects(self, user):
        '''
        Get visible projects for user together with ACL.
        :param user:          name of the user
        :raises RundeckError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        logging.debug(f'Searching for shareable projects for user {user}')

        projects_permissions = self._get_shareable_projects(user)

        if not projects_permissions:
            return {'message': 'No projects have been shared with you yet.'}

        # Convert from object to YAML string
        projects_permissions = yaml.dump(projects_permissions)

        logging.debug(
            f'Projects shareable for user {user}:\n{projects_permissions}')

        payload = {'message': projects_permissions}
        return payload

    @staticmethod
    @dump_args
    def list_projects(config):
        '''
        Get the definition of all projects.
        :param config:        a dictionary containing all the config values
        :raises RundeckError: on unexpected backend error
        :returns:             a dictionary containing the backend's response
        '''
        Rundeck._config(config)
        cmd = 'rd projects list'
        cmd += ' --outformat %name'
        _, out, _ = Rundeck._exec_cmd_raise_err_if_fails(cmd)
        projects_list = out.split('\n')
        return projects_list

    @staticmethod
    @dump_args
    def projects_on_server(server_uuid, config):
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
        path = config['SCHEDULER']['API_URL'] + '/scheduler/jobs'
        projects = []
        try:
            response = requests.get(path, json=params, headers=headers)
            if response.status_code == 200 and hasattr(response, 'json'):
                for job in response.json():
                    if not job['project'] in projects:
                        projects.append(job['project'])
        except Exception as error: #pylint: disable=broad-except
            logging.warning(error)
        return projects

    @staticmethod
    @dump_args
    def take_over_jobs(server_uuid, config, project):
        '''
            Take over all the jobs from another server.
            :param server_uuid:   the UUID of the server to take the jobs from
            :param config:        a dictionary containing all the config values
            :raises RundeckError: on unexpected backend error
            :returns:             a dictionary containing the backend's response
            '''
        params = {
            'server': {
                'uuid': server_uuid
            },
            'project': project
        }
        headers = {
            'X-Rundeck-Auth-Token': config['SCHEDULER']['API_KEY'],
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        path = config['SCHEDULER']['API_URL'] + '/scheduler/takeover'
        try:
            response = requests.put(path, json=params, headers=headers)
            if response.status_code == 200 and hasattr(response, 'json'):
                return response.json()
        except Exception as error: #pylint: disable=broad-except
            logging.warning(error)
        raise RundeckError('Takeover failed. ' + response.text)

    # pylint: disable=too-many-arguments

    @dump_args
    def create_job(self, job_id, schedule, target, command, description):
        '''
        Create a new job.
        :param job_id:        the unique job identifier corresponding to the job to create
        :param schedule:      the schedule of the new job, crontab format
        :param target:        the node on which the job will be executed, FQDN
        :param command:       the command to launch on the target at the given schedule
        :param description:   an optional description of the job
        :raises ArgsMalformedError: on wrong job_id
        :raises RundeckError: on unexpected Rundeck error
        :returns:             a dictionary containing the backend's response
        '''
        return self._create_update_job(job_id, schedule, target, command, description, is_create=True)

    # pylint: disable=R0913
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
        return self._create_update_job(job_id, schedule, target, command, description, is_create=False)

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
                cmd = 'rd jobs reschedule'
                payload['message'] = 'Job successfully enabled.'
            else:
                cmd = 'rd jobs unschedule'
                payload['message'] = 'Job successfully disabled.'

            cmd += ' --project ' + self.project_id
            cmd += ' --job ' + job_id
            Rundeck._exec_cmd_raise_err_if_fails(
                cmd, self.project_id, disable_check_job_found=False)

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
            cmd = 'rd jobs list'
            cmd += ' --project ' + self.project_id
            cmd += ' --jobxact ' + job_id
            cmd += ' --file ' + job_file.name
            cmd += ' --format yaml'
            Rundeck._exec_cmd_raise_err_if_fails(
                cmd, self.project_id)

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
        cmd = 'rd jobs purge --confirm'
        cmd += ' --idlist ' + self.project_id + '-' + job_id
        Rundeck._exec_cmd_raise_err_if_fails(
            cmd, self.project_id)
        payload = {'message': 'successfully deleted',
                   'name': job_id}
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
            cmd = 'rd jobs list'
            cmd += ' --project ' + self.project_id
            cmd += ' --file ' + jobs_file.name
            cmd += ' --format yaml'
            Rundeck._exec_cmd_raise_err_if_fails(
                cmd, self.project_id)
            jobs_properties = yaml.safe_load(jobs_file)
        if not jobs_properties:
            payload = {
                'message': 'No jobs found in project ' +
                           self.project_id + '.'}
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
                cmd = 'rd jobs reschedulebulk'
                payload = {'message': 'All jobs successfully enabled.'}
            else:
                cmd = 'rd jobs unschedulebulk'
                payload = {'message': 'All jobs successfully disabled.'}
            cmd += ' --project ' + self.project_id
            cmd += f' --idlist {self._get_job_ids(self.project_id)} --confirm'
            Rundeck._exec_cmd_raise_err_if_fails(
                cmd, self.project_id)
        return payload

    @dump_args
    def delete_jobs(self):
        '''
        Delete all jobs in the current project.
        :raises ProjectNotFoundError: if the project doesn't exist
        :raises RundeckError:         on unexpected Rundeck error
        :returns:                     a dictionary containing the backend's response
        '''
        cmd = f'rd jobs purge --project {self.project_id}'
        cmd += f' --idlist {self._get_job_ids(self.project_id)} --confirm'
        Rundeck._exec_cmd_raise_err_if_fails(
            cmd, self.project_id)
        payload = {'message': 'All jobs successfully deleted.'}
        return payload

    @dump_args
    def is_shareable(self, user):
        '''
        Get the shareable status of the current project.
        :param user: check if project is shared with user given
        :raises ProjectNotFoundError: if the project doesn't exist
        :returns:                     a boolean or ACL for user
        '''
        path, path_parent = self._get_project_home_path(
            self.project_id, ConfigFilenames.SHAREABLE)
        not_shareable_msg = f'project {self.project_id} is not shareable for {user}'
        logging.debug(f'Getting shareable status of project {self.project_id}')
        if user == self.project_id:
            logging.debug(f'User {user} is owner of project {self.project_id}')
            return True
        logging.debug(
            f'Checking if shareable file of {self.project_id} exists: {self.project_id}')
        if not os.path.exists(path_parent):
            logging.error(
                f'Project {self.project_id} not found on filesystem.'
                + f'Path {path_parent} does not exist.')
            raise ProjectNotFoundError
        if os.path.exists(path):
            logging.debug(
                f'Path {path} exists. Proceeding to read its contents...')
            with open(path, OpenModes.READ) as shareable_file:
                shareable_people = yaml.safe_load(shareable_file)
                if not shareable_people:
                    logging.debug(
                        f'File {path} is empty, ' + not_shareable_msg)
                    return False

                if user not in shareable_people:
                    logging.debug(
                        f'Project {self.project_id} is not shareable for user {user}')
                    return False

                logging.debug(
                    f'ACL for {user} found in {path}\n\n{shareable_people[user]}')
                return shareable_people[user]

        logging.debug(f'File does not exist, ' + not_shareable_msg)
        return False
