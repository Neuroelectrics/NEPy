"""
Test to the batch processDirectory function of nepy.
The test imports the ground truth to perform the asserts from test_data.py and asserts all the necessary data to create
a capsule and perform a Frida test.
In case you want to perform the test with different data:
    1. Add your files in nepy/tests/testfiles folder
    2. Modify the ground truth in test_data.py (See documentation)
In case you have modified the processDirectory function, then you might need to modify these test functions too.

2019 Neuroelectrics Barcelona
@author: R Sanchez (roser.sanchez@neuroelectrics.com)
"""

import os
import pytest

from nepy.frida.batch import processDirectory
from nepy.tests.test_data import easyTestData
from nepy.tests.test_data import nedfTestData
from nepy.tests.test_data import testpath


def test_batch():
    """
    It processes all the files in the testfiles directory. It checks that all the test data in the test_data.py
    directory is processed.
    :return: it should return a green tick! It works ;)
    """
    if os.path.isdir(testpath) is False:
        pytest.exit('The the -testfiles- folder path of your computer does not match with the one written '
                    'in test_data.py (testpath) ')

    processed, skipped = processDirectory(testpath, plotit=False)

    # With this assertion we check that batch processes all the files of the test data, given an directory.
    assert (len(processed)+len(skipped)) == (len(easyTestData) + 1 + len(nedfTestData))
    # The +1 is added since we also have the fake_easy file now in the directory.
