import time
import os.path as op
import warnings

import pandas as pd
import numpy as np

from mne import create_info
from mne.utils import logger, verbose
from mne.channels import read_montage
from mne.io import _BaseRaw

from mne.io.utils import _read_segments_file

# EEGLAB = .easy * 1e-3
# MNE = EEGLAB * 1e-6
# MNE = .easy * 1e-3 * 1e-6
# MNE = .easy * 1e-9
SCALING_FACTOR = 1e-9

stim_channel = "STI 014"


def _check_easy_fname(fname):
    """Helper to check that .easy file ends in .easy."""
    fmt = str(op.splitext(fname)[-1])
    if fmt != '.easy':
        raise NotImplementedError("EEG file must be .easy format.")


def _check_info_file(fname):
    """Helper to check that .info file exists."""
    if not op.isfile(fname):
        warnings.warn(
            ".info file not found. EEG data cannot be imported from .easy file "
            "without the .info file. In the future, the use of default values "
            "will be supported if the .info file is not available. " +
            str(fname))
        return False
    return True


def _find_index_of_string(list_, string):
    """Finds the index(es) of a substring in a list and returns the first
    index."""
    indexes = [i for i, s in enumerate(list_) if string in s]
    return indexes[0]


# Make montage_path default to where montages are usually stored.
def _create_info(info_fname, stim_channel, info_exists=True, montage=None,
                 montage_path=None):
    """Create instance of mne.Info using the .info file."""
    if montage_path is None:
        montage_path = op.join(op.dirname(__file__), 'data', 'montages')

    if not info_exists:
        # Add default values here.
        pass
    else:
        # Read the .info file into a list.
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

    Add _read_segment_file(self, data, idx, fi, start, stop, cals, mult)

    Parameters
    ----------

    Returns
    -------

    Notes
    -----


    """

    @verbose
    def __init__(self, input_fname, montage=None, montage_path=None,
                preload=True, stim_channel=stim_channel, verbose=None):
        input_fname = op.abspath(input_fname)
        basedir = op.dirname(input_fname)
        input_basename = op.basename(input_fname)

        # Get the .info filename.
        info_fname = input_basename.replace(".easy", ".info")
        info_fname = op.join(basedir, info_fname)  # Prepend the path.

        # Check .easy and .info filenames.
        _check_easy_fname(input_fname)
        info_exists = _check_info_file(info_fname)

        # Create instance of mne.Info from .info file.
        self.info = _create_info(info_fname, stim_channel,
                                 info_exists=info_exists, montage=montage,
                                 montage_path=montage_path)

        # Read EEG data from .easy file.
        eeg_header = self.info['ch_names'][:] + ["timestamp"]
        logger.info('Reading {}'.format({input_fname}))
        # pd.read_csv turns out to be faster than np.loadtxt and np.genfromtxt.
        unscaled_eeg = pd.read_csv(input_fname, sep='\t', header=None,
                                   dtype=np.float64, names=eeg_header)
        # Scale the EEG data.
        chs_to_scale = self.info['ch_names'][:-1]  # Exclude stimulus channel.
        eeg = unscaled_eeg[chs_to_scale] * SCALING_FACTOR
        # Note that the timestamp is not being added to the scaled EEG data.
        eeg[stim_channel] = unscaled_eeg[stim_channel]

        last_samps = len(eeg)
        self._event_ch = eeg[stim_channel].values

        # Transpose to be compatible with MNE-Python.
        self.data = eeg.values.T

        if preload is False:
            warnings.warn("Data will be preloaded. preload=False is "
                          "not supported for data in .easy files.")

        super(RawEnobio, self).__init__(
            self.info, self.data, filenames=[input_fname], verbose=verbose)

    def _read_segment_file(self, data, idx, fi, start, stop, cals, mult):
        """Read a chunk of raw data. This method has not been tested yet."""
        _read_segments_file(self, data, idx, fi, start, stop, cals, mult,
                            dtype=np.float32, trigger_ch=self._event_ch,
                            n_channels=self.info['nchan'] - 1)
