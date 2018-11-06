"""
Simplified version of a Frida (object format).

2018 Neuroelectrics Corporation

Created on Mon Nov 5 11:39:39 2018
@author: roser (NE)
"""

from nepy.capsule.capsule import Capsule
import nepy.frida.functions as ffun


class Frida(object):

    def __init__(self, filepath, author="anonymous"):
        c = Capsule(filepath, author)
        self.c = c

    def QC(self, grab_seconds=10., offset_limit=1., std_limit=15., plotit=True):

        print("\n... QUALITY CHECK ...")
        print("Current log is:")
        print(self.c.log)

        ffun.checkOffsets(c=self.c, offset_limit=offset_limit, std_limit=std_limit, plotit=plotit)

        print("\nChecking Quality of data with epoch length of ", grab_seconds, " seconds.")
        print("Amplitude threshold (uV)= ", self.QCthreshold)
        print("STD limit of (uV)       = ", self.QCsmax)

        channel_data = np.transpose(self.np_eeg)  # np.array(data["EEG_ECSeq"][0][seq])
        # print channel_data.shape

        #       print " Num samples:, ", channel_data.shape[1]
        print("Minutes of data: {minu:3.1f}".format(minu=channel_data.shape[1] / fs / 60.))
        Maxtimeskips = int((np.floor(channel_data.shape[1] / fs) - GrabSeconds) / GrabSeconds)
        print("Maxtimeskips", Maxtimeskips)

        badRecords = []
        for timeskip in range(0, Maxtimeskips):

            try:
                for channel in range(num_channels):
                    Segment = np.array(
                        np.arange(timeskip * GrabSeconds * fs, (timeskip) * GrabSeconds * fs + GrabSeconds * fs),
                        dtype="int32")
                    Signal = channel_data[channel, Segment].flatten()
                    fl, maxAmp, STD = checkSignal(Signal, threshold=self.QCthreshold, smax=self.QCsmax)
                    if fl is True:
                        badRecords.append([channel, timeskip, maxAmp, STD])
            except:
                break
        self.badRecords = badRecords

        print(""" Found {Nbad} bad channel-epochs out of {total}, or {pc:2.1f}%.
                """.format(Nbad=len(badRecords), total=num_channels * Maxtimeskips,
                           pc=100 * len(badRecords) / (num_channels * Maxtimeskips)))
        print("\nBad channel-epochs per channel:")
        for ch in range(num_channels):
            lista = [x[0] for x in badRecords if x[0] == ch]
            pc = 100 * len(lista) / (num_channels * Maxtimeskips)
            # print "channel",ch, "(",self.electrodes[ch], "), N=",len(lista), "(or", pc,"%)"
            print("channel {ch:<3} / {name:>5}, N= {l:<4} (or {pc:2.1f}%)".format(
                ch=ch, name=self.electrodes[ch], l=len(lista), pc=pc))
        print("\nQC complete.")



