import time
import os.path as op
import warnings

import pandas as pd
import numpy as np

from mne import create_info
from mne.utils import logger, verbose
from mne.channels import read_montage
from mne.io import _BaseRaw


# EEGLAB = .easy * 1e-3
# MNE = EEGLAB * 1e-6
# MNE = .easy * 1e-3 * 1e-6
# MNE = .easy * 1e-9
SCALING_FACTOR = 1e-9

stim_channel = "STI 014"


def _check_easy_fname(fname):
    """Check that .easy file ends in .easy"""
    fmt = str(op.splitext(fname)[-1])
    if fmt != '.easy':
        raise NotImplementedError("EEG file must be .easy format.")


def _check_info_fname(fname):
    """Check that .info file has the same name as .easy file and exists"""
    if not op.isfile(fname):
        raise IOError(
            "Could not find info file. The .info file must have the "
            "same name as the .easy file.", fname)


def _find_index_of_string(list_, string):
    """Finds the index(es) of a substring in a list and returns the first index."""
    indexes = [i for i, s in enumerate(list_) if string in s]
    return indexes[0]


# Make montage_path default to where montages are usually stored.
def _create_info(info_fname, stim_channel, montage=None, montage_path=None):
    """Create mne.Info object using the .info file"""

    # Read the .info file.
    with open(info_fname) as f:
        info_list = f.readlines()
    info_list = [x.strip() for x in info_list]

    # Extract the number of channels.
    n_ch_index = _find_index_of_string(info_list, "Total number of channels:")
    n_channels = info_list[n_ch_index].split(":")[-1]
    n_channels = int(n_channels)

    # Extract sampling rate.
    srate_index = _find_index_of_string(info_list, "EEG sampling rate:")
    srate = info_list[srate_index].split(":")[-1]
    srate = srate.split()[0]  # Remove "Samples/seconds"
    srate = int(srate)

    # Extract channel names.
    ch_names = []
    for c in range(n_channels):
        ch_to_find = "Channel {}".format(c + 1)
        ch_index = _find_index_of_string(info_list, ch_to_find)
        ch_name = info_list[ch_index].split(":")[-1].strip()
        ch_names.append(ch_name)

    # Extract timestamp.
    timestamp_index = _find_index_of_string(info_list, "StartDate")
    timestamp = info_list[timestamp_index].split(":")[-1]
    # Convert from millisecond epoch time to second epoch time.
    timestamp = int(timestamp) / 1000.

    # Create instance of Montage.
    if montage is not None:
        montage = read_montage(kind=montage, ch_names=ch_names, path=montage_path)
    else:
        warnings.warn("Montage is not being applied. "
                      "Channel locations will not be available.")

    # Add stimulus channel to channel names.
    ch_names_for_info = ch_names + [stim_channel]

    # Specify the type of each channel in ch_names_for_info.
    ch_types_for_info = ['eeg' for __ in ch_names] + ['stim']

    # Create instance of Info.
    info = create_info(ch_names_for_info, srate, ch_types_for_info, montage=montage)

    # Add information to the instance of Info.
    info['meas_date'] = [timestamp]
    input_basename = op.basename(info_fname)
    info['filename'] = input_basename
    info['buffer_size_sec'] = 1.0

    return info


# def _read_easy_events(eeg, stim_channel):
#     """Read all of the events except zeros.
#
#     Have to fix the error handling here.
#     """
#     event_types = eeg[stim_channel].unique()
#
#     # Remove zeros because there are zeros in the stim column by default.
#     event_types = event_types[event_types > 0]
#
#     # Check if there are no events.
#     if len(event_types) < 1:
#         logger.info('No events found, returning empty stim channel.')
#         return np.zeros((0,3))
#
#     # Create events nested-list.
#     events = [[i, 0, e] for i, e in enumerate(eeg['STI 014']) if e in event_types]
#
#     return np.asarray(events, dtype='int')


def read_raw_enobio(input_fname, montage=None, montage_path=None,
                    preload=True, verbose=None):
    """Read an Enobio .easy file.

    Parameters
    ----------

    Returns
    -------

    Notes
    -----

    """

    return RawEnobio(input_fname=input_fname, montage=montage,
                     montage_path=montage_path, preload=preload,
                     verbose=verbose)


class RawEnobio(_BaseRaw):
    """Documentation will go here.

    Parameters
    ----------

    Returns
    -------

    Notes
    -----

    See Also
    --------
    """

    @verbose
    def __init__(self, input_fname, montage=None, montage_path=None,
                preload=True, verbose=None):
        input_fname = op.abspath(input_fname)
        basedir = op.dirname(input_fname)
        input_basename = op.basename(input_fname)

        # Get the .info filename.
        info_fname = input_basename.replace(".easy", ".info")
        info_fname = op.join(basedir, info_fname)  # Prepend the path.

        # Check .easy and .info filenames.
        _check_easy_fname(input_fname)
        _check_info_fname(info_fname)

        # Create instance of Info from .info file.
        info = _create_info(info_fname, stim_channel, montage=montage,
                            montage_path=montage_path)

        # Read EEG data from .easy file.
        eeg_header = info['ch_names'][:] + ["timestamp"]
        logger.info('Reading {}'.format({input_fname}))
        # pd.read_csv turns out to be faster than np.loadtxt and np.genfromtxt.
        unscaled_eeg = pd.read_csv(input_fname, sep='\t', header=None,
                                   dtype=np.float64, names=eeg_header)
        # Scale the EEG data.
        chs_to_scale = info['ch_names'][:-1]  # Slice to exclude stimulus channel.
        eeg = unscaled_eeg[chs_to_scale] * SCALING_FACTOR
        eeg[['STI 014', 'timestamp']] = unscaled_eeg[['STI 014', 'timestamp']]


        # # Do we need to find events here?
        # events = _read_easy_events(eeg, stim_channel)

        # Data should not include timestamps.
        data = eeg.values.T[:-1]

        if preload is False:
            warnings.warn("Data will be preloaded. preload=False is "
                          "not supported yet.")

        super(RawEnobio, self).__init__(
            info, data, filenames=[input_fname], verbose=verbose)
