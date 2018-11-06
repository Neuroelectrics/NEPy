"""
Functions to run the FRIDA test.

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


def resetEEG(c=None):
    """
    Resets the attribute self.np_eeg to the original, unprocessed data.
    :param c: Capsule object
    :return: c class with updated np_eeg to original and update log.
    """

    if c is None:
        print("\033[91mERROR @frida resetEEG(): Missing capsule argument in reset function.\033[0m")
        return
    print("\n... Reseting EEG ...")
    c.np_eeg = c.np_eeg_original.copy()
    c.log.append("- EEG reset on " + time.strftime("%Y-%m-%d %H:%M"))

    return c


def checkOffsets(c=None, offset_limit=1., std_limit=15., plotit=True):
    """
    Check the offsets for every EEG channel (np_eeg) and mark it with an (*) if the thresholds are exceeded.
    :param c: Capsule object
    :param offset_limit: offset limit in mV. For testboard the default is 1. uV. Default = 1. mV
    :param std_limit: standard deviation limit in uV. Default = 15. uV
    :param plotit: flag to plot or not the result in a bar graph.
    :return: summary of the channels that are above or not those limits.
    """

    if c is None:
        print("\033[91mERROR @frida_func checkOffsets(): Missing capsule argument in check offsets function.\033[0m")
        return
    print("\n... Checking Offsets ...")
    print("Offset limit: ", offset_limit)
    print("STD limit: ", std_limit)

    offsets = [np.mean(c.np_eeg, axis=0)[ch] / 1000 for ch in range(0, c.np_eeg.shape[1])]  # mV
    sigmas = [np.std(c.np_eeg, axis=0)[ch] for ch in range(0, c.np_eeg.shape[1])]  # uV

    for ch in range(c.num_channels):
        star_offset = ' '
        star_sigma = ' '
        if np.abs(offsets[ch]) > offset_limit:
            star_offset = '(*)'
        if sigmas[ch] > std_limit:
            star_sigma = '(*)'
        print("Channel {ch:<6}: Offset = {off:>6.1f} mV{star1:3} / STD = {std:>6.1f} uV {star2}".format(
            ch=c.electrodes[ch], off=offsets[ch], star1=star_offset, star2=star_sigma, std=sigmas[ch]))

    if plotit:
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

    c.offsets = offsets
    c.sigmas = sigmas

    return c


def rereferenceData(c=None, reference_electrodes=None):
    """
    Rereference the data to a channel, a collection of channels or the average ref.
    :param c: Capsule object.
    :param reference_electrodes: list of electrodes (or a single electrode) in electrode list. It can also be the
            average by typing "Ave" or any other string. Default = ['Cz']
    :return: c class with a re-referenced data and updated log.
    """

    if c is None:
        print("\033[91mERROR @frida_func rereferenceData(): Missing capsule argument in rereference function.\033[0m")
        return

    if reference_electrodes is None:
        reference_electrodes = ['Cz']

    print("\n... Rereferencing data ...")
    print("Reference electrodes: ", reference_electrodes)
    c.reference_electrodes = reference_electrodes

    try:
        sorted_electrode_index = [c.electrodes.index(element) for element in reference_electrodes]
        if len(reference_electrodes) == 1:
            ref = c.np_eeg[:, sorted_electrode_index[0]]
        else:
            print("Computing mean of: ", reference_electrodes)
            ref = np.mean(c.np_eeg[:, sorted_electrode_index], axis=1)
    except:
        print("Using average reference")
        ref = np.mean(c.np_eeg, axis=1)

    df_eeg_ref = c.np_eeg.copy()

    for ch in range(c.np_eeg.shape[1]):
        df_eeg_ref[:, ch] = c.np_eeg[:, ch] - ref

    c.np_eeg = df_eeg_ref
    c.log.append('- Reference to: ' + " ".join(reference_electrodes) + " on " + time.strftime("%Y-%m-%d %H:%M"))

    return c


def detrendData(c=None, detrend_time=10.):
    """
    Detrend capsule data linearly in a specific time window, detrend_time
    :param c: Capsule object
    :param detrend_time: time window to detrend the data. Default: 10. seconds
    :return: Capsule object with detrended data and updated log.
    """

    if c is None:
        print("\033[91mERROR @frida_func DetrendData(): Missing capsule argument in detrend function.\033[0m")
        return

    print("\n... Detrending data ...")
    print("Every ", detrend_time, " seconds")
    c.detrendtime = detrend_time
    df_eeg_det = detrend(c.np_eeg, axis=0, bp=np.arange(0, c.np_eeg.shape[0], detrend_time * c.fs, dtype="int32"))

    c.np_eeg = df_eeg_det
    c.log.append('- Detrend data every ' + str(detrend_time) + " s on " + time.strftime("%Y-%m-%d %H:%M"))

    return c


def butter_bandpass_filter(data, fs, cutoff1, cutoff2, order=5):
    """
    Butterworth band-pass filter.
    :param data: data that you want to filter
    :param fs: sampling frequency
    :param cutoff1: lower cutoff frequency
    :param cutoff2: higher cutoff frequency
    :param order: order of the filter
    :return: filtered data
    """
    nyq = 0.5 * fs
    normal_cutoff1 = cutoff1 / nyq
    normal_cutoff2 = cutoff2 / nyq
    [b, a] = butter(order, [normal_cutoff1, normal_cutoff2], btype='bandpass', analog=False)
    y = lfilter(b, a, data)
    return y


def bandpassfilter(c=None, fL=2., fH=45., order=5):
    """
    Band pass filter the data with a butterworth filter with a specific cutoff frequencies
    :param c: Capsule object
    :param fL: Low cutoff frequency
    :param fH: High cutoff frequency
    :param order: order of the butterworth filter.
    :return: capsule object with filtered data and updated log.
    """

    if c is None:
        print("\033[91mERROR @frida_func bandpassfilter(): Missing capsule argument in bandpassfilter function.\033[0m")
        return

    print("\n... Filtering data ...")
    print("Cutoff frequencies: ", fL, "-", fH)

    for ch in range(c.num_channels):
        filtered = butter_bandpass_filter(c.np_eeg[:, ch], c.fs, cutoff1=fL, cutoff2=fH, order=order)
        c.np_eeg[:, ch] = filtered

    c.fL = fL
    c.fH = fH
    c.log.append('- Filter at fL= ' + str(fL) + " and fH=" + str(fH) + " on " + time.strftime("%Y-%m-%d %H:%M"))

    return c


def notch(c=None, fline=50., Q=30.):
    """
    Notch filter the data to remove the power line frequency component.
    :param c: Capsule object
    :param fline: Power line frequency. Boston: 60HZ, Spain: 50Hz (Default).
    :param Q: Q-factor for the notch filter.
    :return: return a capsule object with updated filtered data and log.
    """

    if c is None:
        print("\033[91mERROR @frida_func notch(): Missing capsule argument in notch function.\033[0m")
        return

    print("\n... Notch filtering ...")
    print("Power line frequency: ", fline)
    print("Notch Q-factor: ", Q)

    w0 = 1.0 * fline / (c.fs / 2.)
    b, a = iirnotch(w0, Q)

    for ch in range(c.num_channels):
        filtered = lfilter(b, a, c.np_eeg[:, ch])
        c.np_eeg[:, ch] = filtered
    c.np_eeg = c.np_eeg
    c.fline = fline
    c.Q = Q
    c.log.append('- Notch at ' + str(fline) + " with Q=" + str(Q) + " on " + time.strftime("%Y-%m-%d %H:%M"))

    return c


def plotEEG(c=None, spacing=200, fixlim=True, xlim=False):
    """
    Function to visualize the eeg file
    :param c: Capsule object
    :param spacing: y axis space between channels. Default: 200uV
    :param fixlim: fix the y axis accordingly. Default: True.
    :param xlim: limits of time that you want to plot. Default=None, that means that we will plot all data we have.
    :return: EEG plot.
    """

    if c is None:
        print("\033[91mERROR @frida_func plotEEG(): Missing capsule argument in plot EEG function.\033[0m")
        return

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


def getPSD(c=None, ix=None):
    """
    Generates PSD for a given capsule and channel.
    :param c: Capsule object
    :param ix: Channel index (array index, i.e., ch-1)
    :return: returns the frequency and the PSD array for the input channel
    """
    window = 'hanning'
    nperseg = 10 * c.fs
    noverlap = nperseg / 2.
    nfft = None
    detrendit = 'constant'  # or linear
    return_onesided = True
    scaling = 'density'

    f, Pxx_den = welch(c.np_eeg[:, ix], fs=c.fs, window=window, nperseg=nperseg, noverlap=noverlap, nfft=nfft,
                       detrend=detrendit, return_onesided=return_onesided, scaling=scaling, axis=-1)
    return f, Pxx_den


def capsulePSD(c=None, plotit=True):
    """
    function that computes (and plots) the PSD of np_eeg channels of capsule.
    :param c: Capsule object
    :param plotit: flag to plot the PSDs for each channel or not.
    :return: capsule object with updated PDS attribute
    """

    if c is None:
        print("\033[91mERROR @frida_func plotPSD(): Missing capsule argument in plotPSD function.\033[0m")
        return

    print("\033[1mPlotting PSDs after this pipeline:\033[0m")
    for n in range(0, len(c.log)):
        print(n + 1, ".", c.log[n])
    print("\n\033[1mFile: \033[0m", c.filenameroot)

    PSDs = []
    f = []
    for ix in range(c.num_channels):
        print("\nChannel {chix}: {chname}, STD={stdv:6.1f} uV".format(chix=str(ix + 1), chname=c.electrodes[ix],
            stdv=np.std(c.np_eeg[:, ix])))

        f, PSD = getPSD(c, ix)
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

    c.PSD = {
        "frequencies": f,
        "PSDs": PSDs,
        "Channels": c.electrodes,
        "Log:": c.log}

    return c

