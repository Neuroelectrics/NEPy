"""
This is nedfReader, a class to read ".nedf" files and obtain its data.
It is an object that contains data from nedf file,
and provides methods to obtain this information.

2018 Neuroelectrics Corporation

Created on Tue Feb 14 2018
@author: sergi and giulio (NE)
"""

from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import json
import datetime
import os
import xml.etree.ElementTree as ET


class nedfReader(object):
    """NEDFReader object. Example of use:
            >>> c = nedfReader("nedfdata/20180213122712_Patient01.nedf")
        You must provide the relative or absolute path to the data file.
        In general, output units are uV, uA and seconds (c.np_time) and mm/s^2 (np_acc).
        (see http://wiki.neuroelectrics.com/index.php/Files_%26_Formats)
        The EEG data for processing is kept in .np_eeg and is a numpy array (uV),
        and its shape is (num eeg samples,num channels), e.g., 

            >>> c.np_eeg.shape = (15000,32)

        The stimulation data for processing is kept in .np_stim (uA) and is a numpy array,
        and its shape is (num stim samples,num channels), e.g., 

            >>> c.np_stim.shape = (30000,32)

        The accelerometer data for processing is kept in .np_acc and is a numpy array,
        and its shape is (num acc samples,num acc channels), e.g., 

            >>> c.np_acc.shape = (3000,3)

        The markers are kept in .np_markers and is a numpy array,
        and its shape is (numsamples), e.g., 

            >>> c.np_markers.shape = (15000)

        Metadata information from the nedf header is returned as a json using method get_info. 
        """
    def __init__(self, filepath, author="anonymous"):
        self.filepath = filepath
        self.np_eeg = []  # will hold data in uV
        self.np_stim = []  # holds currents in uA
        self.np_acc = []  # mm/s^2
        self.np_markers = []
        self.np_time = []  # seconds
        self.eegstartdate_unixtime = 0
        self.basename = ""
        self.num_channels = 0
        self.electrodes = []
        self.samplesread = 0
        self.author = author
        enableINFO = False  # If True, prints array shapes and info.

        print()
        """ First we check if file exists with or without file extension."""
        if not os.path.isfile(filepath):
            if filepath.endswith('.nedf'):
                print(""" The path provided is not correct: \n {path} """.format(path=filepath))
                return
            else:
                if not os.path.isfile(filepath+'.nedf'):
                    print(""" The path provided is not correct: \n {path} """.format(path=filepath))
                    print(" Remember that this class only accepts files with .nedf extension ")
                    return
                else:
                    filepath = filepath + '.nedf'
        
        print("File found! {file}".format(file=filepath))
        self.basename = filepath[filepath.rfind("/")+1:].replace(".nedf", "")
        self.filenameroot = filepath[:-5]
        
        file = open(filepath, 'rb')
        """ Here we are reading just the header. 
        By definition of format the header cannot be larger than 10240 bytes"""
        content = file.read(10240)
        content = content.decode("utf-8") 
        nedftitle = content[1:content.find('>')]
        # This is the last character of xml header
        lastindex = content.find('</'+nedftitle+'>') + len('</'+nedftitle+'>')
        content = content[:lastindex]
        try:
            """ We try to convert the header string into a XML structure using ElementTree."""
            root = ET.fromstring(content)
        except:
            print("Nedf header is incorrect. The xml is corrupted")
            return
        """ Using XmlDictConfig we obtain a dictionary from the ET object"""
        xmldict = XmlDictConfig(root)
        self.header = dict(xmldict)
        print("Reading file...")
        """ As we already started reading the file, next read will start from 10240 byte,
        and we will read the whole file at once and then close it. We store what we read
        in a bytearray. This is done for efficiency matters. """
        content2 = file.read()
        file.close()
        self.nedfbytes = bytearray(content2)
        self.nedfbytessize = len(self.nedfbytes)
        """ We initialize the object variables with header values"""
        try:
            self.isaccon = xmldict['AccelerometerData'] == 'ON'
            self.isstimon = 'STIMSettings' in xmldict
            self.num_channels = int(xmldict['EEGSettings']['TotalNumberOfChannels'])
            self.eegstartdate_unixtime = int(xmldict['StepDetails']['StartDate_firstEEGTimestamp'])
            print(self.eegstartdate_unixtime)
            # want this in calendar format
            valuedate=datetime.datetime.fromtimestamp(self.eegstartdate_unixtime /1000.)
            self.eegstartdate=valuedate.strftime('%Y-%m-%d %H:%M:%S')
            print(self.eegstartdate_unixtime)
            # want a simple list of electrodes ordered by channel as in np_eeg
            electrodesDict = dict(xmldict['EEGSettings']['EEGMontage'])
            electrodesDictNumKey = {int(k[7:]): val for (k, val) in electrodesDict.items()}
            self.electrodes = [electrodesDictNumKey[k] for k in sorted(electrodesDictNumKey)]
            
            self.eegtotaltime = int(xmldict['EEGSettings']['EEGRecordingDuration'])
            self.fs = int(xmldict['EEGSettings']['EEGSamplingRate'])
            self.samples = self.eegtotaltime*self.fs
            if self.isstimon:
                self.stimtotaltime = int(xmldict['STIMSettings']['StimulationDuration'])+int(xmldict['STIMSettings']['RampDownDuration'])+int(xmldict['STIMSettings']['RampUpDuration'])+int(xmldict['STIMSettings']['ShamRampDuration'])
                self.samples = self.stimtotaltime*self.fs
            self.np_eeg = (np.zeros(shape=(self.samples, self.num_channels), dtype="float32"))
            if self.isstimon:
                self.np_stim = (np.zeros(shape=(self.samples*2, self.num_channels), dtype="float32"))
            if self.isaccon:
                self.np_acc = (np.zeros(shape=(self.samples//5, self.num_channels), dtype="float32"))
            self.np_markers = (np.zeros(shape=(1), dtype="int32"))
            self.np_time = (np.zeros(shape=(1), dtype="uint64"))

        except Exception as e:
            print("NEDF Header is missing some required fields: " + str(e))
            return
        print("Header information has been correctly retrieved.")

        """ NEDF read is based on nedf file definition and sampling rate.
        Accelerometer sampling rate is 100 samples per second.
        EEG sampling rate is 500 samples per second.
        Stimulation sampling rate is 1000 samples per second.
        Based on that, we iterate taking EEG as reference. """
        supereeg, superstim, superacc, supermarkers, supertime = self.processBytes()
        """Finally we create the numpy arrays from python lists"""

        self.np_acc = np.array(superacc, dtype="float32")
        self.np_eeg = np.array(supereeg, dtype="float32")/1000.  # uV (originally in nV)
        self.np_stim = np.array(superstim, dtype="float32")
        self.np_markers = np.array(supermarkers, dtype="float32")
                
        # create a time column in seconds from beginning of file
        np_time = np.array(supertime)/1000.  # go to seconds
        self.np_time = np.array(np_time, dtype="float32")
            
        print("Finished processing")
        if enableINFO:
            print()
            print("Data has been stored into the following self structures:")
            print()
            print("  > np_acc contains Accelerometer Data and it is shaped", self.np_acc.shape)
            print("  > np_eeg contains EEG Data (uV) and it is shaped", self.np_eeg.shape)
            if self.isstimon:
                print("  > np_stim contains Stimulation Data (uA) and it is shaped", self.np_stim.shape)
            print("  > np_markers contains Markers Data and it is shaped", self.np_markers.shape)
            print("  > np_time contains EEG corresponding Timestamps (s from start) and it is shaped", self.np_time.shape)
            print("  > np_acc contains acc data (mm/s^2) and it is shaped", self.np_time.shape)
            print() 
            print("Header information can be obtained as a json using get_info method or directly accessed:")
            print()
            print("  > self.filepath", self.filepath)
            print("  > self.eegstartdate_unixtime", self.eegstartdate_unixtime)
            print("  > self.basename", self.basename)
            print("  > self.num_channels", self.num_channels)
            if not self.isstimon:
                print("  > self.eegtotaltime", self.eegtotaltime)
            else:
                print("  > self.stimtotaltime", self.stimtotaltime)
            print("  > self.electrodes", "Keys:", list(electrodesDict.keys()))
            print("  > self.author", self.author)


    def processBytes(self):
        self.bytesread = -1
        counteracc = 5
        supereeg = []
        superacc = []
        superstim = []
        supermarkers = []
        supertime = []
        for i in range(self.samples):
            supertime.append(i*2)
            if self.isaccon:
                if counteracc == 5:
                    counteracc = 1
                    accsample = []
                    for j in range(3):
                        if self.nedfbytessize - self.bytesread < 2:
                            print("[Error] Not enough bytes while reading Accelerometer")
                            return supereeg, superstim, superacc, supermarkers, supertime
                        byte1 = self.getByte()
                        byte2 = self.getByte()
                        accvar = byte1*256+byte2
                        if byte1 >= 128:
                            accvar = accvar - 65536 
                        accsample.append(accvar)
                    if len(accsample):
                        superacc.append(accsample)
                else:
                    counteracc += 1
            eegsample = []
            for j in range(self.num_channels):
                if self.nedfbytessize - self.bytesread < 3:
                    print("  > [Error] Not enough bytes while reading EEG")
                    return supereeg, superstim, superacc, supermarkers, supertime
                byte1 = self.getByte()
                byte2 = self.getByte()
                byte3 = self.getByte()
                eegvar = byte1 * 65536 + byte2 * 256 + byte3
                if byte1 >= 128:
                    eegvar = (16777216 * 255) + eegvar - (16777216 * 256)
                eegvar = (eegvar * 2.4 * 1000000000) / 6.0 / 8388607.0
                eegsample.append(eegvar)
            supereeg.append(eegsample)  
            if self.isstimon:
                for s in range(2):
                    stimsample = []
                    for j in range(self.num_channels):
                        if self.nedfbytessize - self.bytesread < 3:
                            print("[Error] Not enough bytes while reading Stimulation")
                            return supereeg, superstim, superacc, supermarkers, supertime
                        byte1 = self.getByte()
                        byte2 = self.getByte()
                        byte3 = self.getByte()
                        stimvar = byte1 * 65536 + byte2 * 256 + byte3
                        if byte1 >= 128:
                            stimvar = (16777216 * 255) + stimvar - (16777216 * 256)
                        stimsample.append(stimvar)
                    superstim.append(stimsample)

            if self.nedfbytessize - self.bytesread < 4:
                print("[Error] Not enough bytes while reading markers")
                return supereeg, superstim, superacc, supermarkers, supertime
            byte1 = self.getByte()
            byte2 = self.getByte()
            byte3 = self.getByte()
            byte4 = self.getByte()
            marker = byte1 * 16777216 + byte2 * 65536 + byte3 * 256 + byte4
            supermarkers.append(marker)
            self.samplesread = i
        return supereeg, superstim, superacc, supermarkers, supertime

    def getByte(self):
        self.bytesread += 1
        return self.nedfbytes[self.bytesread]

    def get_info(self):
        """ returns a json with NEDF header information. The information of the json can be
            retrieved following this example of use:

            Being 'info' the result of this method:
            >>> headerdict = json.loads(info)
            >>> root = headerdict.keys()[0]   #the root element
            >>> print headerdictprint[root]['EEGSettings']['EEGMontage']
            <<< {u'Channel17': u'PO3', u'Channel16': u'CP2', u'Channel15': u'Cz', 
                u'Channel14': u'FC2', u'Channel13': u'Fz', u'Channel12': u'AF3', 
                u'Channel11': u'Fp1', u'Channel10': u'Fp2', u'Channel19': u'Oz', 
                u'Channel18': u'O1', u'Channel3': u'CP6', u'Channel2': u'T8', u'Channel1': u'P8', 
                u'Channel7': u'C4', u'Channel6': u'F4', u'Channel5': u'F8', u'Channel4': u'FC6', 
                u'Channel9': u'AF4', u'Channel8': u'P4', u'Channel22': u'Pz', u'Channel23': u'CP1', 
                u'Channel20': u'O2', u'Channel21': u'PO4', u'Channel26': u'C3', u'Channel27': u'F3', 
                u'Channel24': u'FC1', u'Channel25': u'P3', u'Channel28': u'F7', u'Channel29': u'FC5', 
                u'Channel31': u'T7', u'Channel30': u'CP5', u'Channel32': u'P7'}

            """
        return json.dumps(self.header)


class XmlDictConfig(dict):
    """
    http://code.activestate.com/recipes/410469-xml-as-dictionary/
    Example usage:

    >>> tree = ElementTree.parse('your_file.xml')
    >>> root = tree.getroot()
    >>> xmldict = XmlDictConfig(root)

    Or, if you want to use an XML string:

    >>> root = ElementTree.XML(xml_string)
    >>> xmldict = XmlDictConfig(root)

    And then use xmldict for what it is... a dict.
    """
    def __init__(self, parent_element):
        if list(parent_element.items()):
            self.update(dict(list(parent_element.items())))
        for element in parent_element:
            if len(element):
                # treat like dict - we assume that if the first two tags
                # in a series are different, then they are all different.
                if len(element) == 1 or element[0].tag != element[1].tag:
                    aDict = XmlDictConfig(element)
                # treat like list - we assume that if the first two tags
                # in a series are the same, then the rest are the same.
                else:
                    # here, we put the list in dictionary; the key is the
                    # tag name the list elements all share in common, and
                    # the value is the list itself 
                    aDict = {element[0].tag: XmlListConfig(element)}
                # if the tag has attributes, add those to the dict
                if list(element.items()):
                    aDict.update(dict(list(element.items())))
                self.update({element.tag: aDict})
            # this assumes that if you've got an attribute in a tag,
            # you won't be having any text. This may or may not be a 
            # good idea -- time will tell. It works for the way we are
            # currently doing XML configuration files...
            elif list(element.items()):
                self.update({element.tag: dict(list(element.items()))})
            # finally, if there are no child tags and no attributes, extract
            # the text
            else:
                self.update({element.tag: element.text})