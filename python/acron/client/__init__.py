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
from acron.utils import (check_schedule, check_target,
                         check_command, check_description,
                         check_projects, check_user_id, check_job_id)
from .auth import login
from .cli import (add_creds_subparsers, add_jobs_subparsers,
                  add_projects_subparsers, TITLE_COMMANDS,
                  METAVAR_COMMAND, HELP_DESCRIPTION)


__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)',
               'Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


def input_parser():
    '''
    Get user input and set flags.

    :returns: a dictionary containing the user's parameters
    '''
    # acron [--version] [--help]
    main_parser = argparse.ArgumentParser(
        description='Acron client. Please use the available subcommands.',
        epilog='For more information please check the man page, acron(1).')
    main_parser.add_argument(
        '-v', '--version', action='version',
        version=pkg_resources.require('acron')[0].version)
    main_subparsers = main_parser.add_subparsers(
        title=TITLE_COMMANDS, metavar=METAVAR_COMMAND, help=HELP_DESCRIPTION)
    main_subparsers.required = True

    add_creds_subparsers(main_subparsers)
    add_jobs_subparsers(main_subparsers)
    add_projects_subparsers(main_subparsers)

    return main_parser.parse_args()


def sanity_checks(args):
    """ perform sanity checks on given inputs """

    # The corresponding check_{target,schedule,...} functions should be defined
    inputs = ["schedule", "target", "job_id",
              "command", "description", "projects", "user_id"]

    # pylint: disable=unused-variable
    schedule_error_msg = 'Only numbers, /, * and, are allowed, with 5 fields separated by one space.\n'
    # pylint: disable=unused-variable
    target_error_msg = 'Allowed are: "a-z", "A-Z", "0-9", ".", "-" and "_"\n'
    # pylint: disable=unused-variable
    job_id_error_msg = 'Allowed are: "a-z", "A-Z", "0-9", and "-"\n'
    # pylint: disable=unused-variable
    command_error_msg = ('''Allowed are word characters, numbers, spaces, backslash''' +
                         '''and any of "-+_/><&()[]$~"'*.!#@;:|\n''')
    # pylint: disable=unused-variable
    description_error_msg = 'Allowed are characters, numbers, spaces, "+", "-", "." and "," \n'
    # pylint: disable=unused-variable
    projects_error_msg = 'Allowed are characters, numbers, spaces, "-" and "." \n'
    # pylint: disable=unused-variable
    user_id_error_msg = 'Allowed are characters only.\n'

    for input_name in inputs:
        if input_name in args and getattr(args, input_name) is not None:
            try:
                input_value = getattr(args, input_name)
                # Example of how it evaluates:
                #   check_target(args.target)
                globals()[f'check_{input_name}'](input_value)
            except AssertionError:
                # The locals call should insert the value of the variable specified.
                # Example:
                #  For input_name=target it should return the value of target_error_msg
                sys.stderr.write(f'''The {input_name} field has the wrong format.
    {locals()[f'{input_name}_error_msg']}''')
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
