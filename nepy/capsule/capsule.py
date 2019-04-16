"""
Simplified version of a Capsule object: http://git.starlab.es/Sanchez/NEpy_original/tree/master/nepy/capsule
Capsule is a python object that contains all the informaiton regarding the EEG Neuroelectrics' files.
Frida deals just with this data structure of EEG.

2018 Neuroelectrics Corporation

Created on Mon Nov 5 9:45:59 2018
@author: roser (NE)
"""

import time
import os

from nepy.readers.easyReader import easyReader
from nepy.readers.nedfReader import nedfReader


class Capsule(object):
    """
    Description:
    Capsule is a python Object that stores all information extracted from an .easy, .easy.gz, .info
    (if available) or .nedf file. It uses 'easyReader' and 'nedfReader' functions from readers module to read the files.

    Attributes:
        good_init        Flag to say that the file has been read correctly by the readers.
        author:          Name of the user. Default: "anonymous"
        capsuledate:     date when the capsule class is created
        eegstartdate:    date when the EEG is recorded
        filepath:        datapath (folder where all the data is stored) + filename (basename+extension)
        basename:        name of the file without the extension nor the path
        fs:              sampling frequency
        num_channels:    number of channels
        electrodes:      electrode list
        np_time:         array of the time (seconds)
        np_eeg:          array containing the EEG data. np_eeg.shape[0] is the maxspan and np_eeg.shape[1] are the
                         channels.
        np_acc:          accelerometer data
        np_markers:      markers (if any)
        np_stim:         stim file, just if .nedf file.
        filenameroot:    root of the file / path
        offsets:         from Frida check_offset_std() in QC()
        sigmas:          from Frida check_offset_std() in QC()
        PSD:             from Frida plotPSD()
        bad_records:     from Frida check_badepochs in QC()
    """
    def __init__(self, filepath, author="anonymous", verbose=True):

        # 1. Does the file exist? If not, provide help.
        if os.path.isfile(filepath):
            print("Found the file:", filepath)
        else:
            print("\nFile \033[91m{0}\033[0m NOT found".format(filepath))
            print("\nMake sure the following variables are set correctly. See this example: ")
            print("     -nepypath: C:\\Users\\yourname\\Documents\\Git\\nepy_support")
            print("     -nepypath: C:\\Users\\yourname\\Documents\\Git\\nepy_support\\sampledata")
            print("     -filename*: 20170807135459_W012_V1_EYC.easy.gz")
            print("\n*Don't forget, when you copy the filename, the extension (.easy / .easy.gz) should be included.")
            print("\nTry it again!")
            print("\033[91mERROR @capsule __init__: proposed file not found. Exiting.\033[0m")
            self.good_init = False
            return 
        
        # 2. Find extension, and read file with help of readers.
        if filepath.endswith(".easy.gz") or filepath.endswith(".easy"):
            rdr = easyReader(filepath=filepath, author=author, verbose=verbose)
            self.good_init = True
        elif filepath.endswith(".nedf"):
            rdr = nedfReader(filepath=filepath, author=author)
            self.good_init = True
        else:
            print("\nWrong extension! Make sure the file is one of these types: .easy, .easy.gz, .nedf")
            print("\n\033[91mERROR @capsule __init__: proposed file has wrong extension. Exiting.\033[0m \n")
            self.good_init = False
            return

        # 3. Set class attributes
        # From user
        self.author = author

        # From Readers
        self.capsuledate = time.strftime("%Y-%m-%d %H:%M")
        self.eegstartdate = rdr.eegstartdate
        self.filepath = rdr.filepath
        self.basename = rdr.basename
        self.fs = rdr.fs
        self.num_channels = rdr.num_channels
        self.electrodes = rdr.electrodes
        self.np_time = rdr.np_time
        self.np_eeg = rdr.np_eeg
        self.np_acc = rdr.np_acc
        self.np_markers = rdr.np_markers
        self.np_stim = rdr.np_stim
        self.filenameroot = rdr.filenameroot
    
    def listAttributes(self):
        """Convenience function, prints list of attributes."""
        for attr in sorted(self.__dict__.keys()):
            print("-", attr, ":\n", self.__dict__[attr], "\n\n")
