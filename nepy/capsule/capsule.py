"""
Simplified version of a Capsule object.

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
    Overview:
    Capsule is a python Object that stores all information extracted from an .easy, .easy.gz, .info
    (if available) or .nedf file. It uses 'easyReader' and 'nedfReader' functions from readers module to read the files.

    Attributes:
        author:          Name of the user. Default: "anonymous"
        capsuledate:     date when the capsule class is created
        eegstartdate:    date when the EEG is recorded
        log:             log containing all the preprocessing steps
        filepath:        datapath (folder where all the data is stored) + filename (basename+extension)
        basename:        name of the file without the extension nor the path
        fs:              sampling frequency
        num_channels:    number of channels
        electrodes:      electrode list
        np_time:         array of the time (seconds)
        np_eeg:          array containing the EEG data. np_eeg.shape[0] is the maxspan and np_eeg.shape[1] are the
                         channels.
        np_eeg_original: raw data. Same shape as np_eeg
        np_acc:          accelerometer data
        np_markers:      markers (if any)
        np_stim:         stim file, just if .nedf file
        filenameroot:    root of the file / path
        offsets:         from Frida checkOffsets()
        sigmas:          from Frida checkOffsets()
        PSD:             from Frida plotPSD()
        bad_records:     y
    """
    def __init__(self, filepath, author="anonymous"):

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
            rdr = easyReader(filepath=filepath, author=author)
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
        self.log = ["Object created: " + self.capsuledate]
        self.filepath = rdr.filepath
        self.basename = rdr.basename
        self.fs = rdr.fs
        self.num_channels = rdr.num_channels
        self.electrodes = rdr.electrodes
        self.np_time = rdr.np_time
        self.np_eeg = rdr.np_eeg
        self.np_eeg_original = rdr.np_eeg.copy()
        self.np_acc = rdr.np_acc
        self.np_markers = rdr.np_markers
        self.np_stim = rdr.np_stim
        self.filenameroot = rdr.filenameroot

        # From Frida
        self.offsets = None
        self.sigmas = None
        self.PSD = None
        self.bad_records = None

    def __repr__(self):
        form = """\033[1mCapsule object created by {author} on {date} from file:\033[0m \n            
            - {fil}
        \033[1m \nCurrent log is:\033[0m \n
            - {log}
        """.format(author=self.author, date=self.capsuledate, fil=self.filepath, log=str(self.log))
        print("\n\033[1mCapsule attributes:\n\033[0m")
        self.listAttributes()
        return form
    
    def __str__(self):
        mess = """\033[1mCapsule object created by {author} on {date} from file:\033[0m

            - {fil}

        \033[1mCurrent log is:\033[0m

            - {log}

        So long and thanks for all the fish.
        """.format(author=self.author, date=self.capsuledate, fil=self.filepath, log=str(self.log))
        print("\n\033[1mCapsule attributes:\n\033[0m")
        self.listAttributes()
        return mess
    
    def listAttributes(self):
        """Convenience function, prints list of attributes."""
        for attr in sorted(self.__dict__.keys()):
            print("-", attr, ":\n", self.__dict__[attr], "\n\n")
