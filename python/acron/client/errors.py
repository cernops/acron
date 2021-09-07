#
# (C) Copyright 2021 CERN
#
# This software is distributed under the terms of the GNU General Public Licence version 3
# (GPL Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Client-side error handling'''

__author__ = 'Rodrigo Bermudez Schettino (CERN)'
__credits__ = ['Rodrigo Bermudez Schettino (CERN)', 'Philippe Ganz (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


import sys


class ServerError:
    '''
    Print server errors to stderr
    '''

    @staticmethod
    def error_no_access_job():
        '''
        Error message when user has no access to the project.
        '''
        ServerError.error_no_access(True)

    @staticmethod
    def error_no_access(job_related=False):
        '''
        Error message when user lacks access rights.
        :params job_related: Toggle to print project-related message
        '''
        sys.stderr.write(f'''You do not have access.
Please check that you have a valid Kerberos ticket,
that you are registered to the right service group
''')
        if job_related:
            sys.stderr.write(
                'and that you have access rights to the project.\n')

    @staticmethod
    def error_creds_not_found():
        '''
        Error message when user credentials were not found.
        '''
        sys.stderr.write('No credentials on the server.\n')

    @staticmethod
    def error_creds_expired():
        '''
        Error message when user credentials have expired.
        '''
        sys.stderr.write('''Your uploaded credentials are no longer valid.
They may have expired, or your password may have been changed recently.
Please update them using the "acron creds upload -g" command.
''')

    @staticmethod
    def error_user_not_found():
        '''
        Error message when the requested user can not be found.
        '''
        sys.stderr.write(
            'Incorrect user specified. Please check the username and try again.\n')

    @staticmethod
    def error_job_not_found():
        '''
        Error message when the requested job can not be found.
        '''
        sys.stderr.write(
            'This job does not exist. Please check the job name and try again.\n')

    @staticmethod
    def error_job_already_exists():
        '''
        Error message when the requested job already exists.
        '''
        sys.stderr.write(
            'This job id already exists. Please try using another job id and try again.\n')

    @staticmethod
    def error_project_not_found():
        '''
        Error message when the requested project can not be found.
        '''
        sys.stderr.write(
            'This project does not exist. Please create a job first to initialise the project.\n')

    @staticmethod
    def error_project_or_user_not_found():
        '''
        Error message when project or user could not be found.
        '''
        sys.stderr.write(
            '''Either the project or the user given could not be found.
Please check that both exist and retry.
Hint: To initialise a project, create a job first.\n''')

    @staticmethod
    def error_internal_server():
        '''
        Error message for internal server error.
        '''
        sys.stderr.write('''An internal server error occurred.
Please try later or contact technical support.\n''')

    @staticmethod
    def error_unknown(message):
        '''
        Error message when an unknown error occurred.

        :param message: raw message returned by the server
        '''
        sys.stderr.write('''An unknown error occurred, please try again or
contact the support with the following information:''')
        sys.stderr.write(message + '\n')
