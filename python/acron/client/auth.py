#!/usr/bin/python3
#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''session management functions'''

import sys
import os
import re
import json
import requests
import gssapi
from requests_gssapi import HTTPSPNEGOAuth
from acron.constants import Endpoints, ReturnCodes
from .config import CONFIG


def get_user_from_principal():
    ''' Get the username from the current principal'''
    try:
        creds = gssapi.creds.Credentials(usage='initiate')
        principal = str(creds.name.display_as(creds.name.name_type))
        return principal.split('@')[0]
    except Exception as krb_error:  # pylint: disable=broad-except
        sys.stderr.write(
            "Kerberos ticket not found or expired. Exiting...\n")
        sys.stderr.write(
            "The error returned was \"%s\"\n" % str(krb_error))
        sys.stderr.write(
            "\nPlease run kinit and try again.\n")
        sys.exit(1)

def read_secret(length):
    ''' read the 2FA secret from stdin '''
    secret = sys.stdin.readlines(1)[0].rstrip()
    if len(secret) != length:
        print("Invalid secret entered %s" % secret)
        return None
    return secret


def otp_secret(secret):
    ''' check if secret can be a OTP '''
    valid = re.compile(r'\d+')
    if secret is not None and len(secret) == 6 and valid.match(secret):
        return '{"otp":"' + secret + '"}'
    return None


def yubi_secret(secret):
    ''' check if secret can be a yubicode '''
    valid = re.compile(r'\w+')
    if secret is not None and len(secret) == 44 and valid.match(secret):
        return '{"yubicode":"' + secret + '"}'
    return None


def ask_for_secret():
    ''' dialog to ask for the secret'''
    username = get_user_from_principal()
    secret = None
    while secret is None:
        print("Your 2nd factor (%s):" % username)
        try:
            chars = sys.stdin.readlines(1)[0].rstrip()
            if len(chars) == 6 or len(chars) == 44:
                if len(chars) == 6:
                    secret = otp_secret(chars)
                if len(chars) == 44:
                    secret = yubi_secret(chars)
                if secret is not None:
                    return secret
            print('\nNo or invalid secret entered.')
        except KeyboardInterrupt:
            # Print empty line
            print('')
            sys.exit(0)


def check_login_status():
    ''' check if the user is logged into the server '''
    # check login status
    path = CONFIG['ACRON_SERVER_FULL_URL'] + \
        Endpoints.SESSION_TRAILING_SLASH + 'status'
    response = requests.get(path, auth=HTTPSPNEGOAuth(),
                            verify=CONFIG['SSL_CERTS'])
    if response.status_code == 200:
        return response.json()['loggedIn']
    if response.status_code == 401:
        return response.text
    return False


def login_user():
    ''' log in the user '''
    secret = ask_for_secret()
    path = CONFIG['ACRON_SERVER_FULL_URL'] + \
        Endpoints.SESSION_TRAILING_SLASH + 'login'
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(path,
                             data=secret,
                             headers=headers,
                             auth=HTTPSPNEGOAuth(),
                             verify=CONFIG['SSL_CERTS'])
    if response.status_code == 200:
        try:
            answer = response.json()
            if 'isError' in answer:
                return 0
            return response.json()['AuthTimestamp']
        except json.decoder.JSONDecodeError:
            sys.stderr.write("%s" % response.text)
            sys.exit(1)
    return 0


def login():
    ''' check session status and login the user if needed '''
    # check logged user
    if os.environ['USER'] != get_user_from_principal():
        print('WARNING: Kerberos Principal does not match the logged in username')
    # check login status
    if check_login_status():
        return ReturnCodes.OK
    authtime = login_user()
    if authtime > 0:
        return ReturnCodes.OK
    sys.stderr.write('2FA authentication has failed.\n')
    sys.exit(1)
