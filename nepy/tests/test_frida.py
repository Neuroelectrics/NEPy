"""
Test to the Frida class of nepy.
The test imports the ground truth to perform the asserts from test_data.py and asserts all the necessary data to create
a capsule and perform a Frida test.
In case you want to perform the test with different data:
    1. Add your files in nepy/tests/testfiles folder
    2. Modify the ground truth in test_data.py (See documentation)
In case you have modified the Frida class, then you might need to modify these test functions too.

2019 Neuroelectrics Barcelona
@author: R Sanchez (roser.sanchez@neuroelectrics.com)
"""

import os
import pytest
import numpy as np

from nepy.frida.frida import Frida
from nepy.tests.test_data import easyTestData
from nepy.tests.test_data import testpath


@pytest.fixture(scope='module')
def fobj():
    """
    Since we have a test for the readers and for capsule (with two extension types), it is enough to test Frida object
    with one of the easyFiles. In this case, we are always going to take the first one that it finds in easyTestData
    so we make sure we have at leasst one file to test!
    """
    if os.path.isdir(testpath) is False:
        pytest.exit('The the -testfiles- folder path of your computer does not match with the one written '
                    'in test_data.py (testpath) ')
    filepath = os.path.join(testpath, str(easyTestData[list(easyTestData.keys())[0]]['filename']) + '.easy')

    fobj = Frida(filepath)
    if fobj.c.good_init is False:
        pytest.exit("File not found to create the capsule. Check that the file exists or the reader's tests.")

    # Now we are going to fill the capsule eeg data with a synthetic signal to perform the signal processing tests:
    fobj = define_testdata(fobj)
    fobj.updatePSD()
    return fobj


def define_testdata(fobj):
    """
    This funciton fills the np_eeg dat of the Frida object with known signals so we can preprocess them and know for
    sure its result.
    :param fobj:
    :return:
    """
    # Now we are going to fill the capsule eeg data with a synthetic signal to perform the signal processing tests:
    x = np.linspace(0, fobj.eeg.shape[0] / 500., fobj.eeg.shape[0])
    mu = 0
    sigma = 5
    # Reseting the data to test...
    fobj.eeg[:, 0] = 500 * np.ones(fobj.eeg.shape[0])  # Ref channel.
    fobj.eeg[:, 1] = 600 + fobj.eeg[:, 0] + np.random.normal(mu, sigma, x.shape) + 10 * np.sin(
        x * 2 * np.pi * 50)  # Line noise channel (at 50Hz)
    fobj.eeg[:, 2] = fobj.eeg[:, 0] + np.random.normal(mu, sigma + 10, x.shape) + 10 * np.sin(
        x * 2 * np.pi * 1)
    fobj.eeg[:, 3] = fobj.eeg[:, 0] + np.random.normal(mu, sigma, x.shape) + 10 * np.sin(x * 2 * np.pi * 100)
    for ch in range(4, fobj.eeg.shape[1]):
        fobj.eeg[:, ch] = fobj.eeg[:, 0] + np.random.normal(mu, sigma, x.shape) + 10 * np.sin(
            x * 2 * np.pi * 10)
    fobj.updatePSD()
    return fobj


@pytest.mark.parametrize("input_span, eeg_vals", [
    (None, [0, 29999]),
    (30, [0, 30*500-1]),
    (30., [0, 30*500-1]),
    ([30], [0, 30*500-1]),
    ([30.], [0, 30*500-1]),
    ([0, 30], [0, 30*500-1]),
    ([0., 30.], [0, 30*500-1]),
    ([1, 50], [1*500, 50*500-1]),
    ([30., 50.], [30*500, 50*500-1]),
    ('g', [0, 29999])
])
def test_fridainit(input_span, eeg_vals):
    """
    It tests if the init fucntion of frida works. Mainly, for any time_span input, it checks that the EEG lenght
    has the expected size.
    :param input_span: expected input span form the user
    :param eeg_vals: expected min and max values of the eeg (it is expected to read the file fake_easy.easy.
    For more informaiton check the test_data.py
    :return:
    """
    filepath = os.path.join(testpath, 'fake_easy.easy')

    # Test the input span is correct:
    f = Frida(filepath, time_span=input_span)

    assert eeg_vals[0] == int(np.amin(f.eeg*1000))
    assert eeg_vals[1] == int(np.amax(f.eeg * 1000))


