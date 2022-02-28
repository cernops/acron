#
# (C) Copyright 2019-2021 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Various functions needed across the acron module'''

import os
import getpass
import re
import logging
from subprocess import Popen, PIPE
from acron.exceptions import GPGError, KdestroyError, KlistError, KinitError, KTUtilError

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)',
               'Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


def fqdnify(hostname, domain):
    '''
    Make sure a hostname is an FQDN.

    :param hostname: hostname to check
    :param domain:   the domain the host belongs to
    :returns:        the same host if already an FQDN or
                     the hostname with the domain appended if not
    '''
    host = re.match(r'([A-Za-z0-9_-]+).' + domain, hostname)
    if host is None:
        return hostname + '.' + domain
    return hostname


def get_current_user():
    '''
    Retrieve the user currently running the shell

    :returns: the current user
    '''
    return getpass.getuser()


def gpg_key_exist(gpg_binary, key_name):
    '''
    Check if the public acron key exists in the local gpg keyring.

    :param gpg_binary: path to the gpg binary to use
    :param key_name:   name of the acron key to use
    :returns:          a boolean
    '''
    with Popen([gpg_binary, '--list-keys', key_name],
               universal_newlines=True, stdout=PIPE, stderr=PIPE) as process:

        process.communicate()
        if process.returncode != 0:
            return False
        return True


def gpg_add_public_key(gpg_binary, key_path):
    '''
    Add the public acron key to the local gpg keyring.

    :param gpg_binary: path to the gpg binary to use
    :param key_path:   path to the key to import
    :raises GPGError:  if the import fails
    '''
    with Popen([gpg_binary, '--import', key_path],
               stdout=PIPE, stderr=PIPE) as process:
        _, err = process.communicate()
        if process.returncode != 0:
            raise GPGError(err)


def gpg_encrypt_file(raw_file, result, gpg_binary, key_name):
    '''
    Encrypts a file using the local gpg keyring.

    :param raw_file:   file to decrypt
    :param result:     resulting file
    :param gpg_binary: path to the gpg binary to use
    :param key_name:   name of the acron key to use
    :raises GPGError:  if the encryption fails
    '''
    with Popen([gpg_binary, '--yes', '--batch', '--always-trust',
                '--recipient', key_name,
                '--output', result,
                '--encrypt', raw_file],
               universal_newlines=True, stdout=PIPE, stderr=PIPE) as process:
        _, err = process.communicate()
        if process.returncode != 0:
            raise GPGError(err)


def gpg_decrypt_file(encrypted_file, result, gpg_binary, gpg_home, gpg_passphrase_file):
    '''
    Decrypts an encrypted file using the local gpg keyring.

    :param encrypted_file:      the file to decrypt
    :param result:              path to the resulting file
    :param gpg_binary:          path to the gpg binary to use
    :param gpg_home:            path to gnupg database
    :param gpg_passphrase_file: path to the file containing the private key passphrase
    :raises GPGError:           if the decryption fails
    '''
    with Popen([gpg_binary, '--batch',
                '--pinentry-mode', 'loopback',
                '--homedir', gpg_home,
                '--passphrase-file', gpg_passphrase_file,
                '--output', result,
                '--decrypt', encrypted_file],
               universal_newlines=True, stdout=PIPE, stderr=PIPE) as process:
        _, err = process.communicate()
        if process.returncode != 0:
            raise GPGError(err)


def find_salt_mit(user, realm, password):
    '''
    Find the salt for a principal and return it

    :param user:     the name of the user
    :param realm:    realm for the username
    :password:       the users password
    :output:         the salt or None
    '''
    execenv = os.environ.copy()
    cachefile = "/tmp/krb5cc_"+user+"_"+realm
    execenv["KRB5_TRACE"] = '/dev/stdout'
    execenv["KRB5CCNAME"] = cachefile

    with Popen(['kinit', user + '@' + realm],
               universal_newlines=True,
               stdout=PIPE,
               stderr=PIPE,
               stdin=PIPE, env=execenv) as process:
        out, err = process.communicate(input=password)
        if process.returncode != 0:
            raise KinitError(err)

    saltcheck = re.compile(r'salt "(.*)", ')
    salt = None
    for line in out.split("\n"):
        saltmatch = saltcheck.search(line)
        if saltmatch is not None:
            salt = saltmatch[1]
    os.unlink(cachefile)
    return salt


