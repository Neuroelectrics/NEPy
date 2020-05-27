"""
This file contains all the ground truth to perform the nepy basic tests.
It is linked to the folder testdata.

Please copy and paste the path of the test data in the testdata variable below.
The original test data is located in this path:

    '//antares.starlab.es//Phact//6 - Neuroelectrics//6.3 - Development & Production//NEPy//
    1- Project//1.4- WPs Working Area//DATA//testfiles'

Every field in the easyTestData and nedfTestdata is a file in the folder.
If you want to perform the nepy tests with other data please make sure that you store the necessary information in
this file following the format:

- each FIELD in the dictionaries is the ID of the file. In this case we have Enobio and StarStim files with different
number of channels and with/without .info file data. We have decided to name the files's ID with 'E' if it an Enobio
file and 'SS' if it StarStim. The number behind corresponds to the number of channels and if there's no info file it
says _noinfo. But be free to follow any other convention.

- Each of the files is at the same time another dictionary, so we have nested dicitonaries to define the ground data
to test. Each of this subdictionaries (corresponding to a file in the testdata folder) contains at the same time
different fields to fill if you change the testing files:

    ['filename']: name of the file, as it is, without the extension. Click on the file name or press F2 and you get it.

    ['chanlist']: the worse field to fill if you want to test a 32 channel device. Just copy the channel list in the
                    order that appears in the info file. IF you don't have the info file then it easy. There's a
                    function defined at the beginning of this file called 'elist_generator', you just need to call it,
                    the only argument of the function is the number of channels of the device. If you have a .nedf file
                    without .info file then you can't perform the test. Sorry. We can try to fix it in the future.

    ['first_easy_row']: this field is really important regarding the .nedf files. To test a .nedf file you need to have
                        the corresponding .easy file so you can copy the first row information. Just copy and paste
                        the first row of the .easy file as an array. Recommendation to not make if by hand:
                        open the easy file in Notepad++, copy the first row in a new Notepad++ text file. Then, find
                        and replace all the tabs '\t' by a coma and space ', '. Then you have it!
    ['more_rows']: optional field for a more exhaurstive testing. The rows are in the same format as the
                   'first_easy´_row' field, but there's an extra index at the beginning that specifies the row index.
                   If you edit it with Notepad++ it is easy to see the index in the left. (In the code we already take
                   into account that the first element of Notebook is not 0, as it is for Python)
                   It is important that it is a two dimensional array, even though you just input one extra row.

    ['num_samples']: to find the number of samples you also need the .easy file. Find how many rows the .easy file has
                    and copy that number to this field.

IMPORTANT NOTES:
    - to perform tests of .easy files you don't need the .info file
    - to perform tests of the .nedf file you need the respective .easy and .info file to can access to its data.
    - to perform a capsule test you need AT LEAST one .easy and one .nedf file in the folder.
    - it is really important to do the frida test that there is a file called fake_easy.easy in the testfiles folder.
    This .easy file is made out of this code:

            f = open('fake_easy.easy', 'w+')
            for i in range(500*60):
                f.write("{0}\t{0}\t{0}\t{0}\t{0}\t{0}\t{0}\t{0}\t1\t1\t1\t2\t1500000000000\n".format(i))
            f.close()


2019 Neuroelectrics Barcelona
@author: R Sanchez (roser.sanchez@neuroelectrics.com)

"""

# Copy and paste the directory of your compute of the testfiles.
testpath = '//antares.starlab.es//Phact//6 - Neuroelectrics//6.3 - Development & Production//NEPy//1- Project//' \
           '1.4- WPs Working Area//DATA//testfiles'


def elist_generator(n):
    """
    Generates an electrode list for the files that doesn't have .info file.
    Format: [Ch1, Ch2, Ch3, ...]
    """
    elist = []
    for n in range(1, n + 1):
        elist.append('Ch{0}'.format(n))
    return elist


