"""
Test to the nedfReader class of nepy.
The test imports the ground truth to perform the asserts from test_data.py and asserts all the necessary data to create
a capsule and perform a Frida test.
In case you want to perform the test with different data:
    1. Add your files in nepy/tests/testfiles folder
    2. Modify the ground truth in test_data.py (See documentation)
In case you have modified the nedfReader class, then you might need to modify these test functions too.

2019 Neuroelectrics Barcelona
@author: R Sanchez (roser.sanchez@neuroelectrics.com)
"""

import pytest
import os
import datetime
import numpy as np

from nepy.tests.test_data import nedfTestData
from nepy.tests.test_data import nedfOnlyStimTestData
from nepy.readers.nedfReader import nedfReader
from nepy.tests.test_data import testpath


def get_nedf_readers(dataSet):
    """ Loading all the .nedf files of the testfiles directory and then initializing a reader for each of them.
    :return: a list of the readers for all files.
    """
    if os.path.isdir(testpath) is False:
        pytest.exit('The the -testfiles- folder path of your computer does not match with the one written '
                    'in test_data.py (testpath) ')
    rdrs = {}  # Dictionary containing a reader per test file.
    for file in dataSet:
        print(file)
        filepath = os.path.join(testpath, dataSet[file]['filename']+'.nedf')
        try:
            rdrs[file] = nedfReader(filepath)
        except FileNotFoundError:
            print('\033[1;31;0m There is a file missing: ', dataSet[file]['filename']+'.nedf')
            print('\033[1;31;0mMake sure that the file exists in the folder.')
            pytest.exit()
    return rdrs

@pytest.fixture(scope='module')
def nedf_readers():
    return get_nedf_readers(nedfTestData)
    
@pytest.fixture(scope='module')
def nedf_readers2():
    return get_nedf_readers(nedfOnlyStimTestData)

def test_inits(nedf_readers):
    """ In this test we assert if all the information regarding file names is recorded correctly in the easyReader
    class """
    assert len(nedfTestData) == len(nedf_readers)  # Are all the files loaded correctly?
    for file in nedfTestData:
        assert nedf_readers[file].filepath.endswith(nedfTestData[file]['filename']+'.nedf')
        assert nedfTestData[file]['filename'] == nedf_readers[file].basename
        assert 'anonymous' == nedf_readers[file].author
        filepath = os.path.join(testpath, nedfTestData[file]['filename'])
        assert filepath == nedf_readers[file].filenameroot
        assert 500. == nedf_readers[file].fs


def test_getinfo(nedf_readers):
    """ Test if the reader reads correctly the channel information, even if we don't have .info file """
    for file in nedfTestData:
        assert len(nedfTestData[file]['chanlist']) == nedf_readers[file].num_channels
        assert nedfTestData[file]['chanlist'] == nedf_readers[file].electrodes


def test_get10data(nedf_readers):
    """ Test if the EEG, accelerometer, markers and dates are loaded correctly """
    for file in nedfTestData:
        # Load data from nedfTestData database
        numchan = len(nedfTestData[file]['chanlist'])
        first = nedfTestData[file]['first_easy_row']

        # Get the information we want to assert
        first_eegdata = np.float32(np.array(first[:numchan]) / 1000.)
        first_markdata = np.array(first[numchan + 3])
        first_dateraw = first[-1]
        first_date = datetime.datetime.fromtimestamp(first_dateraw / 1000).strftime("%Y-%m-%d %H:%M:%S")

        assert len(first_eegdata) == len(nedf_readers[file].np_eeg[0, :])
        assert np.array_equal(np.round(first_eegdata), np.round(nedf_readers[file].np_eeg[0, :]))
        assert nedfTestData[file]['num_samples'] == len(nedf_readers[file].np_eeg)
        assert first_markdata == nedf_readers[file].np_markers[0]
        assert nedfTestData[file]['num_samples'] == len(nedf_readers[file].np_markers)
        assert first_date == nedf_readers[file].eegstartdate
        assert nedfTestData[file]['num_samples'] == len(nedf_readers[file].np_time)

        # For more exhaustive testing we need to have more rows to test in the fields of the test data.
        if 'more_rows' in nedfTestData[file]:
            for ind in range(len(nedfTestData[file]['more_rows'])):
                # Load the info for each of the lines
                row = nedfTestData[file]['more_rows'][ind]
                row_ind = row[0]-1  # We subtract 1 since Notepad starts the indexing in 1.
                eegdata = np.float32(np.array(row[1:numchan+1]) / 1000.)

                # Perform the assertions
                assert np.array_equal(np.round(eegdata),  np.round(nedf_readers[file].np_eeg[row_ind, :]))
                # We can't assert the rest of the data since the sampling rate are different.

def test_get_stim_data(nedf_readers2):
    """ Test if the stim data is loaded correctly in a file with no EEG data """
    for file in nedfOnlyStimTestData:
        assert len(nedf_readers2[file].np_eeg) == 0
        n_eeg_samples = nedfOnlyStimTestData[file]['num_stim_samples'] // 2
        n_stim_samples = n_eeg_samples * 2
        assert nedf_readers2[file].samples == n_eeg_samples
        assert len(nedf_readers2[file].np_stim) == n_stim_samples
        for rows in nedfOnlyStimTestData[file]['stim_rows']:
            r = rows['row']
            data = rows['data']
            print(data)
            stimdata = np.float32(np.array(data))
            assert np.array_equal(np.round(stimdata), np.round(nedf_readers2[file].np_stim[r, :]))
            

