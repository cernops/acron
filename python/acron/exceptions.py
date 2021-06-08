#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Exception handling submodule'''

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'


class AcronError(Exception):
    '''
    Base exception class.
    '''

class AbortError(AcronError):
    '''
    User interrupted the command.
    '''

class ArgsMalformedError(AcronError):
    '''
    Method did get all parameters but at least one was not in a good format.
    '''

class ArgsMissingError(AcronError):
    '''
    Method did not get all required parameters.
    '''

class CredsError(AcronError):
    '''
    The creds backend failed to perform the requested task.
    '''

class GPGError(CredsError):
    '''
    GPG decryption failed.
    '''

class KerberosError(CredsError):
    '''
    General Kerberos error.
    '''

class KdestroyError(CredsError):
    '''
    Kerberos ticket could not be deleted.
    '''

class KinitError(CredsError):
    '''
    Keytab could not be used to get a Kerberos TGT.
    '''

class KlistError(CredsError):
    '''
    Keytab is not in a valid format.
    '''

class KTUtilError(CredsError):
    '''
    The ktutil utility failed to produce a keytab.
    '''

class CredsNoFileError(CredsError):
    '''
    The creds backend does not have the requested credentials.
    '''

class FileError(CredsError):
    '''
    The File creds backend failed to perform the requested task.
    '''

class VaultError(CredsError):
    '''
    The Vault creds backend failed to perform the requested task.
    '''

class SchedulerError(AcronError):
    '''
    The scheduler backend failed to perform the requested task.
    '''

class SSHFailureError(SchedulerError):
    '''
    An error happened whilst trying to launch the command with ssh.
    '''

class NotFoundError(SchedulerError):
    '''
    The resource was not found in the backend.
    '''

class JobNotFoundError(NotFoundError):
    '''
    The job was not found in the backend.
    '''

class ProjectNotFoundError(NotFoundError):
    '''
    The project was not found in the backend.
    '''

class NotShareableError(SchedulerError):
    '''
    Project can not be shared with other users.
    '''

class NoAccessError(SchedulerError):
    '''
    Project is shareable but the requesting user doesn't have access.
    '''

class CrontabError(SchedulerError):
    '''
    The Crontab scheduler backend failed to perform the requested task.
    '''

class NomadError(SchedulerError):
    '''
    The Nomad scheduler backend failed to perform the requested task.
    '''

class RundeckError(SchedulerError):
    '''
    The Rundeck scheduler backend failed to perform the requested task.
    '''