def find_kvno_mit(user, realm):
    '''
    Find the salt for a principal and return it

    :param user:     the name of the user
    :param realm :   realm for the username
    :output:         current key version number (KVNO)
    '''
    kvno = 1
    kvnocheck = re.compile(r'kvno = (\d+)')
    with Popen(['kvno', user + '@' + realm],
               universal_newlines=True,
               stdout=PIPE, stderr=PIPE) as process:
        out, _ = process.communicate()
        if process.returncode == 0:
            for line in out.split("\n"):
                kvnomatch = kvnocheck.search(line)
                if kvnomatch is not None:
                    kvno = kvnomatch[1]

    return kvno


def keytab_generator_custom(username, realm, enc_types, keytab, script):
    '''
    Generate a keytab for the given principal with heimdal

    :param username:    short username to use as Kerberos principal
    :param realm:       Kerberos domain
    :param enc_types:   encryption types to use for the keytab
    :param script:      string containing the full script call with arguments
    :param keytab:      path to the resulting file
    :param script:      custom script to be called
    :raises KTUtilError: if script fails to generate a keytab
    '''
    try:
        password = getpass.getpass('Password for ' + username + ': ')
    except getpass.GetPassWarning as getpasserr:
        raise IOError from getpasserr
    # resolve parameters in the command
    for encryption_type in enc_types:
        resolved = re.split(r'\s+',
                            script.replace(
                                "__keytab__", keytab).replace(
                                    "__username__", username).replace(
                                        "__realm__", realm).replace(
                                            "__enctype__", encryption_type))
        with Popen(resolved, universal_newlines=True,
                   stdout=PIPE,
                   stderr=PIPE,
                   stdin=PIPE) as process:
            _, err = process.communicate(password)
            if process.returncode != 0:
                raise KTUtilError(err)


def keytab_generator_heimdal(username, realm, enc_types, keytab):
    '''
    Generate a keytab for the given username with heimdal

    :param username:     short username to use as Kerberos username
    :param realm:        Kerberos realm
    :param enc_types:    encryption types to use for the keytab
    :param keytab:       path to the resulting file
    :raises KTUtilError: if ktutil fails to generate a keytab
    '''
    try:
        password = getpass.getpass('Password for ' + username + ': ')
    except getpass.GetPassWarning as getpasserr:
        raise IOError from getpasserr
    for encryption_type in enc_types:
        with Popen(['ktutil', '-k', keytab, 'add', '-V', '1', '-e',
                    encryption_type, username + '@' + realm],
                   universal_newlines=True,
                   stdout=PIPE,
                   stderr=PIPE,
                   stdin=PIPE) as process:
            _, err = process.communicate(password)
        if process.returncode != 0:
            raise KTUtilError(err)


def keytab_generator_mit(username, realm, enc_types, keytab):
    '''
    Generate a keytab for the given username with MIT

    :param username:     short username to use as Kerberos username
    :param realm:        Kerberos realm
    :param enc_types:    encryption types to use for the keytab
    :param keytab:       path to the resulting file
    :param opts:         additional options to be passed
    :raises KTUtilError: if ktutil fails to generate a keytab
    '''
    try:
        password = getpass.getpass('Password for ' + username + ': ')
    except getpass.GetPassWarning as getpasserr:
        raise IOError from getpasserr
    if os.path.isfile(keytab):
        ktutil_input = 'rkt ' + keytab + '\n'
    else:
        ktutil_input = ''
    # Let's see if we can get a salt and the kvno
    salt = find_salt_mit(username, realm, password)
    kvno = find_kvno_mit(username, realm)
    for encryption_type in enc_types:
        ktutil_input += 'add_entry -password -p ' + username + '@' + realm + ' '
        if salt is None:
            ktutil_input += '-k ' + \
                str(kvno) + ' -e ' + encryption_type + \
                ' -f \n' + password + '\n'
        else:
            ktutil_input += ('-k ' + str(kvno) + ' -s ' + salt + ' -e ' +
                             encryption_type + '\n' + password + '\n')
        ktutil_input += 'wkt ' + keytab + '\n' + 'exit'
    with Popen(['ktutil'],
               universal_newlines=True, stdin=PIPE, stdout=PIPE, stderr=PIPE) as process:
        _, err = process.communicate(ktutil_input)
        if process.returncode != 0:
            raise KTUtilError(err)


