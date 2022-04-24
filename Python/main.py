#!/usr/bin/env python3
# %
# % Description: This is the main script file that instantiates the MIDI2HTTP_Bridge class
# % initializes the process configuration and runs the control loop.
# % 
# % Author: JessyJP (2020) % License: GPLv3 @ LICENCE.md
# %

from operator import truediv;
from MIDI2HTTP_Bridge import MIDI2HTTP_Bridge;
import os;
from tkinter import *;


# Clearing the Screen
# posix is os name for linux or mac
if(os.name == 'posix'):
   os.system('clear')
# else screen will be cleared for windows
else:
   os.system('cls')


def showSplashScreen():
    splash_screen =Tk();
    splash_screen.title("Splash screen");
    splash_screen.geometry("512x512");
   #  splash_screen.iconbitmap('../QueleaPreset/QueleaLogoWithRemote.png');
    splash_screen.overrideredirect(True);


showSplashScreen();

# %% Logging
# % diary on;
# % diary logs.txt;

# %% Construct
B = MIDI2HTTP_Bridge();

# %% Get Available midi devices and set the midi device bridge
B.selectMidiDeviceInput();

# % Matlab how to test with CPU useage.
B.establishServerConnection();

# Handle User Authentication
B.handleLogin_();

# %% Setup the MIDI to HTTP cue/trigger map
B.importMidiTriggers();

# %% Prepare the HTTP calls
B.processTriggerMap();
B.log(B);

# %% Run the main process loop
B.runLoop();


# %% Testing ...
# % arrayfun(@(x) B.val2note(x), [0:127])

# % diary off
