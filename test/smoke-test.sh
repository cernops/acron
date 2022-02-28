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

# Shell options
set -o errexit
set -o pipefail
set -o nounset

# Export enabled shell options to subshells
# Documentation:
# https://www.gnu.org/software/bash/manual/html_node/Bash-Variables.html
export SHELLOPTS

###########
# Toggles #
###########
readonly YES='yes'
readonly NO='no'

# Set variables to default value only in case they are not set
readonly ENABLE_TEST_USING_CLIENT="${ENABLE_TEST_USING_CLIENT:-$YES}"
readonly ENABLE_TEST_USING_CURL="${ENABLE_TEST_USING_CURL:-$YES}"
readonly ENABLE_CHAOS_TEST_USING_CURL="${ENABLE_CHAOS_TEST_USING_CURL:-$YES}"

#############
# Constants #
#############

# Curl constants
readonly API_VERSION_ZERO='v0'
readonly API_VERSION_ONE='v1'
readonly SERVER_URL="https://acron-rundeck01.cern.ch:8443"
# shellcheck disable=SC2034
readonly HTTP_CODE_ONLY=(--silent --output /dev/null --write-out "%{http_code}\n")
# HTTP methods
readonly GET='GET'
# shellcheck disable=SC2034
readonly POST='POST'
# shellcheck disable=SC2034
readonly PUT='PUT'
# shellcheck disable=SC2034
readonly DELETE='DELETE'

# URLs
readonly API_ZERO_URL="${SERVER_URL}/${API_VERSION_ZERO}"
readonly API_ONE_URL="${SERVER_URL}/${API_VERSION_ONE}"

# shellcheck disable=SC2034
readonly WRONG_API_URL="${SERVER_URL}/v999"
readonly LEGACY_API_URL="$API_ZERO_URL"
readonly CURRENT_API_URL="$API_ONE_URL"

#############
# Variables #
#############

# Curl variable
# shellcheck disable=SC2034
declare LAST_CURL_OUTPUT=0
# Acron variables
# User should exist and should be different than own username.
declare SHARE_PROJECT_USER
declare CUSTOM_JOB_ID

# shellcheck disable=SC1091
source _utils.sh
# shellcheck disable=SC1091
source _client_smoke_test.sh
# shellcheck disable=SC1091
source _curl_smoke_test.sh

test_using_client() {
    fancy_echo "Testing acron client and API together using acron client"

    fancy_echo "Print acron --version"
    acron --version

    fancy_echo "Check version of installed rpms"
    rpm -qa | grep python3-acron

    _test_creds_using_client
    _test_jobs_using_client
    _test_projects_using_client
}

test_using_curl() {
    fancy_echo "Testing acron API using curl against URL $CURRENT_API_URL"

    _curl_request "Logging out" "$GET" "${CURRENT_API_URL}/session/logout"

    fancy_echo "Please enter an OTP to authenticate yourself using curl"
    while true; do
        # -r cleans input (backslashes, see shellcheck SC2162)
        # -p displays text in prompt
        read -rp "OTP > " OTP
        if ! [[ "$OTP" =~ ^[0-9]{6}$ ]]; then
            echo "Error. Input only accepts 6 integers. Try again…"
            continue
        fi
        break
    done

    # Test backwards compatibility of APIs
    fancy_echo "Testing legacy API using curl"
    _test_api_using_curl "$LEGACY_API_URL"

    # Log out in order to test login with current API
    _curl_request "Logging out" "$GET" "${CURRENT_API_URL}/session/logout"

    fancy_echo "Testing current API using curl"
    _test_api_using_curl "$CURRENT_API_URL"
}

chaos_test_using_curl() {
    fancy_echo "Chaos test"

    _chaos_test_wrong_api
    _chaos_test_unauthenticated
    _chaos_test_share_project
}

populate_variables() {
    local -r min_length=3
    local -r max_length=30
    local -r default_error_msg="Error. Input only accepts between $min_length and $max_length"
    local -r letters_error_msg="$default_error_msg letters. Try again…"
    local -r letters_numbers_hyphen_error_msg="$default_error_msg letters, numbers and hyphens. Try again…"

    fancy_echo "Populate smoke test variables"

    fancy_echo "Please enter the name of another user (other than yours).
This will be used to test sharing the project with this user."
    while true; do
        # -r cleans input (backslashes, see shellcheck SC2162)
        # -p displays text in prompt
        read -rp "SHARE_PROJECT_USER > " SHARE_PROJECT_USER
        if ! [[ "$SHARE_PROJECT_USER" =~ ^[a-zA-Z]{"$min_length","$max_length"}$ ]]; then
            echo "$letters_error_msg"
            continue
        fi
        break
    done

    fancy_echo "Please enter a custom job id.
This will be used to test creating a job with custom job id."
    while true; do
        # -r cleans input (backslashes, see shellcheck SC2162)
        # -p displays text in prompt
        read -rp "CUSTOM_JOB_ID > " CUSTOM_JOB_ID
        if ! [[ "$CUSTOM_JOB_ID" =~ ^[a-zA-Z0-9\-]{"$min_length","$max_length"}$ ]]; then
            echo "$letters_numbers_hyphen_error_msg"
            continue
        fi
        break
    done
}

smoke_test() {
    if [ "$ENABLE_TEST_USING_CLIENT" = "$YES" ]; then
        test_using_client
    fi
    if [ "$ENABLE_TEST_USING_CURL" = "$YES" ]; then
        test_using_curl
    fi
    if [ "$ENABLE_CHAOS_TEST_USING_CURL" = "$YES" ]; then
        chaos_test_using_curl
    fi
}

main() {
    welcome
    populate_variables
    smoke_test
    summary
}

main "$@"