def test_reset(fobj):
    """
    Since we are changing already the values in the setup, the reset function should bring the np_eeg to the original.
    Also, we are checking here that the np_eeg_original is the expected and that the detrend flag is False again.
    """
    # testset:
    fobj = define_testdata(fobj)
    first = easyTestData[list(easyTestData.keys())[0]]['first_easy_row']
    numchan = len(easyTestData[list(easyTestData.keys())[0]]['chanlist'])
    first_eegdata = np.float32(np.array(first[:numchan]) / 1000.)

    pipeline = ['reset']
    fobj.preprocess(pipeline=pipeline)
    assert np.array_equal(first_eegdata, fobj.eeg[0, :])
    assert np.array_equal(first_eegdata, fobj.eeg_original[0, :])
    assert fobj.detrend_flag is False

    # And again...
    pipeline = ['bandpassfilter', 'reset']
    fobj.preprocess(pipeline=pipeline)
    assert np.array_equal(first_eegdata, fobj.eeg[0, :])
    assert np.array_equal(first_eegdata, fobj.eeg_original[0, :])
    assert fobj.detrend_flag is False


def test_bandpasssfilter(fobj):
    """
    Since we know that the second third channel (indx=2) and the forth(indx=3) have frequencies outside that the onens
    set for the bandpassfilter (1 Hz and 100Hz, respectively), we test first that the test data is saved properly in the
    setup and tben that we obtain the desired results of the bandpassfilter.
    """
    fobj = define_testdata(fobj)
    # First we need to be sure that the initial test data is saved properly:
    PSD1 = 10 * np.log10(fobj.PSD['PSDs'][2] + 1e-12)
    PSD2 = 10 * np.log10(fobj.PSD['PSDs'][3] + 1e-12)
    f = fobj.PSD['frequencies']

    if (PSD1[np.where(f == 1)] < 15) or (PSD2[np.where(f == 100)] < 15):
        pytest.exit('The test data of the set up is not the one expected for this test. Exiting...')
    else:  # Then we can perform the test...
        fobj.preprocess(pipeline=['bandpassfilter'])
        # Update PSDs now
        PSD1 = 10 * np.log10(fobj.PSD['PSDs'][2] + 1e-12)
        PSD2 = 10 * np.log10(fobj.PSD['PSDs'][3] + 1e-12)
        f = fobj.PSD['frequencies']
        assert float(PSD1[np.where(f == 1)][0]) < (-15)
        assert float(PSD2[np.where(f == 100)][0]) < (-15)

        # Reset the eeg in the known sinusoids:
        fobj = define_testdata(fobj)
        # Change bandpass filter parameters:
        fobj.param['low_cutoff_freq'] = 80
        fobj.param['high_cutoff_freq'] = 120
        PSD2_original = 10 * np.log10(fobj.PSD['PSDs'][3] + 1e-12)
        # Perform the preprocessing again and check that the freq at 100 Hz is the same and the other is lower:
        fobj.preprocess(pipeline=['bandpassfilter'])
        # Update PSDs now
        PSD1 = 10 * np.log10(fobj.PSD['PSDs'][2] + 1e-12)
        PSD2 = 10 * np.log10(fobj.PSD['PSDs'][3] + 1e-12)
        f = fobj.PSD['frequencies']
        assert float(PSD1[np.where(f == 1)][0]) < (-15)
        assert np.round(float(PSD2[np.where(f == 100)][0])) == np.round(float(PSD2_original[np.where(f == 100)][0]))


