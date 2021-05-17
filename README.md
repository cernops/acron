# Authenticated cron service

Acron is a centralised, authenticated service which allows users to periodically execute tasks on arbitrary target nodes to which they have access.

This project contains client and server tools, including different open source backend examples, serving as a replacement for the
legacy acron service

### Concepts
The goal of the redesign is to get rid of legacy protocols such as ARC, as well as dependencies on AFS which is deprecated.

### Requirements
* Provide the same functionality as the legacy acron service
* Eliminate legacy home grown components and base it on free Open Source tools
* Improve security
* Improve redundancy of the service

### General Design
The client tools are used to
* manage user credentials
* manage user authenticated cron entries

## Client - Server API
The communication between the client and the server happens exclusively over HTTPS using an API.
Authentication is done using kerberos5. The kerberos principal determins the user name to act on.

Requests always only act on the files of the authenticated users. Eg a delete on the /jobs endpoint will only delete the crontab entries of the corresponding user.
### /creds endpoint

* PUT: create or update user credentials
* GET: get the *status* of the stored credentials (exists, is valid, ...). Does not return the credentials itself.
* DELETE: delete stored credentials if they exist.
Credentials are stored with a name which makes it unique to the authenticated users.
Users can only access credentials which match their principal.

### /jobs endpoint
Acts on all jobs of the authenticated user.

* POST: create a new job. The job ID is automatically generated in a unique way.
* GET:  get the list of *all* acron jobs for that user
* DELETE: delete *all* the jobs in the project

#### /jobs/<jobid>
Acts on a specific job of the authenticated user. Throw an error if the job does not exist.

* PUT: update a named job. Fail if the job does not exist
* GET:  get the named job of the authenticated user
* DELETE: delete the named  job of the authenticated user

## Feature request: Ability to share job management
This is a feature request we got from a specific user community. They would like to be able to allow other users (defined by an LDAP group name) to also manage the acron entries of a specific user.

* The user in question has to agree to this feature
* The user in question has to be able to specify the a list of groups or users.
* Members of the LDAP group have to be able to query the list of jobs of the specific users. They need to know (and pass on) the name of the user in the request.
* Members of the LDAP group have to be able to create jobs on behalf of that user.
* Members of the LDAP group have to be able to update jobs on behalf of that user.
* Members of the LDAP group have to be able to delete jobs on behalf of that user.

Implementing this feature requires that the service is able to manage and store user profiles by principle name. The user
settings have to be stored on the acron master and need to be shared between the masters.

### /users endpoint
Access to /users should be restricted for admins only.

* GET:  get list of all users
* DELETE: delete all users

#### /users/<username>
Allows to manipulate user profiles and settings.

* PUT: create the user username if it doesn't already exist
* GET: get the details of the named user
* DELETE: delete the named user
