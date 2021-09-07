# (C) Copyright 2021 CERN
#
# This software is distributed under the terms of the GNU General Public Licence version 3
# (GPL Version 3), copied verbatim in the file "COPYING" /copied verbatim below.
#
# In applying this licence, CERN does not waive the privileges and immunities granted to it
# by virtue of its status as an Intergovernmental Organization or submit itself to any jurisdiction.
#
"""
  Checking the regular expressions
"""

__author__ = 'Ulrich Schwickerath (CERN)'
__credits__ = ['Ulrich Schwickerath (CERN)']
__maintainer__ = 'Ulrich Schwickerath (CERN)'
__email__ = 'ulrich.schwickerath@cern.ch'
__status__ = 'Development'

import sys
from acron.utils import check_schedule  # pylint: disable=import-error


def check_expressions():
    """ Validates several regex"""
    print("Checking the following expressions")

    failed = 0
    valid_expressions = [
        '* * * * *',
        '* * 2,3,4 * *',
        '2-8,5 * * * *',
        '*/10 * * * *',
        '2-8,*/10 * * * *',
        '0 0 * * FRI',
        '*/50 * * OCT Mon']
    for my_expr in valid_expressions:
        print("Validating %s" % my_expr)
        try:
            check_schedule(my_expr)
        except AssertionError:
            failed += 1
            print("ERROR: This was not supposed to fail!!!")
    wrong_expressions = ['* * *',
                         '* * 2,3 4 * *',
                         '4- * * * *',
                         '* 25 * * *',
                         '61 * * * *'
                         '* * 33 * *',
                         '* * * 13 *',
                         '*/0 * * * *',
                         '* * 0 * *',
                         '* * * 0 *',
                         '* * * Okt Mon']
    for my_expr in wrong_expressions:
        print("Checking  %s" % my_expr)
        try:
            check_schedule(my_expr)
            print("ERROR: This was not supposed to work!!!")
            failed += 1
        except AssertionError:
            print("It failed, good!")
    return failed


if __name__ == '__main__':
    sys.exit(check_expressions())
