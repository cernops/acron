#
# (C) Copyright 2019-2021 CERN
#
# This  software  is  distributed  under  the  terms  of  the  GNU  General  Public  Licence  version  3
# (GPL  Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Setup file to create the acron packages'''

from setuptools import setup


setup(name='acron',
      version='0.14.4',
      description='Authenticated crontab service',
      author='Philippe Ganz (CERN)',
      author_email='philippe.ganz@cern.ch',
      maintainer='Rodrigo Bermudez Schettino (CERN)',
      maintainer_email='rodrigo.bermudez.schettino@cern.ch',
      url='https://gitlab.cern.ch/acron-devs/acron',
      download_url='https://gitlab.cern.ch/acron-devs/acron',
      license='GPL-3.0',
      platforms=['Linux'],
      packages=['acron',
                'acron.server',
                'acron.server.api',
                'acron.server.backend',
                'acron.server.backend.creds',
                'acron.server.backend.scheduler',
                'acron.client'],
      entry_points={
          'console_scripts': [
              'acron=acron.client:main',
          ], },
      )
