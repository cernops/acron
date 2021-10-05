Name: python36-acron
Version: 0.14.4
Release: 1%{?dist}
License: GPLv3
URL: https://gitlab.cern.ch/acron-devs/acron
Source0: %{name}-%{version}.tgz
BuildRequires: bzip2
BuildRequires: python36-devel
BuildRequires: selinux-policy-devel
BuildRequires: zip
BuildArch: noarch
Provides: python(acron) = %{version}
Summary: Authenticated crontab service
Group: Development/Languages
%description
Authenticated crontab service


%package common
Conflicts: python-acron-common
Requires: gnupg2
Requires: python3-PyYAML
Summary: Common files for the authenticated crontab service
Group: Development/Languages
%description common
Provides the files common to both the server and the client side

%package server
Conflicts: python-acron-server
Requires: %{name}-common
Requires: httpd
Requires: httpd-devel
Requires: python3-devel
Requires: python3-flask
Requires: python3-flask-login
Requires: python3-ldap3
%if 0%{?el7}
Requires: mod_wsgi
%else
Requires: python3dist(mod-wsgi)
%endif
Requires: python3-requests
Requires: python3-memcached
Requires(pre): /usr/sbin/useradd
Requires(postun): /usr/sbin/userdel
Summary: Server side of the authenticated crontab service
Group: Development/Languages
%description server
Contains the API with projects, jobs and credentials handling. Also contains different backends for the scheduler and credential storage.
It is based on the Flask library and is thus developed in a rather modular fashion using blueprints and an app factory as launcher.
Configuration is stored in a separate Config class and can load parameters from config files.

%package server-creds-file
Conflicts: python-acron-server-creds-file
Conflicts: %{name}-server-creds-vault
Requires: %{name}-server
Summary: File credentials backend for the acron server
Group: Development/Languages
%description server-creds-file
Uses the native linux file management system as a storage for credentials

%package server-creds-file-selinux
Requires: %{name}-server-creds-file
Requires: selinux-policy-targeted
Summary: SELinux rules for the File backend.
Group: Development/Languages
%description server-creds-file-selinux
SELinux modules for File credentials storage backend

%package server-creds-vault
Conflicts: python-acron-server-creds-vault
Conflicts: %{name}-server-creds-file
Requires: %{name}-server
Summary: Vault credentials backend for the acron server
Group: Development/Languages
%description server-creds-vault
Uses Vault as a storage for credentials

%package server-scheduler-crontab
Conflicts: python-acron-server-scheduler-crontab
Conflicts: %{name}-server-scheduler-nomad
Conflicts: %{name}-server-scheduler-rundeck
Requires: %{name}-server
Summary: Crontab scheduler backend for the acron server
Group: Development/Languages
%description server-scheduler-crontab
Uses the native linux crontab utility as scheduler backend for the acron server

%package server-scheduler-nomad
Conflicts: python-acron-server-scheduler-nomad
Conflicts: %{name}-server-scheduler-crontab
Conflicts: %{name}-server-scheduler-rundeck
Requires: %{name}-server
Summary: Nomad scheduler backend for the acron server
Group: Development/Languages
%description server-scheduler-nomad
Uses Nomad as scheduler backend for the acron server

%package server-scheduler-rundeck
Conflicts: python-acron-server-scheduler-rundeck
Conflicts: %{name}-server-scheduler-crontab
Conflicts: %{name}-server-scheduler-nomad
Requires: %{name}-server
Summary: Rundeck scheduler backend for the acron server
Group: Development/Languages
%description server-scheduler-rundeck
Uses Rundeck as scheduler backend for the acron server

%package server-scheduler-rundeck-selinux
Conflicts: python-acron-server-scheduler-rundeck-selinux
Requires: %{name}-server-scheduler-rundeck
Requires: selinux-policy-targeted
Requires: rundeck
Obsoletes:  %{name}-selinux-server
Summary: SELinux rules for the Rundeck backend.
Group: Development/Languages
%description server-scheduler-rundeck-selinux
SELinux modules for tomcat/rundeck backend

