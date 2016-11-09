# eeg-analysis-workflows

Benefits of MNE-Python
----------------------

- Script-based analysis enhances reproducibility by allowing researchers to share their exact analytic workflow. (This is relevant for mne.Annotations, see below)



Notes to self
-------------

Making annotations in MNE-Python looks tedious (you have to specify the onset and duration of unwanted portions of data). But this might be a benefit. If you specify the onsets and durations in a separate text file, you can share that file with other researchers, so they know exactly what you did to your data. This helps reproducibility and peer review. It would not be hard to import this text file to automatically create the annotations.
