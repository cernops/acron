#!/usr/bin/env bash
#
# (C) Copyright 2021 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
# Acron Smoke Test (client-side)
#
# __author__ = Rodrigo Bermudez Schettino (CERN)'
# __credits__ = ['Rodrigo Bermudez Schettino (CERN)']
# __maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
# __email__ = 'rodrigo.bermudez.schettino@cern.ch'
# __status__ = 'Development'

timestamp() {
    # Default timezone to date's built-in format
    # mac outputs code e.g. CET whereas Linux as time difference +08
    local timezone=%Z
    # Set timezone to contents of system file if exists
    if [ -f /etc/timezone ]; then
        timezone=$(cat /etc/timezone)
    fi
    date "+%a %b %d %I:%M:%S %p $timezone %Y"
}

fancy_echo() {
    echo
    timestamp
    echo "[TEST] ==> $1"
    echo
}

err_exit() {
    echo
    echo "ERROR: $1"
    echo
    exit 1
}

summary() {
    fancy_echo "All tests passed"

}

welcome() {
    fancy_echo "Acron Smoke Test (client-side)"
}
