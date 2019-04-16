"""
Test to the easyReader class of nepy.
The test imports the ground truth to perform the asserts from test_data.py and asserts all the necessary data to create
a capsule and perform a Frida test.
In case you want to perform the test with different data:
    1. Add your files in nepy/tests/testfiles folder
    2. Modify the ground truth in test_data.py (See documentation)
In case you have modified the easyReader class, then you might need to modify these test functions too.

2019 Neuroelectrics Barcelona
@author: R Sanchez (roser.sanchez@neuroelectrics.com)
"""

import pytest
import os
import datetime
import numpy as np

from nepy.tests.test_data import easyTestData
from nepy.readers.easyReader import easyReader
from nepy.tests.test_data import testpath


@pytest.fixture(scope='module')
def easy_readers():
    """ Loading all the .easy files of the testfiles directory and then initializing a reader for each of them.
    :return: a list of the readers for all files.
    """
    if os.path.isdir(testpath) is False:
        pytest.exit('The the -testfiles- folder path of your computer does not match with the one written '
                    'in test_data.py (testpath) ')
    rdrs = {}  # Dictionary containing a reader per test file.
    for file in easyTestData:
        filepath = os.path.join(testpath, easyTestData[file]['filename']+'.easy')
        try:
            rdrs[file] = easyReader(filepath)
        except FileNotFoundError:
            print('\033[1;31;0m There is a file missing: ', easyTestData[file]['filename']+'.easy')
            print('\033[1;31;0mMake sure that the file exists in the folder.')
            pytest.exit()
    return rdrs


def test_inits(easy_readers):
    """ In this test we assert if all the information regarding file names is recorded correctly in the easyReader
    class """
    assert len(easyTestData) == len(easy_readers)  # Are all the files loaded correctly?
    for file in easyTestData:
        assert easy_readers[file].filepath.endswith(easyTestData[file]['filename']+'.easy')
        assert easyTestData[file]['filename'] == easy_readers[file].basename
        assert ('easy' == easy_readers[file].extension) or ('easy.gz' == easy_readers[file].extension)
        assert 'anonymous' == easy_readers[file].author
        filepath = os.path.join(testpath, easyTestData[file]['filename'])
        assert filepath == easy_readers[file].filenameroot
        assert filepath+'.info' == easy_readers[file].infofilepath
        assert 500. == easy_readers[file].fs


def test_getinfo(easy_readers):
    """ Test if the reader reads correctly the channel information, even if we don't have .info file """
    for file in easyTestData:
        assert len(easyTestData[file]['chanlist']) == easy_readers[file].num_channels
        assert easyTestData[file]['chanlist'] == easy_readers[file].electrodes


def test_get10data(easy_readers):
    """ Test if the EEG, accelerometer, markers and dates are loaded correctly """
    for file in easyTestData:
        # Load data from easyTestData database
        numchan = len(easyTestData[file]['chanlist'])
        first = easyTestData[file]['first_easy_row']
        numcols = len(easyTestData[file]['first_easy_row'])

        # Get the information we want to assert
        first_eegdata = np.float32(np.array(first[:numchan])/1000.)
        first_accdata = np.array(first[numchan:numchan + 3])
        first_markdata = np.array(first[numchan + 3])
        first_dateraw = first[-1]
        first_date = datetime.datetime.fromtimestamp(first_dateraw / 1000).strftime("%Y-%m-%d %H:%M:%S")

        assert len(first_eegdata) == len(easy_readers[file].np_eeg[0, :])
        assert easyTestData[file]['num_samples'] == len(easy_readers[file].np_eeg)
        assert np.array_equal(first_eegdata, easy_readers[file].np_eeg[0, :])
        if (numcols == 13) or (numcols == 25) or (numcols == 37):
            assert easy_readers[file].acc_data
        assert np.array_equal(first_accdata, easy_readers[file].np_acc[0, :])
        assert easyTestData[file]['num_samples'] == len(easy_readers[file].np_acc)
        assert np.array_equal(first_markdata, easy_readers[file].np_markers[0])
        assert easyTestData[file]['num_samples'] == len(easy_readers[file].np_markers)
        assert first_date == easy_readers[file].eegstartdate
        assert easyTestData[file]['num_samples'] == len(easy_readers[file].np_time)

        # For more exhaustive testing we need to have more rows to test in the fields of the test data.
        if 'more_rows' in easyTestData[file]:
            for ind in range(len(easyTestData[file]['more_rows'])):
                # Load the info for each of the lines
                row = easyTestData[file]['more_rows'][ind]
                row_ind = row[0]-1  # We subtract 1 since Notepad starts the indexing in 1.
                eegdata = np.float32(np.array(row[1:numchan+1]) / 1000.)
                accdata = np.array(row[numchan+1:numchan + 4])
                markdata = np.array(row[numchan + 4])

                # Perform the assertions
                assert np.array_equal(eegdata, easy_readers[file].np_eeg[row_ind, :])
                if (numcols == 13) or (numcols == 25) or (numcols == 37):
                    assert easy_readers[file].acc_data
                assert np.array_equal(accdata, easy_readers[file].np_acc[row_ind, :])
                assert np.array_equal(markdata, easy_readers[file].np_markers[row_ind])








