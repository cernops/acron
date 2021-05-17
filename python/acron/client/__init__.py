#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Acron client'''

import sys
import argparse
import pkg_resources
from acron.utils import check_schedule, check_target, check_command, check_description
from .auth import login
from .creds import creds_delete, creds_get, creds_put
from .jobs import jobs_delete, jobs_get, jobs_post, jobs_enable, jobs_disable

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'


# pylint: disable=R0914, R0915
def input_parser():
    '''
    Get user input and set flags.

    :returns: a dictionnary containing the user's parameters
    '''
    # acron [--version] [--help]
    main_parser = argparse.ArgumentParser(
        description='Acron client. Please use the available subcommands.',
        epilog='More information in the man page acron(1).')
    main_parser.add_argument(
        '-v', '--version', action='version',
        version=pkg_resources.require('acron')[0].version)
    main_subparsers = main_parser.add_subparsers(title='Commands', metavar='<command>', help='description')
    main_subparsers.required = True


    # acron creds [--help]
    creds_parser = main_subparsers.add_parser(
        'creds',
        help='credentials management utility',
        description='Acron credentials management utility.',
        epilog='More information in the man page acron-creds(1).')
    creds_subparsers = creds_parser.add_subparsers(title='Commands', metavar='<command>', help='description')
    creds_subparsers.required = True

    # acron creds show [--help]
    creds_get_parser = creds_subparsers.add_parser(
        'status',
        help='show credentials status, does not download them',
        description='Acron credentials status utility.',
        epilog='More information in the man page acron-creds(1).')
    creds_get_parser.set_defaults(func=creds_get)

    # acron creds upload [--file FILE|--generate] [--help]
    creds_update_parser = creds_subparsers.add_parser(
        'upload',
        help='upload new credentials, either existing (--file) or generated on the fly (--generate)',
        description='Acron credentials upload utility.',
        epilog='More information in the man page acron-creds(1).')
    creds_update_parser.set_defaults(func=creds_put)
    creds_update_parser_type = creds_update_parser.add_mutually_exclusive_group(required=True)
    creds_update_parser_type.add_argument(
        '-f', '--file', metavar='FILE', help='Path to the keytab to upload.')
    creds_update_parser_type.add_argument(
        '-g', '--generate', action='store_true', help='Generate the keytab.')

    # acron creds delete [--help]
    creds_delete_parser = creds_subparsers.add_parser(
        'delete',
        help='delete credentials, if they exist',
        description='Acron credentials deletion utility.',
        epilog='More information in the man page acron-creds(1).')
    creds_delete_parser.set_defaults(func=creds_delete)


    # acron jobs [--help]
    jobs_parser = main_subparsers.add_parser(
        'jobs',
        help='jobs management utility',
        description='Acron jobs management utility.',
        epilog='More information in the man page acron-jobs(1).')
    jobs_subparsers = jobs_parser.add_subparsers(title='Commands', metavar='<command>', help='description')
    jobs_subparsers.required = True

    # acron jobs show (--job_id JOB_ID|--all) [--project PROJECT] [--help]
    jobs_get_parser = jobs_subparsers.add_parser(
        'show',
        help='show job definition',
        description='Acron jobs information utility.',
        epilog='More information in the man page acron-jobs(1).')
    jobs_get_parser.set_defaults(func=jobs_get)
    jobs_get_parser.add_argument(
        '-j', '--job_id', metavar='JOB_ID',
        help='The unique job identifier corresponding to the job to show.')
    jobs_get_parser.add_argument(
        '-p', '--project', metavar='PROJECT',
        help='Name of the project to manage, if the project is shareable.')

    # acron jobs create --schedule 'CRON' --target HOST --command 'CMD' [--description 'DESCR']
    #                   [--project PROJECT] [--help]
    jobs_post_parser = jobs_subparsers.add_parser(
        'create',
        help='create a job.',
        description='Acron jobs creation utility.',
        epilog='More information in the man page acron-jobs(1).')
    jobs_post_parser.set_defaults(func=jobs_post)
    jobs_post_parser.add_argument(
        '-s', '--schedule', metavar="'CRON'", required=True,
        help='The schedule of the job, quoted, crontab format.')
    jobs_post_parser.add_argument(
        '-t', '--target', metavar='FQDN', required=True,
        help='The node on which the job will be executed, FQDN.')
    jobs_post_parser.add_argument(
        '-c', '--command', metavar="'CMD'", required=True,
        help='The command to launch, quoted.')
    jobs_post_parser.add_argument(
        '-d', '--description', metavar="'DESCR'",
        help='A description that will be displayed when the job is shown.')
    jobs_post_parser.add_argument(
        '-p', '--project', metavar='PROJECT',
        help='Name of the project to manage, if the project is shareable.')

    # acron jobs update --job_id JOB_ID [--schedule 'CRON'] [--target HOST] [--command 'CMD']
    #                   [--description 'DESCR'] [--project PROJECT]  [--help]
    jobs_put_parser = jobs_subparsers.add_parser(
        'update',
        help='modify a job.',
        description='Acron jobs modification utility.',
        epilog='More information in the man page acron-jobs(1).')
    jobs_put_parser.set_defaults(func=jobs_post)
    jobs_put_parser.add_argument(
        '-j', '--job_id', metavar='JOB_ID', required=True,
        help='The unique job identifier corresponding to the job to show.')
    jobs_put_parser.add_argument(
        '-s', '--schedule', metavar="'CRON'",
        help='The schedule of the job, quoted, crontab format.')
    jobs_put_parser.add_argument(
        '-t', '--target', metavar='FQDN',
        help='The node on which the job will be executed, FQDN.')
    jobs_put_parser.add_argument(
        '-c', '--command', metavar="'CMD'",
        help='The command to launch, quoted.')
    jobs_put_parser.add_argument(
        '-d', '--description', metavar="'DESCR'",
        help='A description that will be displayed when the job is shown.')
    jobs_put_parser.add_argument(
        '-p', '--project', metavar='PROJECT',
        help='Name of the project to manage, if the project is shareable.')

    # acron jobs delete (--job_id JOB_ID|--all) [--project PROJECT] [--help]
    jobs_delete_parser = jobs_subparsers.add_parser(
        'delete',
        help='delete a job',
        description='Acron jobs deletion utility.',
        epilog='More information in the man page acron-jobs(1).')
    jobs_delete_parser.set_defaults(func=jobs_delete)
    jobs_delete_parser_jobid = jobs_delete_parser.add_mutually_exclusive_group(required=True)
    jobs_delete_parser_jobid.add_argument(
        '-j', '--job_id', metavar='JOB_ID',
        help='The unique job identifier corresponding to the job to delete.')
    jobs_delete_parser_jobid.add_argument(
        '-a', '--all', action='store_true',
        help='Delete all jobs in the project.')
    jobs_delete_parser.add_argument(
        '-p', '--project', metavar='PROJECT',
        help='Name of the project to manage, if the project is shareable.')

    # acron jobs enable (--job_id JOB_ID|--all) [--project PROJECT] [--help]
    jobs_enable_parser = jobs_subparsers.add_parser(
        'enable',
        help='enable a disabled job.',
        description='Acron jobs enabling utility.',
        epilog='More information in the man page acron-jobs(1).')
    jobs_enable_parser.set_defaults(func=jobs_enable)
    jobs_enable_parser_jobid = jobs_enable_parser.add_mutually_exclusive_group(required=True)
    jobs_enable_parser_jobid.add_argument(
        '-j', '--job_id', metavar='JOB_ID',
        help='The unique job identifier corresponding to the job to enable.')
    jobs_enable_parser_jobid.add_argument(
        '-a', '--all', action='store_true',
        help='Enable all jobs in the project.')
    jobs_enable_parser.add_argument(
        '-p', '--project', metavar='PROJECT',
        help='Name of the project to manage, if the project is shareable.')

    # acron jobs disable (--job_id JOB_ID|--all) [--project PROJECT] [--help]
    jobs_disable_parser = jobs_subparsers.add_parser(
        'disable',
        help='disable a job without deleting it.',
        description='Acron jobs disabling utility.',
        epilog='More information in the man page acron-jobs(1).')
    jobs_disable_parser.set_defaults(func=jobs_disable)
    jobs_disable_parser_jobid = jobs_disable_parser.add_mutually_exclusive_group(required=True)
    jobs_disable_parser_jobid.add_argument(
        '-j', '--job_id', metavar='JOB_ID',
        help='The unique job identifier corresponding to the job to disable.')
    jobs_disable_parser_jobid.add_argument(
        '-a', '--all', action='store_true',
        help='Disable all jobs in the project.')
    jobs_disable_parser.add_argument(
        '-p', '--project', metavar='PROJECT',
        help='Name of the project to manage, if the project is shareable.')

    return main_parser.parse_args()