def keytab_generator(username, realm, enc_types, result, flavor='MIT', script=None):  # pylint: disable=too-many-arguments
    '''
    Generate a keytab for the given username.
    :param username:     short username to use as Kerberos username
    :param realm:        Kerberos realm
    :param enc_types:    encryption types to use for the keytab
    :param keytab:       path to the resulting file
    :param opt:          additional parameters to be passed
    :param flavor:       MIT or Heimdal
    :raises KTUtilError: if ktutil fails to generate a keytab
    '''
    if script is None:
        if flavor == 'MIT':
            keytab_generator_mit(username, realm, enc_types, result)
        else:
            if flavor == 'Heimdal':
                keytab_generator_heimdal(username, realm, enc_types, result)
            else:
                raise KTUtilError('Unknown kerberos client implementation')
    else:
        keytab_generator_custom(username, realm, enc_types, result, script)


def krb_check_keytab_heimdal(keytab):
    '''
    Verifies if a keytab is in a valid format.

    :param keytab:      the keytab to verify
    :raises KlistError: if the keytab is not valid
    '''
    with Popen(['ktutil', '-k', keytab, 'list'],
               universal_newlines=True, stdout=PIPE, stderr=PIPE) as process:
        out, err = process.communicate()
        if process.returncode != 0:
            raise KlistError(err)
        return out


def krb_check_keytab_mit(keytab):
    '''
    Verifies if a keytab is in a valid format.

    :param keytab:      the keytab to verify
    :raises KlistError: if the keytab is not valid
    '''
    with Popen(['klist', '-kt', keytab],
               universal_newlines=True, stdout=PIPE, stderr=PIPE) as process:
        out, err = process.communicate()
        if process.returncode != 0:
            raise KlistError(err)
        return out


def krb_check_keytab(keytab, flavor='MIT'):
    '''
    Verifies if a keytab is in a valid format.
    :param keytab:      the keytab to verify
    :param flavor:      MIT or Heimdal
    :returns            a unique list of realms in the keytab
    :raises KlistError: if the keytab is not valid
    '''
    if flavor == 'MIT':
        out = krb_check_keytab_mit(keytab)
    else:
        if flavor == 'Heimdal':
            out = krb_check_keytab_heimdal(keytab)
        else:
            raise KlistError('Unknown kerberos client implementation')
    match_realm = re.compile(r'@([A-Z\.\-\_]+)')
    realms = []
    for line in out.split('\n'):
        try:
            realm = match_realm.search(line)[1]
            if not realm in realms:
                realms.append(realm)
        except (IndexError, TypeError):
            pass
    return realms


def krb_init_keytab(keytab, principal, cachefile=None):
    '''
    Request a Kerberos TGT with the given keytab and principal.

    :param keytab:      the keytab to use
    :param principal:   the principal to use with the keytab
    :raises KinitError: if the initialization failed
    :param cachefile:   the full path to the cache file name to be used
    '''
    cmd = ['kinit', '-kt', keytab]
    if cachefile:
        cmd += ['-c', cachefile]
        try:
            logging.debug(
                'Trying to remove cachefile located at %s...', cachefile)
            os.unlink(cachefile)
        except FileNotFoundError as _:
            logging.debug('File %s doesn\'t exist. It will be automatically created next',
                          cachefile)

    cmd += [principal]

    with Popen(cmd, universal_newlines=True, stdout=PIPE, stderr=PIPE) as process:
        _, err = process.communicate()
        if process.returncode != 0:
            raise KinitError(err)

def krbcc_is_valid(cachefile=None):
    '''
    check credential cache file, either the default one or the one given
    Returns:
       True: if the cache file is valid
       False: cache file does not exist or is not valid
    '''
    cmd = ['klist']
    if cachefile:
        cmd += cachefile
    with Popen(cmd,
               universal_newlines=True, stdout=PIPE, stderr=PIPE) as process:
        _, _ = process.communicate()
        return process.returncode == 0

