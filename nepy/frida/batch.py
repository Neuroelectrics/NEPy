"""
Batch processor tools, will apply pipelines properly  to files in a dir
Created on Sat Feb  3 09:20:00 2018
Modified on Tue Nov 6 07:49:55 2018

@author: giulio
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import time
import os

from nepy.frida.frida import Frida


def processDirectory(datadir, author='anonymous', pipeline=None, parameters=None):
    """ Process all .easy or .easy.gz files in data's directory using Frida.
    :param datadir: directory of the folder containing the data.
    :param author: ('anonymous') user.
    :param pipeline: (['referenceData', 'detrendData', 'notch', 'filterDataA2B'])
    :param parameters:
    :return: list of processed and skipped files.

    Example of use:
    >>> [processed, skipped] = processDirectory(datadir)
    """

    if pipeline is None:
        pipeline = ['resetEEG', 'rereferenceData', 'detrendData', 'notch', 'bandpassfilter']

    saved_args = locals()
    print("Running with these arguments:", saved_args)
    print("")

    start_time = time.time()
    processed = []
    skipped = []

    for fil in os.listdir(datadir):
        if fil.endswith((".easy", ".easy.gz", ".nedf")):
            print("\n\n##########################################################################\n")
            filepath = datadir + "/" + fil
            print("         Processing", filepath, )
            print("##########################################################################\n\n")
            try:
                f = Frida(filepath, author=author, parameters=parameters)
                f.QC()
                f.preprocess(pipeline)
                f.QC()
            except:
                print("Something is wrong with this file, skipping...")
                f = 0

            if f != 0:
                processed.append(filepath)
            else:
                skipped.append(filepath)
    elapsed_time = time.time() - start_time

    print("\n\nBatch job complete.")
    print("Processed files:", processed)
    print("Skipped files:", skipped)
    print("\nElapsed time (seconds):", elapsed_time)

    return processed, skipped
