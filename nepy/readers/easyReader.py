"""
This is easyReader, a class to read “.easy” files and obtain their data.
It is an object that contains data from easy and info files (the latter if available),
and provides methods to obtain this information.

2018 Neuroelectrics Corporation

Created on Tue Feb 14 2018 modified on Mon Sept 24 2018 (roser)
@author: giulio (NE)
"""

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import os
import time
import datetime
import pandas as pd
 

class easyReader(object):
    """
        Example of use:

            >>> c = easyReader("easydata/20180213122712_Patient01.easy")

        You must provide the relative or absolute path to the data file.
        The EEG data for processing is kept in .np_eeg and is a numpy array,
        and its shape is (num eeg samples,num channels), e.g., 

            >>> c.np_eeg.shape = (15000, 32)

        The accelerometer data for processing is kept in .np_acc and is a numpy array,
        and its shape is (num acc samples,num acc channels), e.g., 

            >>> c.np_acc.shape = (3000, 3)

        The markers are kept in .np_markers and is a numpy array,
        and its shape is (numsamples), e.g.,

            >>> c.np_markers.shape = 15000
        """
  
    def __init__(self, filepath, author="anonymous", verbose=True):

        print("\033[1mInitializing in file path: \033[0m ", filepath)

        # Let us find the extension, or exit if not recognized:
        if filepath.endswith(".easy.gz"):
            filenameroot = filepath[:-8]
            basename = os.path.basename(filepath)[:-8]
            extension = "easy.gz"
            print("\033[1mProcessing: \033[0m", basename)
            print("\033[1mFilenameroot: \033[0m", filenameroot)
            print("\033[1mExtension: \033[0m", extension)
            
        elif filepath.endswith(".easy"):
            extension = "easy"
            filenameroot = filepath[:-5]
            basename = os.path.basename(filepath)[:-5]
            print("\033[1mProcessing: \033[0m", basename)
            print("\033[1mFilenameroot: \033[0m", filenameroot)
            print("\033[1mExtension: \033[0m", extension)
        else: 
            print("\033[91m ERROR @capsule __init__: proposed file has wrong extension. Exiting. \033[0m")
            return
            
        print(" ")

        self.capsuledate = time.strftime("%Y-%m-%d %H:%M")
        self.log = ["capsule created: " + self.capsuledate]
        self.filepath = filepath
        self.basename = basename
        self.extension = extension
        self.author = author
        self.filenameroot = filenameroot
        self.infofilepath = filenameroot + ".info"
        self.fs = 500.
        # Initialize all empty attributes:
        self.acc_data = False
        self.electrodes = []
        self.num_channels = None
        self.eegstartdate = None
        self.np_time = []
        self.np_eeg = []
        self.np_stim = []
        self.np_acc = []
        self.np_markers = []

        # Try to read info file
        self.info_flag = self.__get_info(verbose=verbose)
        # then read data part, easy file
        self.__get_l0_data(verbose=verbose)

    def listAttributes(self):
        """Convenience function, prints list of attributes."""
        for attr in sorted(self.__dict__.keys()):
            print("-", attr, ":\n", self.__dict__[attr], "\n\n")
        print("_______________________________________________________________")
    
    def __get_info(self, verbose=True):
        """ 
        Read .info file, basically to grab electrode names.
        """
        if verbose:
            print("_______________________________________________________________")
            print("\033[1mReading info file ...\033[0m")
        electrodes = []
        try:
            data_file = open(self.infofilepath, 'r')
            for line in data_file.readlines():
                if verbose:
                    print(line[:-1])
                if "Channel " in line[:-1]:
                    electrodes.append(line.split()[-1])
                if "Accelerometer data: " in line[:-1]:
                    self.acc_data = True
                    break
            self.electrodes = electrodes
            flag = 0
            if verbose:
                print(".info file found and read.\n")
        except OSError:
            print("\033[93m Warning! .info file not found! Using standard values... \033[0m")
            print("Reading ", self.filepath, "to get numchannels....\n")
            df = pd.read_csv(self.filepath, delim_whitespace=True, nrows=5)

            cols = df.iloc[:, :].shape[1]
            if (cols == 13) or (cols == 25) or (cols == 37):
                numchannels = df.iloc[:, :].shape[1] - 5
                self.acc_data = True
            elif (cols == 10) or (cols == 22) or (cols == 34):
                numchannels = df.iloc[:, :].shape[1] - 2
            else:
                print('There is an error with the .easy format.')
                print('Number of columns mismatch with the expected for any of the devices')
                print('Exiting...')
                return
            print("numchannels .......", numchannels)
            self.electrodes = ["Ch"+str(x) for x in range(1, 1+numchannels)]
            flag = 1
        self.num_channels = len(self.electrodes) 
            
        return flag

    def __get_l0_data(self, verbose=True):
        """
        Method to grab easy data and set to uV. Data is stored in numpy arrays frame
        """
        if verbose:
            print("_______________________________________________________________")
            print("\033[1mReading:", self.basename, '.', self.extension, '\n \033[0m')
        df = pd.read_csv(self.filepath, delim_whitespace=True, header=None)
        cols = df.iloc[:, :].shape[1]
        if (cols == 13) or (cols == 25) or (cols == 37):
            num_channels = df.iloc[:, :].shape[1] - 5
            self.acc_data = True
        elif (cols == 10) or (cols == 22) or (cols == 34):
            num_channels = df.iloc[:, :].shape[1] - 2
        else:
            print('There is an error with the .easy format.')
            print('Number of columns mismatch with the expected for any of the devices')
            print('Exiting...')
            return

        if num_channels != self.num_channels:
            print("numchannels", num_channels)
            print("self.num_channels", self.num_channels)
            print("\033[93m Something is wrong with numchannels in infofile...\033[0m")
        
        # grab first entry of last dataframe column (unix timestamp in ms)
        timestamp = df[df.columns[-1]][0] 
        value = datetime.datetime.fromtimestamp(timestamp/1000)
        eegstartdate = value.strftime('%Y-%m-%d %H:%M:%S')

        # name dataframe columes using electrodes, etc
        if self.acc_data:
            df.columns = self.electrodes + ['ax', 'ay', 'az'] + ['markers', 'unix_time']
        else:
            df.columns = self.electrodes + ['markers', 'unix_time']
        
        df.iloc[:, 0:num_channels] = df.iloc[:, 0:num_channels]/1000  # now in uV

        if verbose:
            print("Number of channels detected:", num_channels)
            print("First sample recorded :", eegstartdate, "\n")
            print(" L0 raw data data in uV")
            print(df.describe())
        
        # assign attributes
        self.eegstartdate = eegstartdate
        self.np_eeg = np.array(df, dtype="float32")[:, 0:num_channels]
        # create a time column in seconds from beginning of file
        df['t'] = (df['unix_time']-df['unix_time'][0])/1000.  # go to seconds
        self.np_time = np.array(df['t'], dtype="float32")
        self.log.append("Got raw L0_data on " + time.strftime("%Y-%m-%d %H:%M"))
        self.np_acc = np.array(df, dtype="float32")[:, num_channels:num_channels+3]
        if self.acc_data:
            self.np_markers = np.array(df, dtype="float32")[:, num_channels+3]
        else:
            self.np_markers = np.array(df, dtype="float32")[:, num_channels]
        
        return
