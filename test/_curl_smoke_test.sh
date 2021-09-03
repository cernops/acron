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

# HTTP response status codes
readonly STATUS_FOUND=200
readonly STATUS_PERMANENT_REDIRECT=308
readonly STATUS_BAD_REQUEST=400
readonly STATUS_NOT_FOUND=404

readonly PERMS_READ_ONLY='ro'
readonly PERMS_READ_WRITE='rw'
readonly PERMS_DELETE='delete'

_curl_request() {
    # Constants
    local -r curl_opts=(--header "Content-Type: application/json" --negotiate -u:)
    # Arguments
    local -r msg="$1"
    local -r http_method="$2"
    local -r url="$3"

    # Default value
    local extra_args=()

    if [ $# -gt 3 ]; then
        local -r all_args=("$@")
        # Contains all arguments after the third one (url)
        # Helpful in case any data is passed
        local -r extra_args=("${all_args[@]:3}")
    fi

    fancy_echo "$msg"
    set -o xtrace
    # Use extra args only if set
    # https://stackoverflow.com/a/7577209
    LAST_CURL_OUTPUT=$(curl "${curl_opts[@]}" -X"${http_method}" "$url" ${extra_args[@]+"${extra_args[@]}"})
    set +o xtrace
}

_verify_http_response_status_code() {
    if [ "$LAST_CURL_OUTPUT" = "$1" ]; then
        fancy_echo "Received status code $LAST_CURL_OUTPUT matches expected one $1"
        return
    fi

    err_exit "HTTP response status code $LAST_CURL_OUTPUT does not equal $1"
}

_grant_perms_in_project() {
    # Pass $PERMS_DELETE as second parameter to delete share

    # Arguments
    local -r api_url="$1"
    local -r perms="$2"
    local -r user="$3"
    # Variables
    # Default values
    local method="$PUT"
    local extra_args=()

    if [ $# -gt 3 ]; then
        local -r all_args=("$@")
        # Contains all arguments after the third one (user)
        # Helpful in case any data is passed
        local -r extra_args=("${all_args[@]:3}")
    fi

    if [ "$perms" = "$PERMS_DELETE" ]; then
        method="$DELETE"
        _curl_request "Deleting project share from user $user from own project" \
            "$method" "${api_url}/project/user/$user" ${extra_args[@]+"${extra_args[@]}"}
        return
    fi

    _curl_request "Granting user $user $perms permissions to own project" \
        "$PUT" "${api_url}/project/user/$user?project_permissions=$perms" ${extra_args[@]+"${extra_args[@]}"}
}

_chaos_test_wrong_api() {
    fancy_echo "Testing using wrong API $WRONG_API_URL should fail"

    _curl_request "Getting sessions status" "$GET" "${WRONG_API_URL}/session/status" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_NOT_FOUND"

    _curl_request "Getting creds status" "$GET" "${WRONG_API_URL}/creds" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_NOT_FOUND"

    _curl_request "Getting jobs" "$GET" "${WRONG_API_URL}/jobs" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_NOT_FOUND"
}

_chaos_test_unauthenticated() {
    fancy_echo "Unauthenticated requests should fail"

    _curl_request "Logging out" "$GET" "${CURRENT_API_URL}/session/logout" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_FOUND"

    _curl_request "Getting sessions status" "$GET" "${CURRENT_API_URL}/session/status" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_FOUND"

    _curl_request "Getting creds status" "$GET" "${CURRENT_API_URL}/creds" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_PERMANENT_REDIRECT"

    _curl_request "Getting jobs" "$GET" "${CURRENT_API_URL}/jobs" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_PERMANENT_REDIRECT"
}

_chaos_test_create_job() {
    local -r schedule="*/10 * * * *"
    local -r description="Testing curl job custom name"
    local -r target="lxplus-acron.cern.ch"
    local -r command="echo 'works'"
    local -r job_id='asdf;asdfasd\$asdf\$9'

    fancy_echo "Testing creation of job with wrong custom job name"
    curl -G -H "Content-Type: application/json" --negotiate -u: -XPOST https://acron-rundeck01.cern.ch:8443/v1/jobs/ --data-urlencode "schedule=$schedule" --data-urlencode "description=$description" --data-urlencode "target=$target" --data-urlencode "command=$command" --data-urlencode "job_id=$job_id" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_BAD_REQUEST"
}

_chaos_test_share_project() {
    # dummyymmud is a fictive name which we asume it doesn't exist on the DB.
    local -r user="dummyymmud"
    local -r empty_str=''

    fancy_echo "Share project with wrong arguments or user should fail"

    fancy_echo "Sharing project with non-existing $user"
    _grant_perms_in_project "$CURRENT_API_URL" "$PERMS_READ_ONLY" "$user" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_BAD_REQUEST"

    fancy_echo "Sharing project with $SHARE_PROJECT_USER with blank permissions"
    _grant_perms_in_project "$CURRENT_API_URL" "$empty_str" "$SHARE_PROJECT_USER" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_BAD_REQUEST"

    fancy_echo "Sharing project with blank user and permissions"
    _grant_perms_in_project "$CURRENT_API_URL" "$empty_str" "$empty_str" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_NOT_FOUND"

    fancy_echo "Deleting project share from blank user"
    _grant_perms_in_project "$CURRENT_API_URL" "$PERMS_DELETE" "$empty_str" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_NOT_FOUND"

    fancy_echo "Deleting project share from non-existing user $user"
    _grant_perms_in_project "$CURRENT_API_URL" "$PERMS_DELETE" "$user" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_NOT_FOUND"

    fancy_echo "Deleting project share from project admin $user"
    _grant_perms_in_project "$CURRENT_API_URL" "$PERMS_DELETE" "$user" "${HTTP_CODE_ONLY[@]}"
    _verify_http_response_status_code "$STATUS_NOT_FOUND"
}

_test_api_using_curl() {
    local -r api_url="$1"

    _curl_request "Logging in" "$POST" "${api_url}/session/login" --data '{"otp": '"$OTP"'}'
    _curl_request "Getting sessions status" "$GET" "${api_url}/session/status"
    _curl_request "Getting creds status" "$GET" "${api_url}/creds"
    _curl_request "Getting jobs" "$GET" "${api_url}/jobs"

    if [ "$api_url" = "$API_ZERO_URL" ]; then
        return
    fi

    fancy_echo "Testing $API_VERSION_ONE-specific features"
    _curl_request "Getting projects" "$GET" "${api_url}/projects"
    _curl_request "Getting own project" "$GET" "${api_url}/project"
    _curl_request "Getting users in own project" "$GET" "${api_url}/project/users"

    _grant_perms_in_project "$api_url" "$PERMS_READ_ONLY" "$SHARE_PROJECT_USER"
    _grant_perms_in_project "$api_url" "$PERMS_READ_WRITE" "$SHARE_PROJECT_USER"
    _grant_perms_in_project "$api_url" "$PERMS_DELETE" "$SHARE_PROJECT_USER"

    _curl_request "Delete own project" "$DELETE" "${api_url}/project"
}
