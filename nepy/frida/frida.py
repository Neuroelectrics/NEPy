"""
Simplified version of a Frida in an object format (from Giulio's code).
You can find the original version here: http://git.starlab.es/Sanchez/NEpy.git

2018 Neuroelectrics Corporation

Created on Mon Nov 5 11:39:39 2018
@author: roser (NE)
"""

import time

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from scipy.signal import detrend, lfilter, butter, iirnotch, welch
from itertools import cycle

from nepy.capsule.capsule import Capsule


class Frida(object):
    r"""
    Overview:
    Frida is a class that contains
        - a Capsule object containing all necessary information taken from the .easy and .info file,
        - functions to visualize the raw and preprocessed data,
        - functions to perform a report of the quality of the data and
        - functions to preprocess the data.

    Attributes:
          c:     Capsule object (for more information check the Capsule Docstring
          param: Directory with all necessary parameters to perform the quality check (QC).
                 This parameters are:
                 -time_span:
                        Fraction of time that you want to preprocess. It can be either an integer,
                                        or a list with two values.
                                        Units: seconds
                                        Default: None (it doesn't select any specific time)
                 -grab_seconds:         Time to break epochs for QC
                                        Units: seconds
                                        Default: 10.
                 -detrend_time:         window of time to linearly detrend data.
                                        Units: seconds
                                        Default: 10.
                 -QCthreshold:          Maximum absolute value of the amplitude of data to perform the QC.
                                        Units: uV (micro Volts)
                                        Default: 75.
                 -QCmax:                Maximum standard deviation for the QC.
                                        Units: uV
                                        Default: 30.
                 -fline:                Power line frequency used to notch filter the data.
                                        Europe --> 50 Hz
                                        States --> 60 Hz
                                        Units: Hz
                                        Default: 50
                 -Q:                    Quality factor of the notch filter.
                                        Units: dimensionless
                                        Default: 30.
                 -fL:                   lower cutoff frequency for the bandpass filter.
                                        Units: Hz
                                        Default: 2.
                 -fH:                   higher cutoff frequency for the bandpass filter.
                                        Units: Hz
                                        Default: 45.
                 -order:                Order of the bandpass filter (butterworth).
                                        Units: dimensionless
                                        Default: 5.
                 -reference_electrodes: list of strings defining the reference electrodes of the EEG. It can also
                                        perform the average rereferencing by typing 'ave'.
                                        Units: none
                                        Default: ['Cz']
                 -offset_limit:         checkOffsets() is a function in QC that marks the data with offsets higher than
                                        this value.
                                        Units: mV (mili Volts)
                                        Default: 1.
                 -std_limit:            checkOffsets() is a function that marks the data with standard deviation higher
                                        than this value.
                                        Units: uV (micro Volts)
                                        Default: 15.

    Public methods (see function docstrings):
        -QC
        -preprocess
        -plotEEG
        -plotPSD

    Example of use:
    >>>import nepy.frida.frida as frida
    >>>filepath = 'C:\\Users\\roser.sanchez\\Documents\\Git\\nepy_support\\sampledata\\20170807135459_W012_V1_EYC.easy.gz'
    >>>f = frida.Frida(filepath)  # Create a Frida object (with default parameters)
    >>>f.plotEEG()  # Plot raw data
    >>>f.plotPSD()  # Plot PSDs of raw data
    >>>f.QC()  # Perform a Quality Check
    >>>f.preprocess()  # Preproess the data (with default pipeline)
    >>>f.QC()  # Check if after the preprocessing the now it passes the QC
    >>>f.plotEEG()  # Plot the resulting data
    >>>f.plotPSD()  # Plot the resulting PSDs
    """

    def __init__(self, filepath, author="anonymous", parameters=None):

        c = Capsule(filepath, author)
        self.c = c

        if parameters is None:
            self.param = {
                'time_span': [0, self.c.np_eeg.shape[0]/self.c.fs],
                'grab_seconds': 10.,
                'detrend_time': 10.,
                'QCthreshold': 75.,
                'QCmax': 30.,
                'fline': 50.,
                'Q': 30.,
                'fL': 2.,
                'fH': 45.,
                'order': 5,
                'reference_electrodes': ['Cz'],
                'offset_limit': 1.,
                'std_limit': 15.
            }
            span = [0, self.c.np_eeg.shape[0]]
        else:
            # Check that the input parameters are correct.
            s = (parameters['time_span']) * self.c.fs
            if (type(s) is int) or (type(s) is float):
                span = [0, s]
            elif type(s) is list:
                if len(s) == 1:
                    span = [0, s[0]]
                if len(s) == 2:
                    span = s
                else:
                    print('Input a list containing the range of time you want to process/visualize.')
                    print('Example: \'time_span\': [25, 65], ...')
                    print('Try again!')
                    return
            else:
                print('Wrong \'time_span\' format.')
                print('The \'time_span\' has to be an integer, 30, or a list, [20, 60].')
                print('Try again!')
                return
            self.param = parameters
        span = [int(span[0]), int(span[1])]
        tspan = (span[1] - span[0]) / self.c.fs
        if (tspan < self.param['grab_seconds']) or (tspan < self.param['grab_seconds']):
            print('Unexpected input parameters!')
            print('Check that -grab_seconds- and -detrend_time- are smaller than -time_span-.')
            return
        else:
            # After checking, select the data to process.
            self.c.np_eeg_original = self.c.np_eeg_original[span[0]:span[1], :]
            self.c.np_eeg = self.c.np_eeg[span[0]:span[1], :]
            self.c.np_time = self.c.np_time[span[0]:span[1]]
            self.c.np_markers = self.c.np_markers[span[0]:span[1]]
            if len(self.c.np_stim) > 0:
                self.c.np_stim = self.c.np_stim[span[0]:span[1], :]

    def QC(self):
        """Quailty Check (QC):
        Checking Offsets and checking signal to detect bad data.
        It takes the following parameters:
            -QCthreshold
            -QCmax
            -grab_seconds
        """

        p = self.param
        print("\n--------QUALITY CHECK--------")
        print("Current log is:")
        print(self.c.log)
        print("\nChecking Quality of data with epoch length of ", p['grab_seconds'], " seconds.")
        print("Amplitude threshold (uV)= ", p['QCthreshold'])
        print("STD limit of (uV)       = ", p['QCmax'])

        self._checkOffsets()

        channel_data = np.transpose(self.c.np_eeg)
        print("Minutes of data: {minu:3.1f}".format(minu=channel_data.shape[1] / self.c.fs / 60.))
        Maxtimeskips = int((np.floor(channel_data.shape[1] / self.c.fs) - p['grab_seconds']) / p['grab_seconds'])
        print("Maxtimeskips: ", Maxtimeskips)

        bad_records = []
        for timeskip in range(0, Maxtimeskips):
            try:
                for channel in range(self.c.num_channels):
                    segment = np.array(np.arange(timeskip * p['grab_seconds'] * self.c.fs,
                                                 timeskip * p['grab_seconds'] * self.c.fs + p[
                                                     'grab_seconds'] * self.c.fs), dtype="int32")
                    signal = channel_data[channel, segment].flatten()
                    fl, maxAmp, STD = self._checkSignal(signal)
                    if fl is True:
                        bad_records.append([channel, timeskip, maxAmp, STD])
            except:
                break
        self.c.bad_records = bad_records

        print(""" Found {Nbad} bad channel-epochs out of {total}, or {pc:2.1f}%.
                """.format(Nbad=len(bad_records), total=self.c.num_channels * Maxtimeskips,
                           pc=100 * len(bad_records) / (self.c.num_channels * Maxtimeskips)))
        print("\nBad channel-epochs per channel:")
        for ch in range(self.c.num_channels):
            lista = [x[0] for x in bad_records if x[0] == ch]
            pc = 100 * len(lista) / (self.c.num_channels * Maxtimeskips)
            print("channel {ch:<3} / {name:>5}, N= {ll:<4} (or {pc:2.1f}%)".format(
                ch=ch, name=self.c.electrodes[ch], ll=len(lista), pc=pc))
        print("\n---------QC COMPLETE---------")

    def preprocess(self, pipeline=None):
        """ Preprocess the data
        for a specific input pipeline.
        :param pipeline: list of strings with the name of the functions to preprocess in a specific order.
                         It uses the input parameters of Frida when initialize it.
                         The available functions are (with respective parameters):
                            -resetEEG:        reset EEG to original, unprocessed, raw.
                            -checkOffsets:    check the offsets depending on the 'offset_limit' and 'std_limit' for a
                                              'grab_seconds' time.
                            -rereferenceData: rereference the data to a channel, a collection of channels or the average
                                              of all of them together.
                            -detrendData:     detrend data linearly for every 'detrend_time' seconds.
                            -bandpassfilter:  bandpass filter the data with a cutoff frequencies of 'fL'-'fH' and
                                              'order'.
                            -notch:           notch filter the data to remove the power line frequency 'fline', using a
                                              quality factor 'Q'.
                         Default: ['resetEEG', 'referenceData', 'detrendData', 'notch', 'bandpassfilter']
        """

        if pipeline is None:
            pipeline = ['resetEEG', 'rereferenceData', 'detrendData', 'notch', 'bandpassfilter']

        print('---------PREPROCESSING---------')
        # print("-------------------------------")
        print("Pipeline:")
        print(pipeline)
        print("-------------------------------")

        step = 1
        for action in pipeline:
            print("Step", step, ": ", action, " ...")
            exec("self._" + action + "()")
            step += 1
            print("-------------------------------")
            print(" ")
        print("Done: Updated Log: ", self.c.log)
        print(" ")

    def plotEEG(self, spacing=200, fixlim=True, xlim=False):
        """ Plot EEG
        Function to visualize the EEG data
        :param spacing: y axis space between channels. Default: 200uV
        :param fixlim: fix the y axis accordingly. Default: True.
        :param xlim: limits of time that you want to plot. Default=None, that means that we will plot all data we have.
        """

        c = self.c
        print("\033[1mPlotting EEG channels after this pipeline:\033[0m")
        for n in range(0, len(c.log)):
            print(n + 1, ".", c.log[n])
        print("\n\033[1mFile: \033[0m", c.filenameroot)

        maxspan = c.np_eeg.shape[0]
        t = c.np_time[:maxspan]

        lines = ["-", "--", "-.", ":"]
        linecycler = cycle(lines)

        _, ax = plt.subplots(1, 1, figsize=[12.0, c.num_channels * 0.75])
        for ch in range(1, c.num_channels + 1):
            chadata = c.np_eeg[:maxspan, ch - 1] - c.np_eeg[0, ch - 1]
            if ch % 2 == 0:
                plt.plot(t, chadata + spacing * ch, next(linecycler), color='r')
            else:
                plt.plot(t, chadata + spacing * ch, next(linecycler), color='b')

        plt.grid(which='major')
        plt.grid(which='minor')
        plt.title("data for file " + c.filenameroot + " (Spacing=" + str(spacing) + "uV)")
        plt.xlabel('Seconds from ' + c.eegstartdate)
        plt.ylabel("uV, arbitrary refererence")

        plt.yticks(list(range(spacing, (c.num_channels + 1) * spacing, spacing)), c.electrodes)
        if fixlim:
            plt.ylim(0, (c.num_channels + 1) * spacing)

        try:
            plt.legend(c.electrodes)
        except:
            print("no electrode labels found")
            plt.legend(list(range(1, c.num_channels + 1)))
        if xlim:
            plt.xlim(xlim)

        ax.get_xaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
        ax.get_yaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
        ax.grid(b=True, which='major', color='grey', linewidth=1.0)
        ax.grid(b=True, which='minor', color='lightgrey', linewidth=0.5)
        plt.show()

    def plotPSD(self):
        """ plot PSDs
        function that computes (and plots) the PSD of the eeg channels.
        """
        c = self.c
        print("\033[1mPlotting PSDs after this pipeline:\033[0m")
        for n in range(0, len(c.log)):
            print(n + 1, ".", c.log[n])
        print("\n\033[1mFile: \033[0m", c.filenameroot)

        PSDs = []
        f = []
        for ix in range(c.num_channels):
            print("\nChannel {chix}: {chname}, STD={stdv:6.1f} uV".format(chix=str(ix + 1), chname=c.electrodes[ix],
                                                                          stdv=np.std(c.np_eeg[:, ix])))

            f, PSD = self._getPSD(ix)
            PSDs.append(PSD)

            _, ax = plt.subplots(1, 1, figsize=[12.0, 2.5])
            plt.plot(f, 10 * np.log10(PSD + 1e-12), f, -np.ones(len(f)) * 15, f, np.ones(len(f)) * 15, linewidth=1)
            plt.xlabel('frequency [Hz]')
            plt.ylabel('10log10 (PSD [uV^2/Hz])')
            plt.ylim(-30., 30)
            plt.xlim(0, c.fs / 2)
            plt.grid()
            plt.title("Channel " + str(ix + 1) + " (" + c.electrodes[ix] + ")")
            ax.get_xaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
            ax.get_yaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
            ax.grid(b=True, which='major', color='grey', linewidth=0.5)
            ax.grid(b=True, which='minor', color='lightgrey', linewidth=0.5)
            plt.show()

        self.c.PSD = {
            "frequencies": f,
            "PSDs": PSDs,
            "Channels": c.electrodes,
            "Log:": c.log}

    def _checkSignal(self, signal, verbose=False):
        """
        Check each of the channels independently and returns a flag if the data is bad.
        :param signal: single channel data
        :param verbose: print the info
        :return: flag, amplitude and STD for every channel.
        """

        flag = False
        detrended_signal = detrend(signal)
        w = np.max(np.abs(detrended_signal))
        std = np.std(detrended_signal)
        if w > self.param['QCthreshold']:
            flag = True

        if std > self.param['QCmax']:
            flag = True

        if flag & verbose:
            print("Bad at checkSignal: Threshold of ", self.param['QCthreshold'], " exceeded: max Amp is", w)
            print("Bad at checkSignal: Threshold of ", self.param['QCmax'], " exceeded: STD is", std, "uV")

        return flag, w, std

    def _resetEEG(self):
        """Resets the attribute self.c.np_eeg to the original, unprocessed/raw data."""

        self.c.np_eeg = self.c.np_eeg_original.copy()
        self.c.log.append("EEG reset on " + time.strftime("%Y-%m-%d %H:%M"))

    def _checkOffsets(self):
        """
        Check the offsets for every EEG channel (np_eeg) and mark it with an (*) if the thresholds are exceeded.
        """
        c = self.c
        p = self.param

        print("Offset limit: ", p['offset_limit'])
        print("STD limit: ", p['std_limit'])

        offsets = [np.mean(c.np_eeg, axis=0)[ch] / 1000 for ch in range(0, c.np_eeg.shape[1])]  # mV
        sigmas = [np.std(c.np_eeg, axis=0)[ch] for ch in range(0, c.np_eeg.shape[1])]  # uV

        for ch in range(c.num_channels):
            star_offset = ' '
            star_sigma = ' '
            if np.abs(offsets[ch]) > p['offset_limit']:
                star_offset = '(*)'
            if sigmas[ch] > p['std_limit']:
                star_sigma = '(*)'
            print("Channel {ch:<6}: Offset = {off:>6.1f} mV{star1:3} / STD = {std:>6.1f} uV {star2}".format(
                ch=c.electrodes[ch], off=offsets[ch], star1=star_offset, star2=star_sigma, std=sigmas[ch]))

        _, ax = plt.subplots(1, 1, figsize=[12.0, 2.5])
        plt.bar(np.arange(len(offsets)) + 1, offsets)
        plt.xlabel("Channel")
        plt.ylabel("Offset (mV)")
        plt.xticks(list(range(1, (c.num_channels + 1))), c.electrodes)
        plt.title("Offsets for file " + c.filepath)
        ax.get_xaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
        ax.get_yaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
        ax.grid(b=True, which='major', color='grey', linewidth=1.0)
        ax.grid(b=True, which='minor', color='lightgrey', linewidth=0.5)
        plt.show()

        _, ax = plt.subplots(1, 1, figsize=[12.0, 2.5])
        plt.bar(np.arange(len(sigmas)) + 1, sigmas, color='r')
        plt.xlabel("Channel")
        plt.ylabel("STD (uV)")
        plt.xticks(list(range(1, c.num_channels + 1)), c.electrodes)
        plt.title("STDs for file " + c.filepath)
        ax.get_xaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
        ax.get_yaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
        ax.grid(b=True, which='major', color='grey', linewidth=1.0)
        ax.grid(b=True, which='minor', color='lightgrey', linewidth=0.5)
        plt.show()

        self.c.offsets = offsets
        self.c.sigmas = sigmas

    def _rereferenceData(self):
        """Rereference the data to a channel, a collection of channels or the average ref."""
        p = self.param
        print("Reference electrodes: ", p['reference_electrodes'])
        self.c.reference_electrodes = p['reference_electrodes']
        c = self.c

        try:
            sorted_electrode_index = [c.electrodes.index(element) for element in p['reference_electrodes']]
            if len(p['reference_electrodes']) == 1:
                ref = c.np_eeg[:, sorted_electrode_index[0]]
            else:
                print("Computing mean of: ", p['reference_electrodes'])
                ref = np.mean(c.np_eeg[:, sorted_electrode_index], axis=1)
        except:
            print("Using average reference")
            ref = np.mean(c.np_eeg, axis=1)

        df_eeg_ref = c.np_eeg.copy()

        for ch in range(c.np_eeg.shape[1]):
            df_eeg_ref[:, ch] = c.np_eeg[:, ch] - ref

        self.c.np_eeg = df_eeg_ref
        self.c.log.append(
            'Reference to: ' + " ".join(p['reference_electrodes']) + " on " + time.strftime("%Y-%m-%d %H:%M"))

    def _detrendData(self):
        """ Detrend data linearly in a specific time window, 'detrend_time'."""
        c = self.c
        p = self.param
        print("Every ", p['detrend_time'], " seconds")
        df_eeg_det = detrend(c.np_eeg, axis=0,
                             bp=np.arange(0, c.np_eeg.shape[0], p['detrend_time'] * c.fs, dtype="int32"))

        self.c.np_eeg = df_eeg_det
        self.c.log.append('Detrend data every ' + str(p['detrend_time']) + " s on " + time.strftime("%Y-%m-%d %H:%M"))

    def _bandpassfilter(self):
        """ Band pass filter the data with a butterworth filter with a specific cutoff frequencies"""
        c = self.c
        p = self.param
        print("Cutoff frequencies: ", p['fL'], "-", p['fH'])

        nyq = 0.5 * self.c.fs
        normal_cutoff1 = self.param['fL'] / nyq
        normal_cutoff2 = self.param['fH'] / nyq
        [b, a] = butter(self.param['order'], [normal_cutoff1, normal_cutoff2], btype='bandpass', analog=False)

        for ch in range(c.num_channels):
            filtered = lfilter(b, a, c.np_eeg[:, ch])
            self.c.np_eeg[:, ch] = filtered

        self.c.log.append(
            'Filter at fL= ' + str(p['fL']) + " and fH=" + str(p['fH']) + " on " + time.strftime("%Y-%m-%d %H:%M"))

    def _notch(self):
        """Notch filter the data to remove the power line frequency component."""
        c = self.c
        p = self.param
        print("Power line frequency: ", p['fline'])
        print("Notch Q-factor: ", p['Q'])

        w0 = 1.0 * p['fline'] / (c.fs / 2.)
        b, a = iirnotch(w0, p['Q'])

        for ch in range(c.num_channels):
            filtered = lfilter(b, a, c.np_eeg[:, ch])
            self.c.np_eeg[:, ch] = filtered
        self.c.log.append(
            'Notch at ' + str(p['fline']) + " with Q=" + str(p['Q']) + " on " + time.strftime("%Y-%m-%d %H:%M"))

    def _getPSD(self, ix=None):
        """
        Generates PSD for a given eeg channel.
        :param ix: Channel index (array index, i.e., ch-1)
        :return: returns the frequency and the PSD array for the input channel
        """
        window = 'hanning'
        nperseg = 10 * self.c.fs
        noverlap = nperseg / 2.
        nfft = None
        detrendit = 'constant'  # or linear
        return_onesided = True
        scaling = 'density'

        f, Pxx_den = welch(self.c.np_eeg[:, ix], fs=self.c.fs, window=window, nperseg=nperseg, noverlap=noverlap,
                           nfft=nfft, detrend=detrendit, return_onesided=return_onesided, scaling=scaling, axis=-1)
        return f, Pxx_den




