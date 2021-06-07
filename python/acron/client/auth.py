#!/usr/bin/env python3
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
import json
import requests
import gssapi
from requests_gssapi import HTTPSPNEGOAuth
from acron.errors import ERRORS
from .config import CONFIG

def get_user_from_principal():
    ''' Get the user name from the current principal'''
    try:
        creds = gssapi.creds.Credentials(usage='initiate')
        principal = str(creds.name.display_as(creds.name.name_type))
        return principal.split('@')[0]
    except Exception as krb_error: #pylint: disable=broad-except
        print("Cannot access principal. Please run kinit.\n %s", krb_error)
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
    if secret is not None and len(secret) == 6:
        return '{"otp":"' + secret + '"}'
    return None

def yubi_secret(secret):
    ''' check if secret can be a yubicode '''
    if secret is not None and len(secret) == 44:
        return '{"yubicode":"' + secret + '"}'
    return None

def ask_for_secret():
    ''' dialog to ask for the secret'''
    username = get_user_from_principal()
    secret = None
    while secret is None:
        print("""Login for %s:

1. Authenticator App
2. Yubikey

Option (1-2): """ % username, end="")
        chars = sys.stdin.readlines(1)[0].rstrip()
        if len(chars) == 6:
            secret = otp_secret(chars)
        if len(chars) == 44:
            secret = yubi_secret(chars)
        if chars == '1':
            print('\nOTP: ', end="")
            secret = otp_secret(read_secret(6))
        if chars == '2':
            print('\nYubikey: ', end="")
            secret = yubi_secret(read_secret(44))
        if secret is not None:
            return secret
        print('\nNo or invalid secret entered.')

def check_login_status():
    ''' check if the user is logged into the server '''
    # check login status
    path = CONFIG['ACRON_SERVER_FULL_URL'] + 'session/status'
    response = requests.get(path, auth=HTTPSPNEGOAuth(), verify=CONFIG['SSL_CERTS'])
    if response.status_code == 200:
        return response.json()['loggedIn']
    return False

def login_user():
    ''' login the user '''
    secret = ask_for_secret()
    path = CONFIG['ACRON_SERVER_FULL_URL'] + 'session/login'
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
            print("%s" % response.text)
            sys.exit(1)
    return 0

def login():
    ''' check session status and login the user if needed '''
    # check logged user
    if os.environ['USER'] != get_user_from_principal():
        print('WARNING: Kerberos Principal does not match the logged in user name')
    # check login status
    if check_login_status():
        return  ERRORS['OK']
    authtime = login_user()
    if authtime > 0:
        return ERRORS['OK']
    print('2FA authentication has failed')
    sys.exit(1)
