
#
# (C) Copyright 2021 CERN
#
# This software is distributed under the terms of the GNU General Public Licence version 3
# (GPL Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
'''Shared functions client-side'''

__author__ = 'Rodrigo Bermudez Schettino (CERN)'
__credits__ = ['Rodrigo Bermudez Schettino (CERN)']
__maintainer__ = 'Rodrigo Bermudez Schettino (CERN)'
__email__ = 'rodrigo.bermudez.schettino@cern.ch'
__status__ = 'Development'


import sys


def confirm(question):
    """Ask yes/no question and return answer.

    :param question: question as string to present to the user.
    :returns: Boolean representing user's confirmation

    Source: https://stackoverflow.com/a/3041990
    """
    yes_long = 'yes'
    yes_short = 'y'
    no_long = 'no'
    no_short = 'n'

    valid = {yes_long: True, yes_short: True, no_long: False, no_short: False}
    prompt = " [y/n] "

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if choice not in valid:
            sys.stdout.write(
                f"Please respond with '{yes_long}' or '{no_long}' " +
                f"(or '{yes_short}' or '{no_short}').\n")
        return valid[choice]