def sanity_checks(args):
    """ perfmon sanity checks on given inputs """
    if "schedule" in args and args.schedule is not None:
        try:
            check_schedule(args.schedule)
        except AssertionError:
            sys.stderr.write('The schedule field has the wrong format. \nOnly numbers, /, * and, are allowed, with 5 fields separated by one space.\n')#pylint:disable=line-too-long
            sys.exit(1)

    if "target" in args and args.target is not None:
        try:
            check_target(args.target)
        except AssertionError:
            sys.stderr.write('The target field has contains bad characters. Allowed are: "a-z", "A-Z", "0-9:, ".", "-" and "_" \n')#pylint:disable=line-too-long
            sys.exit(1)

    if "command" in args and args.command is not None:
        try:
            check_command(args.command)
        except AssertionError:
            sys.stderr.write('The command field has contains bad characters. Allowed are word characters, numbers, spaces, backslash and any of "-+_/><&()[]$~"\'*.!#@;:"].\n')#pylint:disable=line-too-long
            sys.exit(1)

    if "description" in args and args.description is not None:
        try:
            check_description(args.description)
        except AssertionError:
            sys.stderr.write('The description field has contains bad characters. Allowed are charactes, numbers, spaces, "+", "-", "." and "," \n')#pylint:disable=line-too-long
            sys.exit(1)

def main():
    '''
    Launcher.

    :returns: 0 if successful, a positive integer in case of failure or error
    '''
    args = input_parser()
    sanity_checks(args)
    login()
    return args.func(args)