def test_removelinefreq(fobj):
    """
    We check that the power spectrum of the channel that we have defined to have a 50Hz sinusoid at the begginning is
    higher, and after the remove_line_freq funciton has get lower.
    """
    fobj = define_testdata(fobj)
    # First we need to be sure that the initial test data is saved properly:
    PSD = 10 * np.log10(fobj.PSD['PSDs'][1] + 1e-12)
    f = fobj.PSD['frequencies']
    if PSD[np.where(f == 50)] < 15:
        pytest.exit('The test data of the set up is not the one expected for this test. Exiting...')
    else:  # Then we can perform the test...
        fobj.preprocess(pipeline=['remove_line_freq'])
        PSD = 10 * np.log10(fobj.PSD['PSDs'][1] + 1e-12)
        f = fobj.PSD['frequencies']
        assert float(PSD[np.where(f == 50)][0]) < (-15)

        # Reset and retest with other freq
        x = np.linspace(0, fobj.eeg.shape[0] / 500., fobj.eeg.shape[0])
        fobj.eeg[:, 1] = 600 + fobj.eeg[:, 0] + np.random.normal(0, 5, x.shape) + 10 * np.sin(
            x * 2 * np.pi * 60)  # Line noise channel (at 60Hz)
        fobj.param['line_freq'] = 60
        fobj.preprocess(pipeline=['remove_line_freq'])
        PSD = 10 * np.log10(fobj.PSD['PSDs'][1] + 1e-12)
        f = fobj.PSD['frequencies']
        assert float(PSD[np.where(f == 60)][0]) < (-15)


def test_detrend(fobj):
    """
    We check that the offsets are the expected before and after detrending. It is independent of the number of channels
    that the file has since from the chan num 4 on, the signal is exactly the same.
    """
    fobj = define_testdata(fobj)
    fobj.QC(plotit=False)
    # Test that the test data is saved as expected
    initial_offsets = 0.5 * np.ones(fobj.c.num_channels)
    initial_offsets[1] = 1.1
    if not np.array_equal(initial_offsets, np.round(fobj.offsets, decimals=3)):
        pytest.exit('The test data of the set up is not the one expected for this test. Exiting...')
    else:  # Then we can perform the tests...
        expected_offsets = np.zeros(fobj.c.num_channels)
        fobj.preprocess(pipeline=['detrend'])
        fobj.QC(plotit=False)
        assert np.array_equal(expected_offsets, np.round(fobj.offsets, decimals=3))
        # add linear trends:
        x = np.linspace(0, fobj.eeg.shape[0] / 500., fobj.eeg.shape[0])
        fobj.eeg[:, 0] = fobj.eeg[:, 0] + x
        fobj.preprocess(pipeline=['detrend'])
        fobj.QC(plotit=False)
        assert np.array_equal(expected_offsets, np.round(fobj.offsets, decimals=3))


def test_QC(fobj):
    """
    First we check that we get the expected offsets and sigmas from the test data. Also, that the flags are set
    correctly. Then we change the parameters and test again.
    Then we  create another test set where we know how many epochs are damaged or outsice the threshold and we assert
    if we get the same number.
    """

    # Test check_offsets_sigmas (entire signals)
    fobj = define_testdata(fobj)
    fobj.QC(plotit=False)
    initial_offsets = 0.5 * np.ones(fobj.c.num_channels)
    initial_offsets[1] = 1.1
    assert np.array_equal(initial_offsets, np.round(fobj.offsets, decimals=3))
    assert np.array_equal(fobj.bad_chan['offset'], np.array([1., 0., 1., 1., 1., 1., 1., 1.]))
    assert np.array_equal(fobj.bad_chan['sigma'], np.array([1., 1., 0., 1., 1., 1., 1., 1.]))
    # Test singal again!
    fobj.param['signal_offset_limit'] = 0.2
    fobj.param['signal_std_limit'] = 20
    fobj.QC(plotit=False)
    assert np.array_equal(fobj.bad_chan['offset'], np.array([0., 0., 0., 0., 0., 0., 0., 0.]))
    assert np.array_equal(fobj.bad_chan['sigma'], np.array([1., 1., 1., 1., 1., 1., 1., 1.]))

    # Test check_badepochs
    epoch_len = fobj.param['epoch_length']
    amp_th = fobj.param['epoch_amp_threshold']
    std_th = fobj.param['epoch_std_threshold']
    # Redefine test data:
    x = np.linspace(0, fobj.eeg.shape[0] / 500., fobj.eeg.shape[0])
    fobj.eeg[:, 0] = np.ones(fobj.eeg.shape[0])  # Ref channel.
    fobj.eeg[int(epoch_len * 500):int(epoch_len * 500) + int(epoch_len * 250), 0] = amp_th * 1000
    fobj.eeg[:, 1] = std_th * 1000 * np.sin(x)
    for ch in range(4, fobj.eeg.shape[1]):
        fobj.eeg[:, ch] = np.ones(fobj.eeg.shape[0])
    fobj.QC(plotit=False)
    ch0_badepochs = []
    ch1_badepochs = []
    for bepoch in range(len(fobj.bad_records)):
        if fobj.bad_records[bepoch][0] == 0:
            ch0_badepochs.append(1)
        if fobj.bad_records[bepoch][0] == 1:
            ch1_badepochs.append(1)
    assert len(ch0_badepochs) == 1
    assert len(ch1_badepochs) == int((np.floor(fobj.eeg.shape[0] / fobj.c.fs) - epoch_len) / epoch_len)


