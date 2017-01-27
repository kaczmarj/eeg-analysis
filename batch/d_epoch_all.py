#!/usr/bin/env python
"""Epoch EEG data in a directory, and save the output in another directory.

Command line example:

"""
import argparse
from glob import glob
from os import path as op

from mne import set_log_level, io, make_fixed_length_events, Epochs
from mne.utils import ProgressBar


EVENT_ID = {
    'rest1': 1,
    'rest2': 2,
    'read': 3,
    'sudoku': 4,
    'audiobook': 5,
    'dvd': 6,
    'song': 7,
}


def epoch_all(main_event_id=EVENT_ID):
    """Epoch EEG data and save the epochs.

    Parameters
    ----------
    input : str
        Directory of files to be epoched.
    """

    parser = argparse.ArgumentParser(prog='1_filter_all.py',
                                     description=__doc__)
    parser.add_argument('-i', '--input', type=str, required=True,
                        help="Directory of files to be epoched.")
    parser.add_argument('-o', '--output', type=str, required=True,
                        help="Directory in which to save filtered files.")
    parser.add_argument('-ed', '--epoch-duration', type=float, required=True,
                        help='Duration of each epoch.')
    parser.add_argument('-co', '--crop-out', type=float, default=0.,
                        help='Duration to crop in the beginning of recording.')
    parser.add_argument('-v', '--verbose', type=str, default='error')
    args = parser.parse_args()

    input_dir = op.abspath(args.input)
    output_dir = op.abspath(args.output)
    epoch_duration = args.epoch_duration
    crop_out = args.crop_out

    if not op.exists(input_dir):
        sys.exit("Input directory not found.")
    if not op.exists(output_dir):
        sys.exit("Output directory not found.")

    set_log_level(verbose=args.verbose)


    input_fnames = op.join(input_dir, '*.fif')
    input_fnames = glob(input_fnames)
    n_files = len(input_fnames)
    failed_files = []  # Put fnames that create errors in here.

    print("Epoching {n} files ...".format(n=n_files))
    # Initialize a progress bar.
    progress = ProgressBar(n_files, mesg='Epoching')
    progress.update_with_increment_value(0)
    for fname in input_fnames:

        raw = io.read_raw_fif(fname, preload=True, add_eeg_ref=False,
                              verbose=args.verbose)

        # Get the condition and event_id of this file.
        this_event_id = {}
        for key in main_event_id:
            if key in op.split(fname)[1]:
                this_event_id[key] = main_event_id[key]
                this_condition = key

        try:
            # Make the events ndarray.
            this_events = make_fixed_length_events(
                raw, this_event_id[this_condition], start=crop_out, stop=None,
                duration=epoch_duration)

            # Create the instance of Epochs.
            this_epochs = Epochs(
                raw, this_events, event_id=this_event_id, tmin=0.0,
                tmax=epoch_duration, baseline=None, preload=True, detrend=0,
                add_eeg_ref=False)

            # Append -epo to filename and save.
            save_fname = op.splitext(op.split(fname)[-1])[0]
            this_epochs.info['filename'] = save_fname
            this_epochs_fname = op.join(output_dir, this_epochs.info['filename'])
            this_epochs.save(this_epochs_fname + '.fif')

        except ValueError:
            failed_files.append(op.split(fname)[-1])

        # Update progress bar.
        progress.update_with_increment_value(1)

    print("\nFailed on:")
    for file_ in failed_files:
        print(file_)


if __name__ == "__main__":
    epoch_all()
