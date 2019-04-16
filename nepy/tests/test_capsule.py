"""
Test to the capsule class of nepy.
The test imports the ground truth to perform the asserts from test_data.py and asserts all the necessary data to create
a capsule and perform a Frida test.
Since the capsule class just copies the information coming from the respective reader, it would be necessary to check
first fi the readers have passed the test. A hardcore dependency will be added in the future.
In case you want to perform the test with different data:
    1. Add your files in nepy/tests/testfiles folder
    2. Modify the ground truth in test_data.py (See documentation)
In case you have modified the capsule class, then you might need to modify these test functions too.

2019 Neuroelectrics Barcelona
@author: R Sanchez (roser.sanchez@neuroelectrics.com)
"""

import pytest
import numpy as np
import os
import datetime

from nepy.capsule.capsule import Capsule
from nepy.tests.test_data import easyTestData
from nepy.tests.test_data import nedfTestData
from nepy.tests.test_data import testpath


@pytest.fixture(scope='module')
def capsules():
    """
    Generating two different capsules to test: one from an .easy file and the other from nedf files.
    """
    if os.path.isdir(testpath) is False:
        pytest.exit('The the -testfiles- folder path of your computer does not match with the one written '
                    'in test_data.py (testpath) ')
    easy_filepath = os.path.join(testpath, str(easyTestData[list(easyTestData.keys())[0]]['filename']) + '.easy')
    nedf_filepath = os.path.join(testpath, str(nedfTestData[list(nedfTestData.keys())[0]]['filename']) + '.nedf')

    caps = {
        'easy': Capsule(easy_filepath),
        'nedf': Capsule(nedf_filepath)
    }  # Dictionary containing a capsule per test file.
    for file in caps:
        if caps[file].good_init is False:
            pytest.exit("File not found to create the capsule. Check that the file exists or the reader's tests.")

    return caps


def test_attributes(capsules):
    """
    We are creating another directory with the test data to test a capsule created with either .easy and .nedf files.
    Since the capsule class copies all the information that the reader gets, it is necessary first to check that the
    readers tests pass (hardcore dependency needed).

    """
    tests = {
        'easy': easyTestData[list(easyTestData.keys())[0]],
        'nedf': nedfTestData[list(nedfTestData.keys())[0]]
    }
    for file in tests:
        # Getting truth from test_data to perform asserts...
        numchan = len(tests[file]['chanlist'])
        first = tests[file]['first_easy_row']
        first_eegdata = np.float32(np.array(first[:numchan]) / 1000.)
        first_markdata = np.array(first[numchan + 3])
        first_dateraw = first[-1]
        first_date = datetime.datetime.fromtimestamp(first_dateraw / 1000).strftime("%Y-%m-%d %H:%M:%S")

        # Assertions now...
        assert capsules[file].good_init
        assert 'anonymous' == capsules[file].author
        assert first_date == capsules[file].eegstartdate

        # file path names assertions:
        assert capsules[file].filepath.endswith(tests[file]['filename'] + '.' + file)
        assert tests[file]['filename'] == capsules[file].basename
        filepath = os.path.join(testpath, tests[file]['filename'])
        assert filepath == capsules[file].filenameroot

        # time related assertions:
        assert 500. == capsules[file].fs
        assert tests[file]['num_samples'] == len(capsules[file].np_time)

        # channel data assertions:
        assert len(tests[file]['chanlist']) == capsules[file].num_channels
        assert tests[file]['chanlist'] == capsules[file].electrodes

        # eeg assertions:
        assert len(first_eegdata) == len(capsules[file].np_eeg[0, :])
        assert tests[file]['num_samples'] == len(capsules[file].np_eeg)
        assert np.array_equal(np.round(first_eegdata), np.round(capsules[file].np_eeg[0, :]))

        # markers assertions:
        assert np.array_equal(first_markdata, capsules[file].np_markers[0])
        assert tests[file]['num_samples'] == len(capsules[file].np_markers)