@pytest.mark.parametrize("ref_chan, exp_init_offsets", [
    ([0], [0., 0.6, 0., 0., -0.]),
    ([0, 1], [-0.3, 0.3, -0.3, -0.3, -0.3]),
    (['ave8'], [-0.075,  0.525, -0.075, -0.075, -0.075]),
    (['ave20'], [-0.03,  0.57, -0.03, -0.03, -0.03]),
    (['ave32'], [-0.019,  0.581, -0.019, -0.019, -0.019])
])
def test_rereference(ref_chan, exp_init_offsets, fobj):
    """
    We check for any input reference_channel in the param attribute of the Frida object.
    This function is made to test any input test file: with or without info file, with any number of channels.
    """

    fobj = define_testdata(fobj)
    fobj.QC(plotit=False)

    # Test that the test data is saved as expected
    initial_offsets = 0.5 * np.ones(fobj.c.num_channels)
    initial_offsets[1] = 1.1
    if not np.array_equal(initial_offsets, np.round(fobj.offsets, decimals=3)):
        pytest.exit('The test data of the set up is not the one expected for this test. Exiting...')

    else:  # Then we can perform the tests...

        # First we need to get the electrode references from the test data
        test_elist = easyTestData[list(easyTestData.keys())[0]]['chanlist']
        numchan = len(test_elist)
        test_refs = []
        ave_flag = False
        if test_elist[0] is not 'Ch1':  # If the test file has an info file with it
            try:  # the index of electrodes, not strings
                for i in ref_chan:
                    test_refs.append(test_elist[i])
            except:  # strings --> Ave, reference. It can be either 'ave', 'average'...
                test_refs = ref_chan
                ave_flag = True
        else:
            test_refs = 'ave'
            ave_flag = True

        # Now that we have the reference channel list saved, we can test the _rereference function in Frida.
        fobj.param['reference_electrodes'] = test_refs  # Save the reference chan list in Frida object, then rereference
        fobj.preprocess(pipeline=['rereference'])
        fobj.QC(plotit=False)

        # We test the 5 first channels of the data since from the fifth, they have the same signal in every channel
        if not ave_flag:  # If we are not performing the average rereferencing...
            assert np.array_equal(exp_init_offsets, np.round(fobj.offsets[:5], decimals=3))
        else:  # If we do the average rereferencing, we need to know how many electrodes we have:
            if numchan == 8 and ref_chan == 'ave8':
                assert np.array_equal(exp_init_offsets, np.round(fobj.offsets[:5], decimals=3))
            elif numchan == 20 and ref_chan == 'ave20':
                assert np.array_equal(exp_init_offsets, np.round(fobj.offsets[:5], decimals=3))
            elif numchan == 32 and ref_chan == 'ave32':
                assert np.array_equal(exp_init_offsets, np.round(fobj.offsets[:5], decimals=3))