# This is a global class with all the information regarding the test files.
easyTestData = {
    'E8': {
        'filename': '20181214090159_testboard_E8',
        'chanlist': ['F6', 'F4', 'F2', 'Fz', 'F1', 'F3', 'F5', 'Cz'],
        'first_easy_row': [311660, -598239, 223827, -279712, -266408, -31280, -512743, 195360, 0, 0, 0, 0,
                           1544774518507],
        'more_rows': [[321, 321626, -593519, 226497, -278329, -264215, -26512, -511217, 195646, 29, 186, 9443, 0,
                       1544774519607],
                      [216, 316095, -595665, 226211, -279426, -266933, -31280, -514078, 191926, -29, 225, 9326, 0,
                       1544774519397]],
        'num_samples': 90000
    },
    'E8_noinfo': {
        'filename': '20181214090159_testboard_E8_noinfo',
        'chanlist': elist_generator(8),
        'first_easy_row': [311660, -598239, 223827, -279712, -266408, -31280, -512743, 195360, 0, 0, 0, 0,
                           1544774518507],
        'more_rows': [[321, 321626, -593519, 226497, -278329, -264215, -26512, -511217, 195646, 29, 186, 9443, 0,
                       1544774519607]],
        'num_samples': 90000
    },
    'E20': {
        'filename': '20181214093909_testboard_E20',
        'chanlist': ['P7', 'P4', 'Cz', 'Pz', 'P3', 'P8', 'O1', 'O2', 'T8', 'F8', 'C4', 'F4', 'Fp2', 'Fz', 'C3', 'F3',
                     'Fp1', 'T7', 'F7', 'EXT'],
        'first_easy_row': [139808, -589799, -81920, -68140, -144815, -8487, -210952, 371503, 344133, -368595, -58746,
                           -8153, -103759, 27704, -190210, 22792, 77438, -118064, -296402, -118446, 147, 0, 9326, 0,
                           1544776748908],
        'num_samples': 90000
    },
    'E20_noinfo': {
        'filename': '20181214093909_testboard_E20_noinfo',
        'chanlist': elist_generator(20),
        'first_easy_row': [139808, -589799, -81920, -68140, -144815, -8487, -210952, 371503, 344133, -368595, -58746,
                           -8153, -103759, 27704, -190210, 22792, 77438, -118064, -296402, -118446, 147, 0, 9326, 0,
                           1544776748908],
        'num_samples': 90000
    },
    'E32': {
        'filename': '20181214100347_testboard_E32',
        'chanlist': ['P7', 'P4', 'Cz', 'Pz', 'P3', 'P8', 'O1', 'O2', 'T8', 'F8', 'C4', 'F4', 'Fp2', 'Fz', 'C3',
                     'F3', 'Fp1', 'T7', 'F7', 'Oz', 'PO4', 'FC6', 'FC2', 'AF4', 'CP6', 'CP2', 'CP1', 'CP5', 'FC1',
                     'FC5', 'AF3', 'PO3'],
        'first_easy_row': [458145, -81157, -131940, -96845, -172805, -117349, 54502, 55694, -762319, 344038, -168275,
                           139856, 27990, -379085, 92554, -480032, -104188, -278282, 95748, -136184, -314331, 335121,
                           -138711, 293064, -7152, -364637, 372219, -536203, 103998, -452899, -6723, -732517, 0, 0, 0,
                           0, 1544778225268],
        'num_samples': 90000
    },
    'E32_noinfo': {
        'filename': '20181214100347_testboard_E32_noinfo',
        'chanlist': elist_generator(32),
        'first_easy_row': [458145, -81157, -131940, -96845, -172805, -117349, 54502, 55694, -762319, 344038, -168275,
                           139856, 27990, -379085, 92554, -480032, -104188, -278282, 95748, -136184, -314331, 335121,
                           -138711, 293064, -7152, -364637, 372219, -536203, 103998, -452899, -6723, -732517, 0, 0, 0,
                           0, 1544778225268],
        'num_samples': 90000
    },
    'SS8': {
        'filename': '20181214105515_testboard_SS8',
        'chanlist': ['F3', 'Cz', 'P8', 'O2', 'F6', 'P3', 'P4', 'C6'],
        'first_easy_row': [-204610, 177621, 34523, -133132, -178766, -74434, -377798, 225782, 451, 107, 9747, 0,
                           1544781314293],
        'num_samples': 90589
    },
    'SS8_noinfo': {
        'filename': '20181214105515_testboard_SS8_noinfo',
        'chanlist': elist_generator(8),
        'first_easy_row': [-204610, 177621, 34523, -133132, -178766, -74434, -377798, 225782, 451, 107, 9747, 0,
                           1544781314293],
        'num_samples': 90589
    },
    'SS20': {
        'filename': '20181214103654_testboard_SS20',
        'chanlist': ['P8', 'T8', 'F8', 'F4', 'C4', 'P4', 'Fp2', 'Fp1', 'Fz', 'Cz', 'O1', 'Oz', 'O2', 'Pz', 'P3','C3',
                     'F3', 'F7', 'T7', 'P7'],
        'first_easy_row': [-336885, -232172, -535392, -179004, -16069, -417661, -323152, -195360, -285482, -533056,
                           -444746, 287199, -174093, -97703, 2527, -395011, 91457, -660038, -720453, 60987, 0, 0, 0, 0,
                           1544780213963],
        'num_samples': 90216
    },
    'SS20_noinfo': {
        'filename': '20181214103654_testboard_SS20_noinfo',
        'chanlist': elist_generator(20),
        'first_easy_row': [-336885, -232172, -535392, -179004, -16069, -417661, -323152, -195360, -285482, -533056,
                           -444746, 287199, -174093, -97703, 2527, -395011, 91457, -660038, -720453, 60987, 0, 0, 0, 0,
                           1544780213963],
        'num_samples': 90216
    },
    'SS32': {
        'filename': '20181214102845_testboard_SS32',
        'chanlist': ['P8', 'T8', 'CP6', 'FC6', 'F8', 'F4', 'C4', 'P4', 'AF4', 'Fp2', 'Fp1', 'AF3', 'Fz', 'FC2', 'Cz',
                     'CP2', 'PO3', 'O1', 'Oz', 'O2', 'PO4', 'Pz', 'CP1', 'FC1', 'P3', 'C3', 'F3', 'F7', 'FC5', 'CP5',
                     'T7', 'P7'],
        'first_easy_row': [-404930, -325393, -486087, -207853, -47731, -865268, -215578, -506162, -38719, -746822,
                           -564146, -367069, -724983, -51307, -507021, -350713, -609541, -25367, -669384, -407791,
                           101947, -353765, -125265, -628519, -1015901, -246048, -590038, -233697, -324678, -363349,
                           -433969, -494527, 0, 0, 0, 0, 1544779724964],
        'num_samples': 90367
    },
    'SS32_noinfo': {
        'filename': '20181214102845_testboard_SS32_noinfo',
        'chanlist': elist_generator(32),
        'first_easy_row': [-404930, -325393, -486087, -207853, -47731, -865268, -215578, -506162, -38719, -746822,
                           -564146, -367069, -724983, -51307, -507021, -350713, -609541, -25367, -669384, -407791,
                           101947, -353765, -125265, -628519, -1015901, -246048, -590038, -233697, -324678, -363349,
                           -433969, -494527, 0, 0, 0, 0, 1544779724964],
        'num_samples': 90367
    },
}

