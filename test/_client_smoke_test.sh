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

readonly JOB_ARGUMENTS=(--command 'ls' --schedule '*/30 * * * *' --target 'lxplus-acron.cern.ch' --description "smoke_test_job")

_test_creds_using_client() {
    fancy_echo "Testing creds using acron client"

    fancy_echo "Checking status of acron's credentials"
    acron creds status

    # Calls here are disabled because keytab generation throws an error when scripted
    #
    # fancy_echo "Deleting acron's credentials, if they exist"
    # acron creds delete
    # fancy_echo "Generating new acron credentials and uploading them"
    # acron creds upload --generate
}

_test_jobs_using_client() {
    fancy_echo "Testing jobs using acron client"

    fancy_echo "Show acron jobs (requires login using 2FA)"
    acron jobs show

    fancy_echo "Create test job"
    local job_out
    # Save output to variable and also print it to console using tee
    job_out=$(acron jobs create "${JOB_ARGUMENTS[@]}" | tee /dev/tty)

    # Extract job id from server response
    # 1. Replace newlines with spaces to make string parsing easier
    # 2. Get second field from output using awk
    #    First field should be job description, second field should be job id
    # 3. Trim trailing ':' using cut
    local -r job_id=$(echo "$job_out" | tr '\n' ' ' | awk '{ print $2 }' | cut -d':' -f1)

    fancy_echo "Updating job $job_id"
    acron jobs update --job_id "$job_id" "${JOB_ARGUMENTS[@]}"

    fancy_echo "Creating job with custom job_id $CUSTOM_JOB_ID"
    acron jobs create --job_id "$CUSTOM_JOB_ID" "${JOB_ARGUMENTS[@]}"

    fancy_echo "Updating job with custom job_id $CUSTOM_JOB_ID"
    acron jobs update --job_id "$CUSTOM_JOB_ID" "${JOB_ARGUMENTS[@]}"

    fancy_echo "Disabling created job $job_id"
    acron jobs disable --job_id "$job_id"

    fancy_echo "Enabling created job $job_id"
    acron jobs enable --job_id "$job_id"

    fancy_echo "Enable all jobs"
    acron jobs enable --all

    fancy_echo "Disable all jobs"
    acron jobs disable --all
}

_test_projects_using_client() {
    fancy_echo "Testing projects using acron client"

    fancy_echo "Showing user's project"
    acron projects show

    fancy_echo "Showing all projects visible to user"
    acron projects show --all

    fancy_echo "Share project with user $SHARE_PROJECT_USER with read-only perms"
    acron projects share --user_id "$SHARE_PROJECT_USER"

    fancy_echo "Share project with user $SHARE_PROJECT_USER with write perms"
    acron projects share --user_id "$SHARE_PROJECT_USER" --write

    fancy_echo "Delete share project with user $SHARE_PROJECT_USER"
    acron projects share --user_id "$SHARE_PROJECT_USER" --delete

    fancy_echo "Delete $USER project"
    acron projects delete

    fancy_echo "Create job to trigger project creation for curl tests"
    local job_out
    # Save output to variable and also print it to console using tee
    acron jobs create "${JOB_ARGUMENTS[@]}"
}
