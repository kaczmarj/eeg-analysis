%% Setup
formatSpec = '%s';
delimiter = '\n';
info_file = '/Users/jakubkaczmarzyk/Documents/analysis_paper/data/0_easy/20160910083157_NEU_001_song_Protocol 1.info';

%% Put contents of file into array
fileID = fopen(info_file);
info = textscan(fileID, formatSpec, 'Delimiter', delimiter);
fclose(fileID);
info = info{1};

%% Extract number of channels
idx = strfind(info,'Total number of channels:');
[idx, ~] = find(not(cellfun('isempty',idx)));
NChannels = info{idx};

NChannels = strsplit(NChannels, ':');
NChannels = textscan(NChannels{2}, '%f');
NChannels = NChannels{1};

%% Extract sampling rate
idx = strfind(info,'EEG sampling rate:');
[idx,~] = find(not(cellfun('isempty',idx)));
EEGSampRate = info{idx};
EEGSampRate = strsplit(EEGSampRate,':');
EEGSampRate = textscan(EEGSampRate{2},'%f');
EEGSampRate = EEGSampRate{1};

%% Get channel names

% Did older versions of .info files have "Position:"?
ChannelList = cell([NChannels,1]);
for n=1:NChannels
    % Find row with "Position:"
    idx = strfind(info,'Position:');
    % If there is a row with "Position:"
    if ~isempty(find(not(cellfun('isempty',idx))))
        idx = strfind(info,'Position:');
        [idx,~] = find(not(cellfun('isempty',idx)));
        Channel = info{idx(n)};
        k = strfind(Channel,':');
        Channel = Channel(k+2:end);
    % If there is no row with "Position:"
    else
        % Find "Channel <n>:".
        idx = strfind(info,['Channel ',num2str(n),':']);
        % Get index of the row with "Channel <n>:".
        [idx,~] = find(not(cellfun('isempty',idx)));
        Channel = info{idx};
        % Take the part of the string after ":" (i.e. the channel name)
        Channel = strsplit(Channel,':');
        Channel = Channel{2};

    end
    % Add the channel name to the list of channel names.
    ChannelList{n} = Channel;
end

%% Get number of EEG samples
idx = strfind(info,'Number of records of EEG:');
[idx,~] = find(not(cellfun('isempty',idx)));
Pnts = info{idx};  % Pnts means the number of samples! (EEG Points)
Pnts = strsplit(Pnts,':');
Pnts = textscan(Pnts{2},'%f');
Pnts = Pnts{1};

%% Get Trigger information
Triggers = 9;

idx = strfind(info,'Trigger information');
[idx,~] = find(not(cellfun('isempty',idx)));
% It looks like there was an older .info version. Maybe that one had
% a row "Position:".
if isempty(idx) % In the new info not implemented yet
    % No trigger information
    Trigs = [];
else
    Trigs = cell([Triggers,1]);
    for n = 1:Triggers
        trig = info{idx+1+n};  % What's going on here?
        trig = trig(2:end);
        Trigs{n} = trig;
    end
end


%% Testing
cd('/Users/jakubkaczmarzyk/Documents/analysis_paper')
data = load('data/0_easy/20160910083157_NEU_001_song_Protocol 1.easy');

%% Testing (continued)
data_1 = data ./ 1000;
















