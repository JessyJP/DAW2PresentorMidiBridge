#!/usr/bin/env python3
# % 
# % Author: JessyJP (2020) % License: GPLv3 @ LICENCE.md
# %

# Extra functions needed in Python

def getTimeNow(): 
    from datetime import datetime;

    # datetime object containing current date and time
    now = datetime.now()
    
    # print("now =", now)

    # dd/mm/YY H:M:S
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    # print("date and time =", dt_string)	
    return dt_string;

def uigetfile(configuration_filepath):
    # from tkinter import Tk;     # from tkinter import Tk for Python 3.x
    from tkinter.filedialog import askopenfilename;

    # Tk().withdraw(); # we don't want a full GUI, so keep the root window from appearing
    filename = askopenfilename(); # show an "Open" dialog box and return the path to the selected file

    return filename;

def importConfigurationSettings(filePath):
    from configparser import ConfigParser
    from itertools import chain

    parser = ConfigParser()
    with open(filePath) as lines:
        lines = chain(("[top]",), lines)  # This line does the trick.
        parser.read_file(lines)

        # for section in parser.sections():
        #     print({section: dict(parser[section]) })
    return parser;

def formattedDisplayText(object):
    import os;
    outputStr = 80*"-"+os.linesep;
    temp = dir(object)
    for fn in temp:
        outputStr =  outputStr+"    "+fn+' : '+str(object.__getattribute__(fn))+os.linesep;
    outputStr =outputStr+80*"-"+os.linesep;
    return outputStr;


# Test function calls 
# uigetfile("c:\Users\JessyJP\Dropbox\Projects Workfiles & Software\DAW2PresentorMidiBridge\daw2server_settingsConfiguration.ini" )
