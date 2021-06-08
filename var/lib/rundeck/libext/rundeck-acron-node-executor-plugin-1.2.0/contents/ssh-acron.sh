#!/usr/bin/bash
#
# (C) Copyright 2019-2020 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
# Acron SSH executor script for Rundeck backend
#
# __author__ = 'Philippe Ganz (CERN)'
# __credits__ = ['Philippe Ganz (CERN)', 'Ulrich Schwickerath (CERN)', 'Rodrigo Bermudez Schettino (CERN)']
# __maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
# __email__ = 'rodrigo.bermudez.schettino@cern.ch'
# __status__ = 'Development'

if [ $# -lt 4 ]; then
  echo "Script requires 4 parameters in the following order: job_id, username, hostname, command" >&2
  exit 1
fi

# Parse arguments
JOB_ID=$1
shift
USER=$1
shift
HOST=$1
shift
CMD=$*

# random delay (0..1s) to make it work with parallel exec
sleep "$(bc <<< "scale=2; $(printf '0.%02d' $(( RANDOM % 100)))")"

sudo -u acron /usr/libexec/acron/ssh_run "$JOB_ID" "$USER" "$HOST" "$CMD"