nedfTestData = {
    'E8_nedf': {
        'filename': '20181214090159_testboard_E8',
        'chanlist': ['F6', 'F4', 'F2', 'Fz', 'F1', 'F3', 'F5', 'Cz'],
        'first_easy_row': [311660, -598239, 223827, -279712, -266408, -31280, -512743, 195360, 0, 0, 0, 0,
                           1544774518507],
        'more_rows': [[321, 321626, -593519, 226497, -278329, -264215, -26512, -511217, 195646, 29, 186, 9443, 0,
                       1544774519607],
                      [216, 316095, -595665, 226211, -279426, -266933, -31280, -514078, 191926, -29, 225, 9326, 0,
                       1544774519397]],
        'num_samples': 90000
    },
    'E20_nedf': {
        'filename': '20181214093909_testboard_E20',
        'chanlist': ['P7', 'P4', 'Cz', 'Pz', 'P3', 'P8', 'O1', 'O2', 'T8', 'F8', 'C4', 'F4', 'Fp2', 'Fz', 'C3', 'F3',
                     'Fp1', 'T7', 'F7', 'EXT'],
        'first_easy_row': [139808, -589799, -81920, -68140, -144815, -8487, -210952, 371503, 344133, -368595, -58746,
                           -8153, -103759, 27704, -190210, 22792, 77438, -118064, -296402, -118446, 147, 0, 9326, 0,
                           1544776748908],
        'num_samples': 90000
    },
    'E32_nedf': {
        'filename': '20181214100347_testboard_E32',
        'chanlist': ['P7', 'P4', 'Cz', 'Pz', 'P3', 'P8', 'O1', 'O2', 'T8', 'F8', 'C4', 'F4', 'Fp2', 'Fz', 'C3',
                     'F3', 'Fp1', 'T7', 'F7', 'Oz', 'PO4', 'FC6', 'FC2', 'AF4', 'CP6', 'CP2', 'CP1', 'CP5', 'FC1',
                     'FC5', 'AF3', 'PO3'],
        'first_easy_row': [458145, -81157, -131940, -96845, -172805, -117349, 54502, 55694, -762319, 344038, -168275,
                           139856, 27990, -379085, 92554, -480032, -104188, -278282, 95748, -136184, -314331, 335121,
                           -138711, 293064, -7152, -364637, 372219, -536203, 103998, -452899, -6723, -732517, 0, 0, 0,
                           0, 1544778225268],
        'num_samples': 90000
    },
    'SS8_nedf': {
        'filename': '20181214105515_testboard_SS8',
        'chanlist': ['F3', 'Cz', 'P8', 'O2', 'F6', 'P3', 'P4', 'C6'],
        'first_easy_row': [-204610, 177621, 34523, -133132, -178766, -74434, -377798, 225782, 451, 107, 9747, 0,
                           1544781314293],
        'num_samples': 90589
    },
    'SS20_nedf': {
        'filename': '20181214103654_testboard_SS20',
        'chanlist': ['P8', 'T8', 'F8', 'F4', 'C4', 'P4', 'Fp2', 'Fp1', 'Fz', 'Cz', 'O1', 'Oz', 'O2', 'Pz', 'P3','C3',
                     'F3', 'F7', 'T7', 'P7'],
        'first_easy_row': [-336885, -232172, -535392, -179004, -16069, -417661, -323152, -195360, -285482, -533056,
                           -444746, 287199, -174093, -97703, 2527, -395011, 91457, -660038, -720453, 60987, 0, 0, 0, 0,
                           1544780213963],
        'num_samples': 90216
    },
    'SS32_nedf': {
        'filename': '20181214102845_testboard_SS32',
        'chanlist': ['P8', 'T8', 'CP6', 'FC6', 'F8', 'F4', 'C4', 'P4', 'AF4', 'Fp2', 'Fp1', 'AF3', 'Fz', 'FC2', 'Cz',
                     'CP2', 'PO3', 'O1', 'Oz', 'O2', 'PO4', 'Pz', 'CP1', 'FC1', 'P3', 'C3', 'F3', 'F7', 'FC5', 'CP5',
                     'T7', 'P7'],
        'first_easy_row': [-404930, -325393, -486087, -207853, -47731, -865268, -215578, -506162, -38719, -746822,
                           -564146, -367069, -724983, -51307, -507021, -350713, -609541, -25367, -669384, -407791,
                           101947, -353765, -125265, -628519, -1015901, -246048, -590038, -233697, -324678, -363349,
                           -433969, -494527, 0, 0, 0, 0, 1544779724964],
        'num_samples': 90367
    },
}

nedfOnlyStimTestData = {
    'SS8_1': {
        'filename': '20200527203558_testboard_no_eeg_SS8',
        'num_stim_samples': 21569,
        'stim_rows' : [
            {
            'row' : 45,
            'data' : [-13,	-1,	-1,	-1,	-1,	-1,	13,	-1]
            },
            {
            'row' : 9029,
            'data' : [327,	-1,	-1,	-1,	-1,	-1,	-327,	-1]
            }
        ]
    },
    'SS8_2': {
        'filename': '20200527210001_testboard_no_eeg_SS8',
        'num_stim_samples': 12472,
        'stim_rows' : [
            {
            'row' : 257,
            'data' : [77,	-19,	-19,	-19,	-19,	-1,	-1,	-1]
            },
            {
            'row' : 10289,
            'data' : [654,	-162,	-162,	-163,	-163,	-1,	-1,	-1]
            }
        ]
    }
}
