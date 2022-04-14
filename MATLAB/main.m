%
% Description: This is the main script file that instantiates the MIDI2HTTP_Bridge class
% initializes the process configuration and runs the control loop.
% 
% Author: JessyJP (2020) % License: GPLv3 @ LICENCE.md
%

% clear all;clc; close all;

%% Logging
% diary on;
% diary logs.txt;

%% Construct
B = MIDI2HTTP_Bridge;

%% Get Available midi devices and set the midi device bridge
B.selectMidiDeviceInput();

% Matlab how to test with CPU useage.
B.establishServerConnection()

B.handleLogin_();

%% Setup the MIDI to HTTP cue/trigger map
B.MAP = importMidiTriggers(fullfile(pwd,B.midi_HttpProtocolPreset));

%% Prepare the HTTP calls
B.processTriggerMap();
B.log(B);

%% Run the main process loop
B.runLoop();


%% Testing ...
% arrayfun(@(x) B.val2note(x), [0:127])

% diary off