def krb_destroy(cachefile=None):
    '''
    Delete the Kerberos TGT.

    :raises KdestroyError: if the destruction failed
    :param cachefile:   the full path to the cache file name to be used
    '''
    cmd = ['kdestroy', '-q']
    if cachefile:
        cmd += ['-c', cachefile]

    with Popen(cmd,
               universal_newlines=True, stdout=PIPE, stderr=PIPE) as process:
        _, err = process.communicate()
        if process.returncode != 0:
            raise KdestroyError(err)


def replace_in_file(pattern, replace, source, destination=None):
    '''
    A Python implementation of sed to replace a pattern in an entire file.

    :param pattern:     regexp to match
    :param replace:     replacement string
    :param source:      path to the file to parse
    :param destination: path to the file to populate, writes back to source if empty
    :returns:           path to the resulting file

    source: https://stackoverflow.com/a/4427835/8141262
    '''
    if not destination:
        destination = source
    with open(source, "r") as sources:
        lines = sources.readlines()
    with open(destination, "w") as sources:
        for line in lines:
            sources.write(re.sub(pattern, replace, line))
    return destination


def check_schedule(schedule):
    """ check the format of the given schedule """
    sched_fields = schedule.split(' ')
    assert len(sched_fields) == 5
    months = ["JAN", "FEB", "MAR", "APR", "MAI", "JUN",
              "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    weekdays = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]

    minutes = r"[0-5]?\d"
    hours = r"[0-1]?\d|2[0-3]"
    day_of_month = r"[LW]|\?|0?[1-9]|[1-2][0-9]|3[0-1]|"+"|".join(weekdays)
    month = r"0?[0-9]|1[0,1]|"+"|".join(months)
    day_of_week = r"[LW]|\?|[1-7](#[1-7])?|"+"|".join(weekdays)
    basicfield = r"(\*|((%s)(-(%s))?))(\/(0\d|[1-9]\d?))?"
    field = r"(%s)(,(%s))*" % (basicfield, basicfield)
    total = []
    # Let's add an additional syntax check here, or even fix it.
    if day_of_month != '*':
        if day_of_week == '*':
            day_of_week = '?'
            logging.info('WARNING: replacing * by ? for day of week')
    if day_of_week not in ['*', '?']:
        if day_of_month == '*':
            day_of_month = '?'
            logging.info('WARNING: replacing * by ? for day of month')
    for term in minutes, hours, day_of_month, month, day_of_week:
        total.append(field % (term, term, term, term))
    valid_chars = re.compile(r"^"+r'\s'.join(total)+"$",
                             re.IGNORECASE)  # pylint: disable=no-member
    assert valid_chars.match(schedule)


def check_target(target):
    """ check if the target contains only valid characters"""
    valid_chars = re.compile(
        r'^[\w\-_\.]+$', flags=re.A)  # pylint: disable=no-member
    assert valid_chars.match(target)


def check_command(command):
    """ check if the command contains only valid characters"""
    valid_chars = re.compile(
        r'^[\s\w\-\+_\/\>\<\&\\\(\)\[\]\$\~\"\'\*\.\,\!\#\@\;\:\|]+$', flags=re.A)  # pylint: disable=no-member
    assert valid_chars.match(command.strip())


def check_description(description):
    """ check if the description contains only valid characters"""
    valid_chars = re.compile(r'^[\s\w\-\+_\.\,]+$')
    assert valid_chars.match(description.strip())


def check_projects(project):
    """ check if the project contains only valid characters"""
    valid_chars = re.compile(r'^[\s\w\-_\.]+$')
    assert valid_chars.match(project.strip())


def check_user_id(user):
    """ check if the user contains only valid characters"""
    valid_chars = re.compile(r'^[a-zA-Z]+$')
    assert valid_chars.match(user.strip())


def check_job_id(job_id):
    """ check if the job id contains only valid characters"""
    valid_chars = re.compile(
        r'^[a-zA-Z0-9\-]+$', flags=re.A)  # pylint: disable=no-member
    assert valid_chars.match(job_id)
