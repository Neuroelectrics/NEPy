"""
Simplified version of a Frida (object format).

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
    """
    Frida is a class that contains a capsule object to process the data, the necessary parameters and methods to do a
    quality check (QC), and to preprocess the data if necessary.
    """

    def __init__(self, filepath, author="anonymous", parameters=None):

        c = Capsule(filepath, author)
        self.c = c

        if parameters is None:
            self.param = {
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
        else:
            self.param = parameters

    def QC(self):
        """
        Quailty Check: checking Offsets and checking signal to detect bad data
        :param plotit: plot the results or not
        :return: summary of a quality check
        """

        p = self.param
        print("\n---QUALITY CHECK---")
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
        print("\n---QC COMPLETE---")

        return

    def preprocess(self, pipeline=None):

        if pipeline is None:
            pipeline = ['rereferenceData', 'detrendData', 'notch', 'bandpassfilter']

        print('---PREPROCESSING---')
        print("Pipeline:")
        print(pipeline)

        step = 1
        for action in pipeline:
            print("Step", step, ": ", action, " ...")
            exec("self._" + action + "()")
            step += 1
            print(" -------------------")
            print(" ")
        print("Done: Updated Log: ", self.c.log)
        print(" ")

        return

    def plotEEG(self, spacing=200, fixlim=True, xlim=False):
        """
        Function to visualize the eeg file
        :param spacing: y axis space between channels. Default: 200uV
        :param fixlim: fix the y axis accordingly. Default: True.
        :param xlim: limits of time that you want to plot. Default=None, that means that we will plot all data we have.
        :return: EEG plot.
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

    def capsulePSD(self, plotit=True):
        """
        function that computes (and plots) the PSD of np_eeg channels of capsule.
        :param plotit: flag to plot the PSDs for each channel or not.
        :return: capsule object with updated PDS attribute
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

            if plotit is True:
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
        Check each of the channels independly and returns a flag if the data is bad.
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
        """
        Resets the attribute self.c.np_eeg to the original, unprocessed data.
        """
        print("\n... Reseting EEG ...")
        self.c.np_eeg = self.c.np_eeg_original.copy()
        self.c.log.append("- EEG reset on " + time.strftime("%Y-%m-%d %H:%M"))

    def _checkOffsets(self):
        """
        Check the offsets for every EEG channel (np_eeg) and mark it with an (*) if the thresholds are exceeded.
        """
        c = self.c
        p = self.param

        print("\n... Checking Offsets ...")
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
        """
        Rereference the data to a channel, a collection of channels or the average ref.
        """
        p = self.param
        print("\n... Rereferencing data ...")
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
            '- Reference to: ' + " ".join(p['reference_electrodes']) + " on " + time.strftime("%Y-%m-%d %H:%M"))

    def _detrendData(self):
        """
        Detrend capsule data linearly in a specific time window, detrend_time
        """
        c = self.c
        p = self.param
        print("\n... Detrending data ...")
        print("Every ", p['detrend_time'], " seconds")
        df_eeg_det = detrend(c.np_eeg, axis=0,
                             bp=np.arange(0, c.np_eeg.shape[0], p['detrend_time'] * c.fs, dtype="int32"))

        self.c.np_eeg = df_eeg_det
        self.c.log.append('- Detrend data every ' + str(p['detrend_time']) + " s on " + time.strftime("%Y-%m-%d %H:%M"))

    def _bandpassfilter(self):
        """
        Band pass filter the data with a butterworth filter with a specific cutoff frequencies
        """
        c = self.c
        p = self.param
        print("\n... Filtering data ...")
        print("Cutoff frequencies: ", p['fL'], "-", p['fH'])

        nyq = 0.5 * self.c.fs
        normal_cutoff1 = self.param['fL'] / nyq
        normal_cutoff2 = self.param['fH'] / nyq
        [b, a] = butter(self.param['order'], [normal_cutoff1, normal_cutoff2], btype='bandpass', analog=False)

        for ch in range(c.num_channels):
            filtered = lfilter(b, a, c.np_eeg[:, ch])
            self.c.np_eeg[:, ch] = filtered

        self.c.log.append(
            '- Filter at fL= ' + str(p['fL']) + " and fH=" + str(p['fH']) + " on " + time.strftime("%Y-%m-%d %H:%M"))

    def _notch(self):
        """
        Notch filter the data to remove the power line frequency component.
        """
        c = self.c
        p = self.param
        print("\n... Notch filtering ...")
        print("Power line frequency: ", p['fline'])
        print("Notch Q-factor: ", p['Q'])

        w0 = 1.0 * p['fline'] / (c.fs / 2.)
        b, a = iirnotch(w0, p['Q'])

        for ch in range(c.num_channels):
            filtered = lfilter(b, a, c.np_eeg[:, ch])
            self.c.np_eeg[:, ch] = filtered
        self.c.log.append(
            '- Notch at ' + str(p['fline']) + " with Q=" + str(p['Q']) + " on " + time.strftime("%Y-%m-%d %H:%M"))

    def _getPSD(self, ix=None):
        """
        Generates PSD for a given capsule and channel.
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