%package client
Conflicts: python-acron-client
Requires: %{name}-common
Requires: bash-completion
Requires: krb5-workstation
Requires: python3-requests-gssapi
Summary: Client side of the authenticated crontab service
Group: Development/Languages
%description client
Contains the client tools to interact with the API


%prep
%setup -q -T -c -a 0


%build
ls -l
cd ./python; CFLAGS="%{optflags}" %{__python3} setup.py build; cd ..

cd ./selinux
ln -sf /usr/share/selinux/devel/Makefile
make
bzip2 *.pp


%install
mkdir -p %{buildroot}/%{_docdir}/acron/
install COPYING COPYRIGHT LICENSE %{buildroot}/%{_docdir}/acron

cd ./python; %{__python3} setup.py install --skip-build --root %{buildroot}; cd ..

mkdir -p %{buildroot}%{_libexecdir}/acron/
install ./usr/libexec/acron/*_creds %{buildroot}%{_libexecdir}/acron/
install ./usr/libexec/acron/ssh_run %{buildroot}%{_libexecdir}/acron/

mkdir -p %{buildroot}%{_libexecdir}/acron/rundeck
install ./usr/libexec/acron/rundeck/* %{buildroot}%{_libexecdir}/acron/rundeck/

mkdir -p %{buildroot}%{_sysconfdir}/acron/
install ./etc/acron/*.config %{buildroot}%{_sysconfdir}/acron/

mkdir -p %{buildroot}%{_sysconfdir}/acron/server/
install ./etc/acron/server/*.config %{buildroot}%{_sysconfdir}/acron/server/

mkdir -p %{buildroot}%{_sysconfdir}/acron/server/rundeck/
install ./etc/acron/server/rundeck/* %{buildroot}%{_sysconfdir}/acron/server/rundeck/

mkdir -p %{buildroot}%{_sysconfdir}/bash_completion.d/
install ./etc/bash_completion.d/* %{buildroot}%{_sysconfdir}/bash_completion.d/

mkdir -p %{buildroot}%{_sysconfdir}/sudoers.d/
install ./etc/sudoers.d/* %{buildroot}%{_sysconfdir}/sudoers.d/

mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d/
install ./etc/logrotate.d/* %{buildroot}%{_sysconfdir}/logrotate.d/

mkdir -p %{buildroot}%{_mandir}/man1/
install ./man/man1/* %{buildroot}%{_mandir}/man1/

mkdir -p %{buildroot}%{_localstatedir}/log/acron/
mkdir -p %{buildroot}%{_localstatedir}/log/acron_service/

mkdir -p %{buildroot}%{_localstatedir}/acron/creds/

pwd

mkdir -p %{buildroot}%{_bindir}/
install ./usr/bin/acrontab2acron %{buildroot}%{_bindir}

mkdir -p %{buildroot}%{_datadir}/acron/
install ./usr/share/acron/acron_gpg_key.pub %{buildroot}%{_datadir}/acron/

mkdir -p %{buildroot}%{_datadir}/acron/rundeck/
install ./usr/share/acron/rundeck/* %{buildroot}%{_datadir}/acron/rundeck/

mkdir -p %{buildroot}%{_datadir}/acron/nomad/
install ./usr/share/acron/nomad/* %{buildroot}%{_datadir}/acron/nomad/

mkdir -p  %{buildroot}/usr/share/selinux/targeted/
install ./selinux/acron_scheduler_rundeck.pp.bz2  %{buildroot}/usr/share/selinux/targeted/
install ./selinux/acron_creds_file.pp.bz2  %{buildroot}/usr/share/selinux/targeted/

mkdir -p %{buildroot}/var/lib/rundeck/libext/
cd ./var/lib/rundeck/libext/
zip -r %{buildroot}/var/lib/rundeck/libext/rundeck-acron-node-executor-plugin-1.2.0.zip rundeck-acron-node-executor-plugin-1.2.0
cd -


%define add_service_account                                                                     \
  echo "  Checking for acron system user..."                                                    \
  /usr/bin/id acron >/dev/null 2>&1 ||                                                          \
  (echo "  user acron does not exist, adding now." && /usr/sbin/useradd -r -d /usr/share/acron acron)

%pre server
%{add_service_account}


%define httpd_refresh                                    \
  echo "  Reloading httpd..."                            \
  if [[ $(/usr/bin/pgrep httpd) ]]; then                 \
    /usr/bin/systemctl reload httpd;                     \
  else                                                   \
    /usr/bin/systemctl start httpd;                      \
  fi

%post server
%{httpd_refresh}

%post server-creds-file
%{httpd_refresh}

%post server-creds-vault
%{httpd_refresh}

%post server-scheduler-crontab
%{httpd_refresh}

%post server-scheduler-nomad
%{httpd_refresh}

%post server-scheduler-rundeck
%{httpd_refresh}

%post server-creds-file-selinux
/usr/sbin/setsebool -P rsync_export_all_ro 1
. /etc/selinux/config;
( semodule -n -i /usr/share/selinux/targeted/acron_creds_file.pp.bz2 -s targeted 2>&1;
  [ "${SELINUXTYPE}" == "targeted" ] && selinuxenabled && load_policy;
)

%post server-scheduler-rundeck-selinux
/usr/sbin/setsebool -P rsync_export_all_ro 1
. /etc/selinux/config;
( semodule -n -i /usr/share/selinux/targeted/acron_scheduler_rundeck.pp.bz2 -s targeted 2>&1;
  [ "${SELINUXTYPE}" == "targeted" ] && selinuxenabled && load_policy;
)
echo "  SElinux changes for /var/lib/rundeck"
/usr/sbin/semanage fcontext -a -t tomcat_cache_t "/var/lib/rundeck/(.*)?"
/usr/sbin/restorecon -rv /var/lib/rundeck


%preun server-creds-file-selinux
if [ $1 -eq 0 ]; then
    . /etc/selinux/config;
    ( semodule -n -r acron_creds_file 2>&1;
      [ "${SELINUXTYPE}" == "targeted" ] && selinuxenabled && load_policy;
    );
fi

%preun server-scheduler-rundeck-selinux
if [ $1 -eq 0 ]; then
    . /etc/selinux/config;
    ( semodule -n -r acron_scheduler_rundeck 2>&1;
      [ "${SELINUXTYPE}" == "targeted" ] && selinuxenabled && load_policy;
    );
fi


%files common
%{python3_sitelib}/acron/
%exclude %{python3_sitelib}/acron/client/
%exclude %{python3_sitelib}/acron/server/
%attr(0755, -, -) %dir %{_sysconfdir}/acron/
%attr(0755, -, -) %dir %{_libexecdir}/acron/
%attr(0755, -, -) %dir %doc %{_docdir}/acron/
%attr(0644, -, -) %doc %{_docdir}/acron/*
%attr(0755, -, -) %dir %{_datadir}/acron/

%files server
%{python3_sitelib}/acron-*
%{python3_sitelib}/acron/server/
%exclude %{python3_sitelib}/acron/server/backend/creds/file*
%exclude %{python3_sitelib}/acron/server/backend/creds/vault*
%exclude %{python3_sitelib}/acron/server/backend/scheduler/crontab*
%exclude %{python3_sitelib}/acron/server/backend/scheduler/nomad*
%exclude %{python3_sitelib}/acron/server/backend/scheduler/rundeck*
%attr(0640, acron, acron) %config(noreplace) %{_sysconfdir}/acron/server.config
%attr(0750, acron, acron) %dir %{_sysconfdir}/acron/server/
%attr(0750, acron, acron) %dir %{_localstatedir}/log/acron/
%attr(0750, apache, apache) %dir %{_localstatedir}/log/acron_service/
%attr(0750, acron, acron) %{_libexecdir}/acron/ssh_run
%attr(0644, root, root)%config %{_sysconfdir}/logrotate.d/*

%files server-creds-file
%{python3_sitelib}/acron/server/backend/creds/file*
%attr(0750, acron, acron) %dir %{_localstatedir}/acron/
%attr(0750, acron, acron) %dir %{_localstatedir}/acron/creds/
%attr(0640, acron, acron) %config(noreplace) %{_sysconfdir}/acron/server/file.config
%attr(0440, -, -)%config(noreplace) %{_sysconfdir}/sudoers.d/apache_acron_file_backend
%attr(0750, acron, acron) %{_libexecdir}/acron/delete_creds
%attr(0750, acron, acron) %{_libexecdir}/acron/get_creds
%attr(0750, acron, acron) %{_libexecdir}/acron/store_creds

%files server-creds-file-selinux
%attr(0644, -, -) /usr/share/selinux/targeted/acron_creds_file.pp.bz2

%files server-creds-vault
%{python3_sitelib}/acron/server/backend/creds/vault*
%attr(0640, acron, acron) %config(noreplace) %{_sysconfdir}/acron/server/vault.config

%files server-scheduler-crontab
%{python3_sitelib}/acron/server/backend/scheduler/crontab*
%attr(0640, acron, acron) %config(noreplace) %{_sysconfdir}/acron/server/crontab.config

%files server-scheduler-nomad
%{python3_sitelib}/acron/server/backend/scheduler/nomad*
%attr(0640, acron, acron) %config(noreplace) %{_sysconfdir}/acron/server/nomad.config
%attr(0750, acron, acron) %{_datadir}/acron/nomad/
%attr(0440, -, -)%config(noreplace)%{_sysconfdir}/sudoers.d/nomad_acron_ssh

%files server-scheduler-rundeck
%{python3_sitelib}/acron/server/backend/scheduler/rundeck*
%attr(0640, acron, acron) %config(noreplace) %{_sysconfdir}/acron/server/rundeck.config
%attr(0640, acron, acron) %config(noreplace) %{_sysconfdir}/acron/server/rundeck/*
%attr(0750, acron, acron) %{_datadir}/acron/rundeck/
%attr(0440, -, -)%config(noreplace)%{_sysconfdir}/sudoers.d/rundeck_acron_ssh
%attr(0644, rundeck, rundeck) %{_sharedstatedir}/rundeck/libext/rundeck-acron-node-executor-plugin-*
%attr(0755, acron, acron) %dir %{_libexecdir}/acron/rundeck/
%attr(0750, acron, acron) %{_libexecdir}/acron/rundeck/*

%files server-scheduler-rundeck-selinux
%attr(0644, -, -) /usr/share/selinux/targeted/acron_scheduler_rundeck.pp.bz2

%files client
%{python3_sitelib}/acron-*
%{python3_sitelib}/acron/client/*
%attr(0644, -, -) %config(noreplace) %{_sysconfdir}/acron/client.config
%attr(0644, -, -) %config(noreplace) %{_sysconfdir}/bash_completion.d/acron
%attr(0644, -, -) %{_mandir}/man1/*
%attr(0755, -, -) %{_bindir}/acron
%attr(0755, -, -) %{_bindir}/acrontab2acron
%attr(0644, -, -) %{_datadir}/acron/acron_gpg_key.pub


%changelog
* Thu  Sep 30 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.14.4-1
- Update SELinux rules for gpg access to file
- change location of the service logs to log/acron_service
- update logrotate rules accordingly
* Fri Sep 24 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.14.3-2
- GPG patches to make the server work on CS8
- do the take over by project
- add script for manual take over of jobs
- update logrotate script
* Wed Sep 15 2021 Rodrigo Bermudez Schettino <rodrigo.bermudez.schettino@cern.ch> - 0.14.1-1
- do not send messages for successful jobs with no output
- bump version
* Wed Sep 1  2021 Rodrigo Bermudez Schettino <rodrigo.bermudez.schettino@cern.ch> - 0.14.0-1
- set custom job names optionally
- add command to delete project
- add command to revoke project share
- notify users via email about project shares
- fix bug in commands with single quotes
- increase user-friendliness (e.g., warn user if not member of required e-group)
- Extend allowed characters in job's command
- improve error handling
- improve documentation
* Tue Jul 27 2021 Rodrigo Bermudez Schettino <rodrigo.bermudez.schettino@cern.ch> - 0.13.0-2
- fix bug on server by creating required intermediate directories for new users
* Wed Jul 21 2021 Rodrigo Bermudez Schettino <rodrigo.bermudez.schettino@cern.ch> - 0.13.0-1
- add projects command with man page and bash completion
- bump API version from v0 to v1
- add smoke test
* Fri Jul 9 2021 Rodrigo Bermudez Schettino <rodrigo.bermudez.schettino@cern.ch> - 0.12.4-4
- improve error handling when aborting log in
- add bash completion for projects
- fix bug in clients while handling server responses for jobs
* Tue Jul 6 2021 Rodrigo Bermudez Schettino <rodrigo.bermudez.schettino@cern.ch> - 0.12.4-3
- refactoring to improve code maintainability
- fix bug in initialization of kerberos credentials
* Fri Jun 18 2021 Rodrigo Bermudez Schettino <rodrigo.bermudez.schettino@cern.ch> - 0.12.4-2
- improve sanity checks for command and description in acron jobs update and create
- generalise credential treatment
- improve script headers and documentation
- improve robustness of bash scripts
* Thu Apr 22 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.12.3-1
- use crontab in quartz format to set the schedule
* Thu Apr 15 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.12.2-1
- correct treatment of ssh connection errors
* Thu Apr 15 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.12.1-1
- replace non - ASCII characters as this causes issues for some users
- silence KVNO script
* Wed Mar 24 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.12.0-1
- support for multiple realms in the client
- add support for custumn ktutil-like call
- update and document list of allowed characters in command
* Wed Mar 24 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.11.14-2
- enforce the usage of -f for MIT ktutil on all OS
- ensure correct construction of keytab file location
* Thu Mar 11 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.11.13-1
- capture case where no description is given at job creation time
- allow environment variables in the keytab path location
* Wed Mar 3 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.11.12-1
- allow e-mails in commands
* Thu Feb 25 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.11.11-1
- update dependencies for C8 support
* Mon Feb 22 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.11.10-1
- bug fix in creds upload
- move logging outside the loop to capture authentication errors
* Mon Feb 01 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.11.9-1
- better capture None errors when creating jobs
- bug fixes
* Mon Feb 01 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.11.8-1
- allow additional characters in the command
- introduce idle session configuration timout
- implement retry if the node was bad
* Wed Jan 27 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.11.7-1
- redo the ssh call using the env parameter of Popen
- sanity checks on user input
* Fri Jan 22 2021 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.11.6-1
- change credential cache file for each user
* Tue Dec 8 2020 Pablo Saiz pablo.saiz@cern.ch>                     - 0.11.5-2
- Using setuptools and pylint
* Thu Nov 12 2020 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.11.4-2
- add support for C8
* Fri Sep 18 2020 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.11.4-1
- add grouping in regular expression
* Fri Sep 04 2020 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.11.3-1
- bugfix release
- add sanity checks on schedule field
* Tue May 05 2020 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.11.2-2
- add support for 2FA on the endpoints
- add support for memcached
- bug fixes
* Thu Feb 27 2020 Philippe Ganz <philippe.ganz@cern.ch> - 0.10.2-1
- Add health_check capability to Rundeck backend
* Fri Feb 21 2020 Philippe Ganz <philippe.ganz@cern.ch> - 0.10.1-1
- Add target transform capability
- Change python3 shebang
* Tue Feb 18 2020 Philippe Ganz <philippe.ganz@cern.ch> - 0.10.0-1
- Add description to job parameters
- Client clean up
- Improve documentation
* Thu Feb 13 2020 Philippe Ganz <philippe.ganz@cern.ch> - 0.9.0-1
- Add support for auth through external script
- Restructure configuration keys
- Add missing SELinux rules
- Fix bug in jobs API
* Thu Feb 06 2020 Philippe Ganz <philippe.ganz@cern.ch> - 0.8.1-1
- Add failover capabilities to Rundeck backend
- Fix bug in client
- Add missing SELinux rules
* Tue Jan 28 2020 Philippe Ganz <philippe.ganz@cern.ch> - 0.8.0-1
- Add system endpoint
- Fix bugs in Rundeck backend
- Fix bug in client
* Fri Jan 17 2020 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.7.2-1
- Catch 500 errors
- Allow to override the server by setting the env variable ACRON_SERVER
- Add missing SELinux rules
* Tue Jan 14 2020 Philippe Ganz <philippe.ganz@cern.ch> - 0.7.1-1
- Add missing SELinux rules
- Fix bug in client
* Wed Dec 18 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.7.0-1
- Release is not taking the Python version into account any more
- Jobs update accepts changes in single fields
- Logging executions in ssh_run
- Add missing SELinux rules
- Improve documentation
- Add more general exception catching on client
- Fix minors typos and style
* Fri Nov 22 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.6.2-py3
- Add missing SELinux rules
* Thu Nov 21 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.6.1-py3
- Update SELinux packages
- Fix various bugs
* Tue Nov 19 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.6.0-py3
- Add projects endpoint
- Add new functions to the scheduler interface
- Change jobs show option in client
- Fix various bugs
* Mon Oct 28 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.5.1-py3
- Fix various bugs
* Mon Oct 07 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.5.0-py3
- Split API and backend layers
- Remove pip dependencies, use rpm requiements instead
* Thu Aug 29 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.4.2-py3
- Fix bug in Rundeck backend
* Fri Aug 16 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.4.1-py3
- Remove unused function in client
* Thu Aug 15 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.4.0-py3
- Add option to manage other projects
- Add functionality to pause and unpause jobs
* Fri Aug 09 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.3.10-py3
- Fix bug in client output
- Port project to python 3
* Thu Aug 08 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.3.9-1
- Improve client output
- Fix bug in Rundeck backend
* Tue Aug 06 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.3.8-1
- Notification e-mails sent on non empty output and non-zero result
- Make job IDs backend independant, now correctly incremented
- Improve client output
* Wed Jul 31 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.3.7-2
- Fix a bug in the spec file
* Wed Jul 31 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.3.7-1
- Deploy the Rundeck plugin with the API
- Fix bug in Rundeck plugin
* Fri Jul 26 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.3.6-1
- Add bash completion to the client tools
- Fix bugs on client side
* Fri Jun 28 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.3.5-1
- Fix typos and minor bugs
* Mon Jun 24 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.3.4-1
- Fix typos and minor bugs
* Tue Jun 18 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.3.3-1
- Warn the user if he has no access to the service
* Fri Jun 14 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.3.2-1
- Mail user on failure
* Thu Apr 25 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.3.1-1
- Make server output more understandable for Rundeck backend
- Fix bug in the ssh runner
* Tue Apr 16 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.3.0-1
- Add File backend
- Add pre step to add service account
- Make selinux package specific to rundeck package
- Move utils functions from acron.server to acron package
* Thu Apr 04 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.2.2-1
- Add documentation
* Mon Apr 01 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.2.1-1
- Fix bug in Rundeck backend and improve code
* Fri Mar 22 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.2.0-1
- Split package into backend plugins
- Add Rundeck backend
* Fri Mar 15 2019 Ulrich Schwickerath <ulrich.schwickerath@cern.ch> - 0.1.0-2
- Add selinux stuff for Rundeck backend
* Fri Feb 22 2019 Philippe Ganz <philippe.ganz@cern.ch> - 0.1.0-1
- Alpha release
