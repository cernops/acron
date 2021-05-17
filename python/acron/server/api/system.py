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
from flask import Blueprint, current_app, jsonify, request
from acron.errors import ERRORS
from acron.exceptions import SchedulerError
from acron.server.http import http_response
from acron.server.utils import default_log_line_request, dump_args
from .jobs import get_scheduler_class

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'


# Blueprint storing all routes and function calls
BP_SYSTEM = Blueprint('system', __name__)


@dump_args
def backend_status(scheduler):
    '''
    Forward a backend status call to the backend

    :param scheduler: the scheduler backend
    :returns:         the backend's response
    '''
    try:
        response = scheduler.backend_status(current_app.config)
    except SchedulerError as error:
        logging.error('%s on /system/: %s', default_log_line_request(), error)
        return http_response(ERRORS['BACKEND_ERROR'])
    return jsonify(response)


@BP_SYSTEM.route('/', methods=['GET'])
def system():
    '''
    Launcher for system call
    GET: get the status of the backend
    '''
    scheduler_class = get_scheduler_class()
    logging.info('%s on /system/.', default_log_line_request())

    if request.method == 'GET':
        return backend_status(scheduler_class)

    logging.critical('%s on /system/: Method not allowed!', default_log_line_request())
    raise ValueError('Critical error: method not allowed!')
