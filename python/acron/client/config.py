#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Acron client configuration'''

import os
import yaml

__author__ = 'Philippe Ganz (CERN)'
__credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)']
__maintainer__ = 'Philippe Ganz (CERN)'
__email__ = 'philippe.ganz@cern.ch'
__status__ = 'Development'


CONFIG_FILE_PATH = '/etc/acron/client.config'

with open(CONFIG_FILE_PATH, 'r') as config_file:
    CONFIG = yaml.safe_load(config_file)

try:
    ACRONSERVER = "https://"+os.environ['ACRON_SERVER']
except KeyError:
    ACRONSERVER = CONFIG['ACRON_SERVER']

CONFIG['ACRON_SERVER_FULL_URL'] = ACRONSERVER + ':' + \
    str(CONFIG['API_PORT']) + '/' + CONFIG['API_VERSION'] + '/'
