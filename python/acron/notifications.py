#
# (C) Copyright 2021 CERN
#
# This software is distributed under the terms of the GNU General Public Licence version 3
# (GPL Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Notifications module'''

__author__ = 'Rodrigo Bermudez Schettino (CERN)'
__credits__ = ['Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import logging
import yaml


with open('/etc/acron/server.config', 'r') as config_file:
    CONFIG = yaml.safe_load(config_file)


def email_user(username, subject, body):
    '''
    Send an email to a user

    :param username: name of the user
    :param subject:  subject of the e-mail
    :param body:     body of the e-mail
    '''
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = 'no-reply@{}'.format(CONFIG['DOMAIN'])
    msg['To'] = '{}@{}'.format(username, CONFIG['DOMAIN'])
    msg.attach(MIMEText(body))
    smtp_obj = smtplib.SMTP('localhost')

    logging.debug(f'Sending email to user {username} with subject:')
    logging.debug(f'{subject}\n')
    logging.debug(f'Body:\n{body}')

    smtp_obj.sendmail(msg['From'], msg['To'], msg.as_string())
