% Use this script to time various steps in EEG analsis with EEGLAB.
% None of the functions being timed modify the EEG data, and the same is
% true for the code that times MNE-Python functions. 

addpath('/Users/jakubkaczmarzyk/Documents/MATLAB/eeglab13_6_5b'); eeglab;
cd('/Users/jakubkaczmarzyk/Documents/analysis_paper/timing');

%% Load file.
% Clear EEGLAB's memory.
STUDY = []; CURRENTSTUDY = 0; ALLEEG = []; EEG=[]; CURRENTSET=[];

% Load raw .set file.
raw_fname = '../data/1_raw/20160910083157_NEU_001_song_Protocol 1.easy.set';
EEG = pop_loadset('filename', raw_fname);

%% High-pass filter.
filt_h_pass = @() pop_eegfiltnew(EEG, 0.5, []);
timeit(filt_h_pass)  % 1.3824 seconds

%% Low-pass filter.
filt_l_pass = @() pop_eegfiltnew(EEG, [], 40.);
timeit(filt_l_pass)  % 0.1290 seconds

%% Run ICA.
ica = @() pop_runica(EEG, 'icatype', 'runica', 'dataset', 1, 'options', {'extended' 1}, 'chanind', (1:32) );
timeit(ica)  % 384.0098 seconds == 6 minutes 24 seconds
