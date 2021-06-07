#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Server-side tools and functions'''

import functools
import inspect
import logging
import os
import re
from socket import gethostbyaddr
from flask import current_app, request
import ldap3
from acron.errors import ERRORS
from acron.exceptions import KdestroyError, KinitError
from acron.utils import fqdnify as ext_fqdnify
from acron.utils import krb_init_keytab as ext_krb_init_keytab
from acron.utils import krb_destroy as ext_krb_destroy

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)',
               'Nacho Barrientos (CERN)', 'David Moreno Garcia (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'


def dump_args(func):
    '''
    Dumps the functions parameters to the debug logger.

    :param func: the function to dump the args from
    :returns:    func with arguments dumping functionality added

    source: https://stackoverflow.com/a/6278457
    '''
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        '''
        Adds the args dump functionality.
        '''
        func_args = inspect.signature(func).bind(*args, **kwargs).arguments
        func_args_str = ', '.join('{} = {!r}'.format(*item) for item in func_args.items())
        logging.debug('%s.%s ( %s )', func.__module__, func.__qualname__, func_args_str)
        return func(*args, **kwargs)
    return wrapper


# pylint: disable=R0914
@dump_args
def _ldap_groups_expansion(groups, server, base, user_regexp, group_regexp):
    '''
    Expands a group or list of groups.

    :param groups: group or list of groups
    :returns:      a set containing the users, empty if the group is empty
    '''
    if isinstance(groups, str):
        groups = [groups]
    elif ((isinstance(groups, list) and not all(isinstance(x, str) for x in groups))
          or not isinstance(groups, list)):
        raise ValueError('Please provide a string or a list of strings.')
    groups_to_process = list(set(groups))
    processed_groups = set()
    users = set()
    while groups_to_process:
        next_group = groups_to_process.pop(0)
        processed_groups.add(next_group)
        group_filter = '(&(objectClass=group)(CN=%s))' % next_group
        ldap_client = ldap3.Connection(server, auto_bind=True)
        ldap_client.search(base, group_filter, attributes=['member'])
        if ldap_client.entries and 'member' in ldap_client.entries[0]:
            for result in ldap_client.entries[0].member.values:
                user = re.match(user_regexp, result)
                group = re.match(group_regexp, result)
                if user is not None:
                    users.add('%s' % user.group(1))
                elif group is not None:
                    if group.group(1) not in processed_groups:
                        groups_to_process.append(group.group(1))
    ldap_client.unbind()
    return users


@dump_args
def ldap_groups_expansion(groups):
    '''
    Expands a group or list of groups.

    :param groups: group or list of groups
    :returns:      a set containing the users, empty if the group is empty
    '''
    users = _ldap_groups_expansion(groups,
                                   current_app.config['LDAP_SERVER'],
                                   current_app.config['LDAP_BASE'],
                                   current_app.config['LDAP_USER_REGEXP'],
                                   current_app.config['LDAP_GROUP_REGEXP'])
    return users


@dump_args
def get_remote_hostname():
    '''
    Performs a DNS lookup on remote_addr of the current context.

    :returns:            the hostname corresponding to request's remote host
    :raises SystemError: raises an exception if the process call fails
    '''
    lookup = gethostbyaddr(request.remote_addr)
    return lookup[0] + '(' + request.remote_addr + ')'


@dump_args
def default_log_line_request():
    '''
    Generates a formatted string for logging on requests.

    :returns: a formatted string
    '''
    return 'User {username} ({host}) requests {method}'.format(
        username=request.remote_user, host=get_remote_hostname(), method=request.method)


@dump_args
def fqdnify(hostname):
    '''
    Make sure a hostname is an FQDN.

    :param host: hostname to check
    :returns:    the same host if already an FQDN or the hostname with the domain appended if not
    '''
    return ext_fqdnify(hostname, current_app.config['DOMAIN'])


@dump_args
def krb_init_keytab(keytab, principal):
    '''
    Request a Kerberos TGT with the given keytab and principal.

    :param keytab:      the keytab to use
    :param principal:   the principal to use with the keytab
    :returns:           OK if the initialization succeeded
    :raises KinitError: raises an exception if the initialization failed
    '''
    try:
        ext_krb_init_keytab(keytab, principal)
    except KinitError as error:
        logging.debug('Kerberos initialization with keytab failed. %s', error)
        raise KinitError
    return ERRORS['OK']


@dump_args
def krb_destroy(cachefile):
    '''
    Delete the Kerberos TGT.

    :raises KdestroyError: raises an exception if the destruction failed
    '''
    try:
        ext_krb_destroy(cachefile)
    except KdestroyError as error:
        logging.debug('Kerberos destruction failed. %s', error)
        raise KdestroyError
    return ERRORS['OK']


@dump_args
def create_parent(path):
    '''
    Check if the parent directory exists and create it if not.

    :param path: path of the leaf object
    '''
    path_parent = os.path.abspath(os.path.join(path, os.pardir))
    if not os.path.exists(path_parent):
        logging.debug('%s does not exist, creating.', path_parent)
        os.makedirs(path_parent, 0o0775)
