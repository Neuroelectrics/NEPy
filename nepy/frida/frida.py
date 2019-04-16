"""
Simplified version of a Frida in an object format (from Giulio's code:
http://git.starlab.es/Sanchez/NEpy_original/tree/master/nepy/frida).

Frida is a class that contains all necessary funcitons to preprocess the EEG data that is stored in a Capsule object.

2018 Neuroelectrics Corporation

Created on Mon Nov 5 11:39:39 2018
@author: roser (NE)
"""

import time

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from scipy.signal import detrend, filtfilt, butter, iirnotch, welch

from nepy.capsule.capsule import Capsule


class Frida(object):
    r"""
    Overview:
    Frida is a class that contains
        - a Capsule object containing all necessary information taken from the .easy and .info file,
        - functions to visualize the raw and preprocessed data (EEG and PSDs,
        - functions to perform a report of the quality of the data and
        - functions to preprocess the data.

    Attributes:
          c:     Capsule object (for more information check the Capsule Docstring
          log: log containing all the preprocessing steps
          eeg: processed eeg
          eeg_original: original capsule eeg
          offsets: offset array of the signal
          sigmas: stds of the signals
          PSD: dictionary with PSD info
          bad_chan: channel flags related to channel threshold
          bad_records: bad epochs informaition dictionary
          param: Directory with all necessary parameters to perform the quality check (QC).
                 This parameters are:
                 -epoch_length:         Time to break epochs for the Quality Check.
                                        Units: seconds
                                        Default: 10.
                 -detrend_time:         window of time to linearly detrend data.
                                        Units: seconds
                                        Default: 10.
                 -epoch_amp_threshold:  Maximum absolute value of the amplitude of an epoch to label as bad.
                                        Units: uV (micro Volts)
                                        Default: 75.
                 -epoch_std_threshold:  Maximum standard deviation of an epoch to label as bad.
                                        Units: uV
                                        Default: 30.
                 -line_freq:            Power line frequency used to notch filter the data.
                                        Europe --> 50 Hz
                                        States --> 60 Hz
                                        Units: Hz
                                        Default: 50
                 -Q_notch:              Quality factor of the notch filter.
                                        Units: dimensionless
                                        Default: 30.
                 -low_cutoff_freq:      lower cutoff frequency for the bandpass filter.
                                        Units: Hz
                                        Default: 2.
                 -high_cutoff_freq:     higher cutoff frequency for the bandpass filter.
                                        Units: Hz
                                        Default: 45.
                 -order:                Order of the bandpass filter (butterworth).
                                        Units: dimensionless
                                        Default: 5.
                 -reference_electrodes: list of strings defining the reference electrodes of the EEG. It can also
                                        perform the average rereferencing by typing 'ave'.
                                        Units: none
                                        Default: ['Cz']
                 -signal_offset_limit:  __check_offset_std() is a function in QC that marks the data with offsets higher
                                        than this value.
                                        Units: mV (mili Volts)
                                        Default: 1.
                 -signal_std_limit:     __check_offset_std() is a function that marks the data with standard deviation
                                        higher than this value.
                                        Units: uV (micro Volts)
                                        Default: 15.
    Public methods (see docstrings):
        -QC
        -preprocess
        -plotEEG
        -plotPSD

    Example of use:
    >>>import nepy.frida.frida as frida
    >>>filepath = 'C:\\Users\\roser.sanchez\\Documents\\Git\\nepy\\sampledata\\20170807135459_W012_V1_EYC.easy.gz'
    >>>f = frida.Frida(filepath)  # Create a Frida object (with default parameters)
    >>>f.plotEEG()  # Plot raw data
    >>>f.plotPSD()  # Plot PSDs of raw data
    >>>f.QC()  # Perform a Quality Check
    >>>f.preprocess()  # Preproess the data (with default pipeline)
    >>>f.QC()  # Check if after the preprocessing the now it passes the QC
    >>>f.plotEEG()  # Plot the resulting data
    >>>f.plotPSD()  # Plot the resulting PSDs
    """

    def __init__(self, filepath, author="anonymous", parameters=None, time_span=None, verbose=True):
        """
        Initialization of a Frida object. What do we need:
        :param filepath: datapath + filename + extension of the file that we want to preprocess
        :param author: author's name
        :param parameters: parameter dictionary. See help(Frida) for the expected dictionary fields.
        :param time_span: time span that we want to study. It can be either an integer/float, or a list of two numbers,
                            the initial and final seconds. Units: seconds. Default: the original lenght of the file.
        :param verbose: flag to plot or not what is read by the easyReader. By default, it is on.
        """

        # Creating a Capsule object with the filepath provided by the user.
        c = Capsule(filepath, author, verbose=verbose)
        self.c = c
        self.log = ["Object created: " + self.c.capsuledate]
        self.good_init = True
        if c.good_init is False:  # Check if it has been an error creating the Capsule object.
            self.good_init = False
            return

        if parameters is None:  # Default parameters if there is no parameter input.
            self.param = {
                'signal_offset_limit': 1.,
                'signal_std_limit': 15.,
                'epoch_length': 10.,
                'epoch_amp_threshold': 75.,
                'epoch_std_threshold': 30.,
                'detrend_time': 10.,
                'line_freq': 50.,
                'Q_notch': 30.,
                'low_cutoff_freq': 2.,
                'high_cutoff_freq': 45.,
                'order': 5,
                'reference_electrodes': ['Cz']
            }
        else:
            if len(parameters) is not 12:  # If there's some parameter missing...
                print('\033[0;31;48m \nThere are parameters missing to perform a Frida test. Expected parameters:')
                print('\033[0;31;48m- signal_offset_limit\n'
                      '- signal_std_limit\n'
                      '- epoch_length\n'
                      '- epoch_amp_threshold\n'
                      '- epoch_std_threshold\n'
                      '- detrend_time\n'
                      '- line_freq\n'
                      '- Q_notch\n'
                      '- low_cutoff_freq\n'
                      '- high_cutoff_freq\n'
                      '- order\n'
                      '- reference_electrodes\n\n'
                      '... Check help(Frida) for more information regarding the input parameters.')

                return
            for field in parameters:  # If there's an emply parameter...
                if not parameters[field]:
                    print('\033[0;31;48m Empty parameter: {0}'.format(parameters[field]))
                    self.good_init = False
                    return

            self.param = parameters  # Save the parameters as an attribute of Frida, so we can access anytime.

        # Now that we have saved the parameters we can check the time_span.
        if (time_span is None) or type(time_span) is str:  # Default time_span. The original shape of the file.
            span = [0, self.c.np_eeg.shape[0]]
            good_span = 1
        else:  # Check what the user has input and return it in the right format
            span, good_span = self.__check_timespan(time_span)

        if good_span:
            self.eeg_original = self.c.np_eeg[span[0]:span[1], :]
            self.eeg = self.eeg_original.copy()
            self.c.np_time = self.c.np_time[span[0]:span[1]]
            self.c.np_markers = self.c.np_markers[span[0]:span[1]]
            if len(self.c.np_stim) > 0:
                self.c.np_stim = self.c.np_stim[span[0]:span[1], :]
            self.detrend_flag = False
            self.updatePSD()
        else:
            self.good_init = False
            return
        # Initialize extra attributes where we are going to save the output of the Frida test:
        self.offsets = None
        self.sigmas = None
        self.PSD = None
        self.bad_chan = {}
        self.bad_records = None

    def __check_timespan(self, time_span):
        """
        Function that returns a time span in the right format, after reading the user's input. Converts the seconds of
        the input in samples so it is faster to work with.
        :param time_span: should be an integer, a float, or a two element list containing the time span that the user
                        wants to preprocess. Unints of the input should be in seconds.
        :return: time_span in the right format and a flag specifying if the user has input the time_span correctly.
                The time span returned is in samples, no in seconds.
        """

        # First we check that the time_span has the right format
        if (type(time_span) is int) or (type(time_span) is float):
            span = [0, int(time_span * self.c.fs)]
            flag = 1
        elif type(time_span) is list:
            if len(time_span) < 2:
                span = [0, int(time_span[0]*self.c.fs)]
                flag = 1
            elif len(time_span) == 2:
                span = [int(time_span[0]*self.c.fs), int(time_span[1]*self.c.fs)]
                flag = 1
            else:
                print('\033[0;31;48mInput a list containing the range of time you want to process/visualize.')
                print('\033[0;31;48mExample: \'time_span\': [25, 65], ...')
                print('\033[0;31;48mTry again!')
                flag = 0
                return time_span, flag
        else:
            print('\033[0;31;48mWrong \'time_span\' format.')
            print('\033[0;31;48mThe \'time_span\' has to be an integer, 30, or a list, [20, 60].')
            print('\033[0;31;48mTry again!')
            flag = 0
            return time_span, flag

        # Then we check that the time_span is bigger than the epoch time, at least to have one epoch
        tspan = (span[1] - span[0]) / self.c.fs
        if (tspan < self.param['epoch_length']) or (tspan < self.param['detrend_time']):
            print('\033[0;31;48mUnconsistent parameters.')
            print('\033[0;31;48mCheck that time_span is greater than epoch_length and detrend_time.')
            print('\033[0;31;48mExiting...')
            flag = 0
            return time_span, flag
        return span, flag

    def QC(self, plotit=True):
        """Quailty Check (QC):
        Checking Offsets, stds and checks the signal by epochs to detect bad data and mark it.

        It takes the following parameters:
            -signal_offset_limit
            -signal_std_limit
            -epoch_amp_threshold
            -epoch_std_threshold
            -epoch_length

        It updates the following attributes:
            -offsets
            -sigmas
            -bad_records
        """

        p = self.param
        print("\n--------QUALITY CHECK--------")
        print("Current log is:")
        print(self.log)
        print("\nChecking Quality of data with epoch length of ", p['epoch_length'], " seconds.")

        # 1. Checking if data exceeds the signal_offset_limit and signal_std_limit
        #    saving results in self.offsets, self.c.sign
        self.__check_offset_std(plotit)

        # 2. Finding the maximum epochs per channel and printing info.
        #    If data is too small, don't do QC()
        channel_data = np.transpose(self.eeg)
        print("Minutes of data: {minu:3.1f}".format(minu=channel_data.shape[1] / self.c.fs / 60.))
        max_epochs = int((np.floor(channel_data.shape[1] / self.c.fs) - p['epoch_length']) / p['epoch_length'])
        if max_epochs == 0:
            print('\033[0;31;48m Data is too short to be analysed by epochs.')
            print('\033[0;31;48m Exiting...')
            return
        print("Max epochs per channel: ", max_epochs)

        # 3. Identify bad epochs:
        bad_records = []
        print('\n-Epoch Amplitude threshold: ', p['epoch_amp_threshold'])
        print('-Epoch STD threshold: ', p['epoch_std_threshold'], '\n')
        for timeskip in range(0, max_epochs):
            try:
                for channel in range(self.c.num_channels):
                    segment = np.array(np.arange(timeskip * p['epoch_length'] * self.c.fs,
                                                 timeskip * p['epoch_length'] * self.c.fs + p[
                                                     'epoch_length'] * self.c.fs), dtype="int32")
                    signal = channel_data[channel, segment].flatten()
                    fl, maxAmp, STD = self.__check_badepochs(signal)
                    if fl is True:
                        bad_records.append([channel, timeskip, maxAmp, STD])
            except:
                break
        self.bad_records = bad_records

        print("""Found {Nbad} bad channel-epochs out of {total}, or {pc:2.1f}%.
                """.format(Nbad=len(bad_records), total=self.c.num_channels * max_epochs,
                           pc=100 * len(bad_records) / (self.c.num_channels * max_epochs)))
        print("\nBad channel-epochs per channel:")
        for ch in range(self.c.num_channels):
            lista = [x[0] for x in bad_records if x[0] == ch]
            pc = 100 * len(lista) / (self.c.num_channels * max_epochs)
            print("channel {ch:<3} / {name:>5}, N= {ll:<4} (or {pc:2.1f}%)".format(
                ch=ch, name=self.c.electrodes[ch], ll=len(lista), pc=pc))
        print("\n---------QC COMPLETE---------")

    def preprocess(self, pipeline=None):
        """ Preprocess the data
        for a specific input pipeline.
        :param pipeline: list of strings with the name of the functions to preprocess in a specific order.
                         It uses the input parameters of Frida when initialize it.
                         The available functions are (with respective parameters):
                            -reset:            reset EEG to original, unprocessed, raw.
                            -rereference:      rereference the data to a channel, a collection of channels or the
                                               average of all of them together.
                            -detrend:          detrend data linearly for every 'detrend_time' seconds.
                            -bandpassfilter:   bandpass filter the data with a cutoff frequencies of 'low_cutoff_freq'
                                               -'high_cutoff_freq' and 'order'.
                            -remove_line_freq: notch filter the data to remove the power line frequency 'line_freq',
                                               using a quality factor 'Q_notch'.

                         Default: ['reset', 'rereference', 'detrend', 'remove_line_freq', 'bandpassfilter']
        """

        if pipeline is None:
            pipeline = ['reset', 'rereference', 'detrend', 'remove_line_freq', 'bandpassfilter']

        print('---------PREPROCESSING---------')
        print("Pipeline:")
        print(pipeline)
        print("-------------------------------")

        step = 1
        for action in pipeline:
            print("Step", step, ": ", action, " ...")
            exec("self._Frida__" + action + "()")
            self.updatePSD()
            step += 1
            print("-------------------------------")
            print(" ")
        print("Done: Updated Log: ", self.log)
        print(" ")

    def plotEEG(self, spacing=None, fixlim=True, xlim=False):
        """ Plot EEG
        Function to visualize the EEG data
        :param spacing: y axis space between channels. Default: maximum value of detrended EEG (uV). It automatically
        recognizes the scale of the EEG data.
        :param fixlim: fix the y axis accordingly. Default: True.
        :param xlim: limits of time that you want to plot. Default=None, that means that we will plot all data we have.
        """
        c = self.c
        if spacing is None:
            if not self.detrend_flag:
                df_eeg = detrend(self.eeg, axis=0, bp=np.arange(0, self.eeg.shape[0], self.param['detrend_time'] * c.fs, dtype="int32"))
            else:
                df_eeg = self.eeg
            spacing = int(np.max(df_eeg))

        print("\033[1mPlotting EEG channels after this pipeline:\033[0m")
        for n in range(0, len(self.log)):
            print(n + 1, ".", self.log[n])
        print("\n\033[1mFile: \033[0m", c.filepath)

        _, ax = plt.subplots(1, 1, figsize=[12.0, c.num_channels * 0.75])
        for ch in range(1, c.num_channels+1):
            if ch % 2 == 0:
                plt.plot(c.np_time, self.eeg[:, ch-1] + spacing * ch, color='r')
            else:
                plt.plot(c.np_time, self.eeg[:, ch-1] + spacing * ch, color='b')

        plt.grid(which='major')
        plt.grid(which='minor')
        plt.title("data for file " + c.basename + " \n(Spacing=" + str(spacing) + "uV)")
        plt.xlabel('Seconds from ' + c.eegstartdate)
        plt.ylabel("uV, arbitrary refererence")

        plt.yticks(list(range(spacing, (c.num_channels + 1) * spacing, spacing)), c.electrodes)

        if fixlim:
            plt.ylim(0, (c.num_channels + 1) * spacing)
        try:
            plt.legend(c.electrodes, loc='center right', bbox_to_anchor=(1.15, 0.5))
        except:
            print("no electrode labels found")
            plt.legend(list(range(1, c.num_channels + 1)), loc='center right', bbox_to_anchor=(1.2, 0.5))
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
        self.updatePSD()  # Check if necessary.
        print("\033[1mPlotting PSDs after this pipeline:\033[0m")
        for n in range(0, len(self.log)):
            print(n + 1, ".", self.log[n])
        print("\n\033[1mFile: \033[0m", c.filenameroot)

        f = self.PSD['frequencies']
        PSDs = self.PSD['PSDs']
        for ix in range(c.num_channels):
            print("\nChannel {chix}: {chname}, STD={stdv:6.1f} uV".format(chix=str(ix + 1), chname=c.electrodes[ix],
                                                                          stdv=np.std(self.eeg[:, ix])))

            PSD = PSDs[ix]
            _, ax = plt.subplots(1, 1, figsize=[12.0, 2.5])
            # plt.plot(f, 10 * np.log10(PSD + 1e-12), f, -np.ones(len(f)) * 15, f, np.ones(len(f)) * 15, linewidth=1)
            plt.hlines(15, 0, len(f))
            plt.hlines(-15, 0, len(f))
            plt.plot(f, 10 * np.log10(PSD + 1e-12))
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

        plt.figure(figsize=(12.0, 3.))
        for ix in range(c.num_channels):
            plt.plot(f, 10 * np.log10(PSDs[ix] + 1e-12))
        plt.hlines(15, 0, len(f))
        plt.hlines(-15, 0, len(f))
        plt.xlabel('frequency [Hz]')
        plt.ylabel('10log10 (PSD [uV^2/Hz])')
        plt.ylim(-30., 30)
        plt.xlim(0, c.fs / 2)
        plt.legend(c.electrodes, loc='center right', bbox_to_anchor=(1.15, 0.5))
        plt.title('All channels PSDs')
        plt.grid()
        plt.show()

    def __check_badepochs(self, signal, verbose=False):
        """
        Check each of the channels independently and returns a flag if the data is bad.
        :param signal: single channel data
        :param verbose: print the info
        :return: flag, amplitude and STD for every channel.
        """

        flag = False
        w = np.max(np.abs(detrend(signal)))
        std = np.std(detrend(signal))

        if w > self.param['epoch_amp_threshold']:
            flag = True

        if std > self.param['epoch_std_threshold']:
            flag = True

        if flag & verbose:
            print("Bad at checkSignal: Threshold of ", self.param['epoch_amp_threshold'], " exceeded: max Amp is", w)
            print("Bad at checkSignal: Threshold of ", self.param['epoch_std_threshold'], " exceeded: STD is", std, "uV")

        return flag, w, std

    def __reset(self):
        """Resets the attribute self.eeg to the original, unprocessed/raw data."""

        self.eeg = self.eeg_original.copy()
        self.detrend_flag = False
        self.log.append("EEG reset on " + time.strftime("%Y-%m-%d %H:%M"))

    def __check_offset_std(self, plotit=True):
        """
        Check the offsets for every EEG channel (np_eeg) and mark it with an (*) if the thresholds are exceeded.
        """
        p = self.param

        print("Offset limit: ", p['signal_offset_limit'])
        print("STD limit: ", p['signal_std_limit'])

        offsets = [np.mean(self.eeg, axis=0)[ch] / 1000 for ch in range(0, self.eeg.shape[1])]  # mV
        offset_flag = np.ones(len(offsets))
        sigmas = [np.std(self.eeg, axis=0)[ch] for ch in range(0, self.eeg.shape[1])]  # uV
        sigma_flag = np.ones(len(sigmas))

        for ch in range(self.c.num_channels):
            star_offset = ' '
            star_sigma = ' '
            if np.abs(offsets[ch]) > p['signal_offset_limit']:
                star_offset = '(*)'
                offset_flag[ch] = 0
            if sigmas[ch] > p['signal_std_limit']:
                star_sigma = '(*)'
                sigma_flag[ch] = 0
            print("Channel {ch:<6}: Offset = {off:>6.1f} mV{star1:3} / STD = {std:>6.1f} uV {star2}".format(
                ch=self.c.electrodes[ch], off=offsets[ch], star1=star_offset, star2=star_sigma, std=sigmas[ch]))
        if plotit:
            _, ax = plt.subplots(1, 1, figsize=[12.0, 2.5])
            plt.bar(np.arange(len(offsets)) + 1, offsets)
            plt.xlabel("Channel")
            plt.ylabel("Offset (mV)")
            plt.xticks(list(range(1, (self.c.num_channels + 1))), self.c.electrodes)
            plt.title("Offsets for file " + self.c.basename)
            ax.get_xaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
            ax.get_yaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
            ax.grid(b=True, which='major', color='grey', linewidth=1.0)
            ax.grid(b=True, which='minor', color='lightgrey', linewidth=0.5)
            plt.show()

            _, ax = plt.subplots(1, 1, figsize=[12.0, 2.5])
            plt.bar(np.arange(len(sigmas)) + 1, sigmas, color='r')
            plt.xlabel("Channel")
            plt.ylabel("STD (uV)")
            plt.xticks(list(range(1, self.c.num_channels + 1)), self.c.electrodes)
            plt.title("STDs for file " + self.c.basename)
            ax.get_xaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
            ax.get_yaxis().set_minor_locator(mpl.ticker.AutoMinorLocator())
            ax.grid(b=True, which='major', color='grey', linewidth=1.0)
            ax.grid(b=True, which='minor', color='lightgrey', linewidth=0.5)
            plt.show()

        self.offsets = offsets
        self.sigmas = sigmas

        self.bad_chan = {
            'offset': offset_flag,
            'sigma': sigma_flag
        }

    def __rereference(self):
        """Rereference the data to a channel, a collection of channels or the average ref."""
        p = self.param
        print("Reference electrodes: ", p['reference_electrodes'])
        self.c.reference_electrodes = p['reference_electrodes']

        try:
            sorted_electrode_index = [self.c.electrodes.index(element) for element in p['reference_electrodes']]
            if len(p['reference_electrodes']) == 1:
                ref = self.eeg[:, sorted_electrode_index[0]]
            else:
                print("Computing mean of: ", p['reference_electrodes'])
                ref = np.mean(self.eeg[:, sorted_electrode_index], axis=1)
        except:
            print("Using average reference")
            ref = np.mean(self.eeg, axis=1)

        df_eeg_ref = self.eeg.copy()

        for ch in range(self.eeg.shape[1]):
            df_eeg_ref[:, ch] = self.eeg[:, ch] - ref

        self.eeg = df_eeg_ref
        self.log.append(
            'Reference to: ' + " ".join(p['reference_electrodes']) + " on " + time.strftime("%Y-%m-%d %H:%M"))

    def __detrend(self):
        """ Detrend data linearly in a specific time window, 'detrend_time'."""
        p = self.param
        print("Every ", p['detrend_time'], " seconds")
        df_eeg_det = detrend(self.eeg, axis=0,
                             bp=np.arange(0, self.eeg.shape[0], p['detrend_time'] * self.c.fs, dtype="int32"))

        self.eeg = df_eeg_det
        self.log.append('Detrend data every ' + str(p['detrend_time']) + " s on " + time.strftime("%Y-%m-%d %H:%M"))
        self.detrend_flag = True

    def __bandpassfilter(self):
        """ Band pass filter the data with a butterworth filter with a specific cutoff frequencies"""
        p = self.param
        c = self.c
        print("Cutoff frequencies: ", p['low_cutoff_freq'], "-", p['high_cutoff_freq'])

        nyq = 0.5 * self.c.fs
        normal_cutoff1 = self.param['low_cutoff_freq'] / nyq
        normal_cutoff2 = self.param['high_cutoff_freq'] / nyq
        [b, a] = butter(self.param['order'], [normal_cutoff1, normal_cutoff2], btype='bandpass', analog=False)

        for ch in range(c.num_channels):
            filtered = filtfilt(b, a, self.eeg[:, ch])
            self.eeg[:, ch] = filtered

        self.log.append('Filter at low_cutoff_freq= ' + str(p['low_cutoff_freq']) + " and high_cutoff_freq=" + str(
            p['high_cutoff_freq']) + " on " + time.strftime("%Y-%m-%d %H:%M"))

    def __remove_line_freq(self):
        """Notch filter the data to remove the power line frequency component."""
        c = self.c
        p = self.param
        print("Power line frequency: ", p['line_freq'])
        print("Notch Q-factor: ", p['Q_notch'])

        # w0 = 1.0 * p['line_freq'] / (c.fs / 2.) older version of scipy
        b, a = iirnotch(p['line_freq'], p['Q_notch'], self.c.fs)  # scipy 1.2.0

        for ch in range(c.num_channels):
            filtered = filtfilt(b, a, self.eeg[:, ch])
            self.eeg[:, ch] = filtered
        self.log.append('Notch at ' + str(p['line_freq']) + " with Q=" + str(p['Q_notch']) + " on " + time.strftime(
            "%Y-%m-%d %H:%M"))

    def updatePSD(self):
        """
        it computes the PSDs of the eeg and saves them in the self.PSD dictionary attribute.
        """

        # Welch parameters:
        window = 'hanning'
        nperseg = 10 * self.c.fs
        noverlap = nperseg / 2.
        nfft = None
        detrendit = 'constant'  # or linear
        return_onesided = True
        scaling = 'density'

        PSDs = []
        f = []
        for ix in range(self.c.num_channels):
            # Welch parameters:
            if self.eeg[:, ix].shape[0] < nperseg:
                nperseg = 500  # Default
                noverlap = nperseg / 2.
            f, Pxx_den = welch(self.eeg[:, ix], fs=self.c.fs, window=window, nperseg=nperseg, noverlap=noverlap,
                               nfft=nfft, detrend=detrendit, return_onesided=return_onesided, scaling=scaling, axis=-1)
            PSDs.append(Pxx_den)
        self.PSD = {
            "frequencies": f,
            "PSDs": PSDs,
            "Channels": self.c.electrodes,
            "Log:": self.log}

