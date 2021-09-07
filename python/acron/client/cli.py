#
# (C) Copyright 2021 CERN
#
# This software is distributed under the terms of the GNU General Public Licence version 3
# (GPL Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''CLI-related functions and constants'''

__author__ = 'Rodrigo Bermudez Schettino (CERN)'
__credits__ = ['Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


from .creds import creds_delete, creds_get, creds_put
from .jobs import (jobs_delete, jobs_get, jobs_put,
                   jobs_post, jobs_enable, jobs_disable)
from .projects import (projects_get, projects_share, projects_delete)


EPILOG_CREDS = 'For more information, please check the man page, acron-creds(1).'
EPILOG_JOBS = 'For more information, please check the man page, acron-jobs(1).'
EPILOG_PROJECTS = 'For more information, please check the man page, acron-projects(1).'

FLAG_SHORT_JOBID = '-j'
FLAG_SHORT_PROJECT = '-p'
FLAG_SHORT_DESCR = '-d'
FLAG_SHORT_CMD = '-c'
FLAG_SHORT_TARGET = '-t'
FLAG_SHORT_SCHEDULE = '-s'
FLAG_SHORT_ALL = '-a'
FLAG_SHORT_USER = '-u'
FLAG_SHORT_WRITE = '-w'
FLAG_SHORT_DELETE = '-d'

FLAG_LONG_JOBID = '--job_id'
FLAG_LONG_PROJECT = '--project'
FLAG_LONG_DESCR = '--description'
FLAG_LONG_CMD = '--command'
FLAG_LONG_TARGET = '--target'
FLAG_LONG_SCHED = '--schedule'
FLAG_LONG_ALL = '--all'
FLAG_LONG_USER = '--user_id'
FLAG_LONG_WRITE = '--write'
FLAG_LONG_DELETE = '--delete'

# Displayed only in usage messages
METAVAR_JOBID = 'JOB_ID'
METAVAR_PROJECT = 'PROJECT'
METAVAR_DESCR = "'DESCR'"
METAVAR_TARGET = 'FQDN'
METAVAR_CMD = "'CMD'"
METAVAR_COMMAND = '<command>'
METAVAR_SCHEDULE = "'CRON'"
METAVAR_USERID = 'USER_ID'

HELP_DESCRIPTION = 'description'
HELP_ARG_JOB = 'The unique job identifier corresponding to the job.'
HELP_ARG_PROJECT = 'Name of the project to manage, if the project is shareable.'
HELP_ARG_USER = 'Name of the user to share project with.'
HELP_ARG_SCHEDULE = 'The schedule of the job, quoted, crontab format.'
HELP_ARG_TARGET = 'The node on which the job will be executed, FQDN.'
HELP_ARG_CMD = 'The command to launch, quoted.'
HELP_ARG_DESCR = 'A description that will be displayed when the job is shown.'
HELP_ARG_WRITE = 'Grant user write permissions to project. Default: read-only permissions.'

TITLE_COMMANDS = 'Commands'


def add_creds_subparsers(arg_parser):
    '''
    Add creds subparsers.

    :param arg_parser: ArgumentParser class instance
    '''
    # acron creds [--help]
    creds_parser = arg_parser.add_parser(
        'creds',
        help='credentials management utility',
        description='Acron credentials management utility.',
        epilog=EPILOG_CREDS)
    creds_subparsers = creds_parser.add_subparsers(
        title=TITLE_COMMANDS, metavar=METAVAR_COMMAND, help=HELP_DESCRIPTION)
    creds_subparsers.required = True

    # acron creds show [--help]
    creds_get_parser = creds_subparsers.add_parser(
        'status',
        help='show credentials status, does not download them',
        description='Acron credentials status utility.',
        epilog=EPILOG_CREDS)
    creds_get_parser.set_defaults(func=creds_get)

    # acron creds upload [--file FILE|--generate] [--help]
    creds_update_parser = creds_subparsers.add_parser(
        'upload',
        help='upload new credentials, either existing (--file) or generated on the fly (--generate)',
        description='Acron credentials upload utility.',
        epilog=EPILOG_CREDS)
    creds_update_parser.set_defaults(func=creds_put)
    creds_update_parser_type = creds_update_parser.add_mutually_exclusive_group(
        required=True)
    creds_update_parser_type.add_argument(
        '-f', '--file', metavar='FILE', help='Path to the credentials file to upload.')
    creds_update_parser_type.add_argument(
        '-g', '--generate', action='store_true', help='Generate the keytab.')

    # acron creds delete [--help]
    creds_delete_parser = creds_subparsers.add_parser(
        'delete',
        help='delete credentials, if they exist',
        description='Acron credentials deletion utility.',
        epilog=EPILOG_CREDS)
    creds_delete_parser.set_defaults(func=creds_delete)


def add_jobs_subparsers(arg_parser):
    '''
    Add job subparsers.

    :param arg_parser: ArgumentParser class instance
    '''

    # acron jobs [--help]
    jobs_parser = arg_parser.add_parser(
        'jobs',
        help='jobs management utility',
        description='Acron jobs management utility.',
        epilog=EPILOG_JOBS)
    jobs_subparsers = jobs_parser.add_subparsers(
        title=TITLE_COMMANDS, metavar=METAVAR_COMMAND, help=HELP_DESCRIPTION)
    jobs_subparsers.required = True

    # acron jobs show (--job_id JOB_ID) [--project PROJECT] [--help]
    jobs_get_parser = jobs_subparsers.add_parser(
        'show',
        help='show job definition',
        description='Acron jobs information utility.',
        epilog=EPILOG_JOBS)
    jobs_get_parser.set_defaults(func=jobs_get)
    jobs_get_parser.add_argument(
        FLAG_SHORT_JOBID, FLAG_LONG_JOBID, metavar=METAVAR_JOBID,
        help=HELP_ARG_JOB)
    jobs_get_parser.add_argument(
        FLAG_SHORT_PROJECT, FLAG_LONG_PROJECT, metavar=METAVAR_PROJECT,
        help=HELP_ARG_PROJECT)

    # acron jobs create --schedule 'CRON' --target HOST --command 'CMD' [--description 'DESCR']
    #                   [--project PROJECT] [--help]
    jobs_post_parser = jobs_subparsers.add_parser(
        'create',
        help='create a job.',
        description='Acron jobs creation utility.',
        epilog=EPILOG_JOBS)
    jobs_post_parser.set_defaults(func=jobs_post)
    jobs_post_parser.add_argument(
        FLAG_SHORT_JOBID, FLAG_LONG_JOBID, metavar=METAVAR_JOBID, required=False,
        help=HELP_ARG_JOB)
    jobs_post_parser.add_argument(
        FLAG_SHORT_SCHEDULE, FLAG_LONG_SCHED, metavar=METAVAR_SCHEDULE, required=True,
        help=HELP_ARG_SCHEDULE)
    jobs_post_parser.add_argument(
        FLAG_SHORT_TARGET, FLAG_LONG_TARGET, metavar=METAVAR_TARGET, required=True,
        help=HELP_ARG_TARGET)
    jobs_post_parser.add_argument(
        FLAG_SHORT_CMD, FLAG_LONG_CMD, metavar=METAVAR_CMD, required=True,
        help=HELP_ARG_CMD)
    jobs_post_parser.add_argument(
        FLAG_SHORT_DESCR, FLAG_LONG_DESCR, metavar=METAVAR_DESCR,
        help=HELP_ARG_DESCR)
    jobs_post_parser.add_argument(
        FLAG_SHORT_PROJECT, FLAG_LONG_PROJECT, metavar=METAVAR_PROJECT,
        help=HELP_ARG_PROJECT)

    # acron jobs update --job_id JOB_ID [--schedule 'CRON'] [--target HOST] [--command 'CMD']
    #                   [--description 'DESCR'] [--project PROJECT]  [--help]
    jobs_put_parser = jobs_subparsers.add_parser(
        'update',
        help='modify a job.',
        description='Acron jobs modification utility.',
        epilog=EPILOG_JOBS)
    jobs_put_parser.set_defaults(func=jobs_put)
    jobs_put_parser.add_argument(
        FLAG_SHORT_JOBID, FLAG_LONG_JOBID, metavar=METAVAR_JOBID, required=True,
        help=HELP_ARG_JOB)
    jobs_put_parser.add_argument(
        FLAG_SHORT_SCHEDULE, FLAG_LONG_SCHED, metavar=METAVAR_SCHEDULE,
        help=HELP_ARG_SCHEDULE)
    jobs_put_parser.add_argument(
        FLAG_SHORT_TARGET, '--target', metavar=METAVAR_TARGET,
        help=HELP_ARG_TARGET)
    jobs_put_parser.add_argument(
        FLAG_SHORT_CMD, FLAG_LONG_CMD, metavar=METAVAR_CMD,
        help=HELP_ARG_CMD)
    jobs_put_parser.add_argument(
        FLAG_SHORT_DESCR, FLAG_LONG_DESCR, metavar=METAVAR_DESCR,
        help=HELP_ARG_DESCR)
    jobs_put_parser.add_argument(
        FLAG_SHORT_PROJECT, FLAG_LONG_PROJECT, metavar=METAVAR_PROJECT,
        help=HELP_ARG_PROJECT)

    # acron jobs delete (--job_id JOB_ID|--all) [--project PROJECT] [--help]
    jobs_delete_parser = jobs_subparsers.add_parser(
        'delete',
        help='delete a job',
        description='Acron jobs deletion utility.',
        epilog=EPILOG_JOBS)
    jobs_delete_parser.set_defaults(func=jobs_delete)
    jobs_delete_parser_jobid = jobs_delete_parser.add_mutually_exclusive_group(
        required=True)
    jobs_delete_parser_jobid.add_argument(
        FLAG_SHORT_JOBID, FLAG_LONG_JOBID, metavar=METAVAR_JOBID,
        help=HELP_ARG_JOB)
    jobs_delete_parser_jobid.add_argument(
        FLAG_SHORT_ALL, FLAG_LONG_ALL, action='store_true',
        help='Delete all jobs in the project.')
    jobs_delete_parser.add_argument(
        FLAG_SHORT_PROJECT, FLAG_LONG_PROJECT, metavar=METAVAR_PROJECT,
        help=HELP_ARG_PROJECT)

    # acron jobs enable (--job_id JOB_ID|--all) [--project PROJECT] [--help]
    jobs_enable_parser = jobs_subparsers.add_parser(
        'enable',
        help='enable a disabled job.',
        description='Acron jobs enabling utility.',
        epilog=EPILOG_JOBS)
    jobs_enable_parser.set_defaults(func=jobs_enable)
    jobs_enable_parser_jobid = jobs_enable_parser.add_mutually_exclusive_group(
        required=True)
    jobs_enable_parser_jobid.add_argument(
        FLAG_SHORT_JOBID, FLAG_LONG_JOBID, metavar=METAVAR_JOBID,
        help=HELP_ARG_JOB)
    jobs_enable_parser_jobid.add_argument(
        FLAG_SHORT_ALL, FLAG_LONG_ALL, action='store_true',
        help='Enable all jobs in the project.')
    jobs_enable_parser.add_argument(
        FLAG_SHORT_PROJECT, FLAG_LONG_PROJECT, metavar=METAVAR_PROJECT,
        help=HELP_ARG_PROJECT)

    # acron jobs disable (--job_id JOB_ID|--all) [--project PROJECT] [--help]
    jobs_disable_parser = jobs_subparsers.add_parser(
        'disable',
        help='disable a job without deleting it.',
        description='Acron jobs disabling utility.',
        epilog=EPILOG_JOBS)
    jobs_disable_parser.set_defaults(func=jobs_disable)
    jobs_disable_parser_jobid = jobs_disable_parser.add_mutually_exclusive_group(
        required=True)
    jobs_disable_parser_jobid.add_argument(
        FLAG_SHORT_JOBID, FLAG_LONG_JOBID, metavar=METAVAR_JOBID,
        help=HELP_ARG_JOB)
    jobs_disable_parser_jobid.add_argument(
        FLAG_SHORT_ALL, FLAG_LONG_ALL, action='store_true',
        help='Disable all jobs in the project.')
    jobs_disable_parser.add_argument(
        FLAG_SHORT_PROJECT, FLAG_LONG_PROJECT, metavar=METAVAR_PROJECT,
        help=HELP_ARG_PROJECT)


def add_projects_subparsers(arg_parser):
    '''
    Add project subparsers.

    :param arg_parser: ArgumentParser class instance
    '''

    # acron projects [--help]
    projects_parser = arg_parser.add_parser(
        'projects',
        help='projects management utility',
        description='Acron projects management utility.',
        epilog=EPILOG_PROJECTS)
    projects_subparsers = projects_parser.add_subparsers(
        title=TITLE_COMMANDS, metavar=METAVAR_COMMAND, help=HELP_DESCRIPTION)
    projects_subparsers.required = True

    # acron projects share --user_id USER_ID [--help]
    projects_share_parser = projects_subparsers.add_parser(
        'share',
        help='share project with another user',
        description='Acron projects sharing utility.',
        epilog=EPILOG_PROJECTS
    )
    projects_share_parser.set_defaults(func=projects_share)
    projects_share_parser.add_argument(
        FLAG_SHORT_USER, FLAG_LONG_USER, metavar=METAVAR_USERID,
        required=True, help=HELP_ARG_USER)
    group = projects_share_parser.add_mutually_exclusive_group(
        required=False)
    group.add_argument(
        FLAG_SHORT_WRITE, FLAG_LONG_WRITE,
        action='store_true', help=HELP_ARG_WRITE)
    group.add_argument(
        FLAG_SHORT_DELETE, FLAG_LONG_DELETE, action='store_true',
        help='Delete project share for user.')

    # acron projects show (--all) [--help]
    projects_get_parser = projects_subparsers.add_parser(
        'show',
        help='show project definition',
        description='Acron projects information utility.',
        epilog=EPILOG_PROJECTS)
    projects_get_parser.set_defaults(func=projects_get)
    projects_get_parser.add_argument(
        FLAG_SHORT_ALL, FLAG_LONG_ALL, action='store_true',
        help='Show all shareable projects for current user.')

    # acron projects delete [--help]
    projects_delete_parser = projects_subparsers.add_parser(
        'delete',
        help='delete personal project',
        description='Acron projects deletion utility.',
        epilog=EPILOG_PROJECTS)
    projects_delete_parser.set_defaults(func=projects_delete)
