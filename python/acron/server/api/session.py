#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''System routines submodule'''

import logging
from time import time
import json
import requests
from flask import Blueprint, current_app, jsonify, request, redirect, url_for
from flask_login import login_user, UserMixin, logout_user
from acron.server.utils import dump_args

__author__ = 'Ulrich Schwickerath (CERN)'
__credits__ = ['Ulrich Schwickerath (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Ulrich Schwickerath (CERN)'
__email__ = 'ulrich.schwickerath@cern.ch'
__status__ = 'Development'


# Blueprint storing all routes and function calls
BP_SESSION = Blueprint('session', __name__)

class User(UserMixin):
    ''' flusk-login User class implementation '''
    def __init__(self):
        ''' initialise locals '''
        self.is_authenticated = False
        self.auth_timestamp = 0
        self.id = None #pylint: disable=invalid-name

    def is_authenticated(self):#pylint: disable=method-hidden
        ''' override inherited method '''
        return self.is_authenticated

    def set_authenticated(self, status):
        ''' set the authentication status '''
        self.is_authenticated = status

def verify_yubicode(username, yubicode):
    ''' verify the yubikey code transmitted
        return authentication time stamp if succees,
        else zero '''
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "username": username,
        "yubicode": yubicode
    }
    result = 0
    try:
        try:
            yubicode_url = current_app.config['YUBICODE_URL']
        except KeyError:
            logging.error("Config Error: Yubicode validation url is not defined")
            return 0
        response = requests.post(yubicode_url,
                                 data=json.dumps(data),
                                 headers=headers, verify=True)
        if response.status_code == 200 and response.content == b"true":
            result = int(time())
    except Exception as error: #pylint: disable=broad-except
        logging.error("Yubicode error: %s", str(error))
    logging.debug("Yubicode auth returns %d", result)
    return result

def verify_otp(username, otp):
    ''' verify the OTP code transmitted
        returns the authentication time stamp if succees,
        else zero '''
    headers = {
        "Content-Type": "text/plain"
    }
    result = 0
    try:
        try:
            otp_url = current_app.config['OTP_URL']+"/"+username+"/validate"
        except KeyError:
            logging.error("Config Error: OTP validation url is not defined")
            return 0
        response = requests.post(
            otp_url, data=str(otp), headers=headers, verify=True)
        if response.status_code == 200:
            try:
                res = response.json()['success']
                if res:
                    result = int(time())
            except KeyError:
                logging.error('OTP: received unexpected response')
    except Exception as error: #pylint: disable=broad-except
        logging.error("OTP error: %s, response code: %d\n", str(error), response.status_code)
    logging.debug("OTP auth returns %d", result)
    return result

@dump_args
@BP_SESSION.route('/login', methods=['POST'])
def login():
    ''' Initiate authentication '''
    yubicode = None
    otp = None
    username = request.remote_user
    logging.debug("user name: %s endpoint: %s url: %s",
                  username, request.endpoint, request.url)
    if username is None:
        return "User name is not defined. Login failed"
    if request.method == 'POST':
        if not current_app.config['ENABLE_2FA'] or (
                int(time())-current_app.user_auth.getauth(username)) < current_app.ttl:
            user = User()
            user.id = username #pylint: disable=invalid-name
            login_user(user)
            return redirect(url_for(request.endpoint))
        try:
            result = request.get_data().decode("utf-8")
            logging.debug(result)
            data = json.loads(result)
        except Exception as failed: #pylint: disable=broad-except
            logging.error(failed)
        try:
            yubicode = data['yubicode']
        except (KeyError, UnboundLocalError):
            try:
                otp = data['otp']
            except (KeyError, UnboundLocalError):
                return jsonify(isError=True)
        current_app.user_auth.setauth(username, 0)
        # verify the transmitted codes
        if yubicode is not None:
            auth_timestamp = verify_yubicode(username, yubicode)
        if otp is not None:
            auth_timestamp = verify_otp(username, otp)
        current_app.user_auth.setauth(username, auth_timestamp)
        return jsonify(AuthTimestamp=auth_timestamp)
    else:
        return 'Bad method.\n'

@BP_SESSION.route('/logout', methods=['GET'])
def logout():
    ''' log the user out '''
    logout_user()
    username = request.remote_user
    current_app.user_auth.setauth(username, 0)
    return 'Logged out\n'

@BP_SESSION.route('/status', methods=['GET'])
def login_status():
    ''' get login status for current user '''
    username = request.remote_user
    status = False
    if current_app.config['ENABLE_2FA']:
        if int(time())-current_app.user_auth.getauth(username) < current_app.ttl:
            status = True
    else:
        status = True
    return jsonify(loggedIn=status)
