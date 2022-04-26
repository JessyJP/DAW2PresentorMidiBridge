#!/usr/bin/env python3
# %
# % Classname:   MIDI2HTTP_Bridge 
# % Description: This is the main class that bridges MIDI to HTTP trigger
# % translation for projection software and a DAW. 
# % 
# % Author: JessyJP (2020) % License: GPLv3 @ LICENCE.md
# %
# % Summary: This service program was developed to connect Reaper and Quelea but
# % should work between any MIDI and HTTP capable software.
# % 
# % Code summary: 
# % The constructor is called and all relevant settings are loaded.
# % "daw2server_settingsConfiguration.ini" contains all relevant configuration settings.
# % "*_Preset_cues.csv" contains the trigger mapping.
# % Both files are pain text and can and should be edited to suit the user purposes.
# % Then Connection checks are performed and then the control loop is ran.
# %

# ==============================================================
# Standard libraty imports

# System and os import
from ast import alias;
import sys , os ;
# Import the time library
import time;
# Library for HTTP requests
import requests;
# Import the math library
from numpy import mod;
from math import floor;
# Import pandas library to handle DataFrame data object
import pandas as pd;


# Custom functions imports
# from ExtraFunctions import *;
from ExtraFunctions import uigetfile,getTimeNow,importConfigurationSettings,formattedDisplayText;


# ==============================================================
# The application class definitiotn
class MIDI2HTTP_Bridge:

    # properties # % Properties to be imported from file
        # % Get the platform the service is currently runing on
        platform=os.name;

        # % The preset file
        midi_BridgeName="";
        midi_HttpProtocolPreset="";
        
        # % The name of the DAW or midi player
        DAW_name="";
        # %DAw(Reaper) audio interface sampling rate
        DAW_AudioFreqencyHz=0;
        # %DAw(Reaper) audio interface samples per buffer, i.e. buffer size
        DAW_InterfaceBufferSamples=0;

        # % Server Connection properties
        Server_Name="";
        Server_autodiscover="";
        Server_Protocol="";
        Server_IP="";
        Server_ControlPort=0;
        Server_password="";
        Server_loggedIN=False;
    # end

    # properties # Additional Properties
        rootPath = os.path.abspath(os.path.dirname(__file__));
        configuration_filepath = "."+os.sep+"daw2server_settingsConfiguration.ini";# % Default file name
        # % MIDI device(bridge name)
        midiDevice=[];
        # % Limiter
        inLoopFPS=[];
        # % State flag for the sate of the program can also be used as a
        # % control flag 
        STATE_FLAG="";
        diagnosticMode=False;

        # serverURL="";# This will not be needed
        MAP=[];
    # end
   

    # % Constructor methods  # methods
        # % Constructor
        def __init__(B):
            isdeployed = False;
            B.STATE_FLAG="Initialization";
            # % Print welcome message
            B.printWelcome();
            
            if not(isdeployed):#% Check if it is deployed to adjust the root paths
                B.configuration_filepath = "."+B.configuration_filepath;
            # end
            # Construct the absolute path for the configuration file
            B.configuration_filepath = os.path.abspath(os.path.join(B.rootPath,B.configuration_filepath));
            # % Check if file exists otherwise locate it
            if not(os.path.exists(B.configuration_filepath)):
                B.configuration_filepath = uigetfile(B.configuration_filepath);                
            # end
            B.log("Get Configuration file: "+B.configuration_filepath);
            # % Get the raw file properties
            iniConfigurationPaser = importConfigurationSettings(B.configuration_filepath);
            # % Assign the file properties
            B.loadFileProperties(iniConfigurationPaser);
            # % Compute the application loop FPS limiter to match the cycle
            # % rate of the DAW's audio interface (it will be approximate)
            B.inLoopFPS = B.DAW_AudioFreqencyHz/B.DAW_InterfaceBufferSamples;
            
            if not(isdeployed):#% Check if it is deployed to adjust the root paths
                B.midi_HttpProtocolPreset = "."+B.midi_HttpProtocolPreset;
            # end
            # Construct the absolute path for the http protocol triggers file
            B.midi_HttpProtocolPreset = os.path.abspath(os.path.join(B.rootPath,B.midi_HttpProtocolPreset));

            B.STATE_FLAG="Configured";
        # end

        # % Loggin and output function
        def log(self,msg):
            if not(isinstance(msg,str)):
               msg=formattedDisplayText(msg)+os.linesep;
            # end

            # % To standart output
            print(msg);
        # end
        
        # % Prints the welcome message
        def printWelcome(B):
            welcome = [
                    "% Classname:   MIDI2HTTP_Bridge ",
                    "% Description: This is the main class that bridges MIDI to HTTP trigger",
                    "% translation for projection software and a DAW.",
                    "% ",
                    "% Author: JessyJP (2020) % License: GPLv3 @ LICENCE.md",
                    ""
                ];
                
            for r in range(1,len(welcome)):
                print(welcome[r]);
            # end

            B.log("Log started at: "+getTimeNow());

            return welcome;
        # end

        # % Function for loading the imported file properties
        def loadFileProperties(B,iniConfig):
            bPropNms = dir(B);
            bPropNms_lower = [x.lower() for x in bPropNms];
             # % Loop over all imported property strings
            for key in iniConfig["top"]:
                try:
                    value = iniConfig["top"][key];
                    # Check if the property name is valid
                    if not(key.lower() in bPropNms_lower):
                        raise Exception("");
                    else:
                        # Locate the correct capitalization of the proert
                        key = bPropNms[bPropNms_lower.index(key.lower())];

                    # Remove double quotes from strings
                    value = value.strip('\"');

                    # Cast in the correct format 
                    value = type(B.__getattribute__(key)) (value);
                    # Assign the value 
                    B.__setattr__(key,value);
                    B.log("Assign Property: ["+key+"] = ["+str(B.__getattribute__(key))+"]");
            
                except:# %(err) Could catch the original message and merge it the one in the catch
                    errorMsg = "Not found Property:["+key+"]"+" Associated data:["+str(value)+"]";
                    B.log(errorMsg); 
                    # error(errorMsg);
                # end
            # end
        # end

    # end


    # % Setup methods
    # methods 

        # % Get MIDI device info
        def getMidiDeviceInfo(B):
            # Import the MIDI module from pygame
            B.log(os.linesep+"MIDI device library:");
            from pygame import midi;
            midi.init();
            B.log(os.linesep+"Get list of midi devices:");
            midiDevInfo = [];
            device_count = midi.get_count()
            # % Get midi device info;
            for device_ID in range(device_count):
                device = midi.get_device_info(device_ID);

                keys = ['interface', 'name', 'is_input', 'is_output', 'opened'];
                info = dict(zip(keys, device));
                info['device_id'] = device_ID;
                info['handle'] = device;
                info['name'] = info['name'].decode();

                
                # If the device is input device 
                if info["is_input"]:
                    B.log("Type: [Input]["+str(device[2])+"] - ID["+str(device_ID)+"] - "+info["name"]);# %display the available midi devices
                elif info["is_output"]:
                    B.log("Type: [Ouput]["+str(device[2])+"] - ID["+str(device_ID)+"] - "+info["name"]);# %display the available midi devices
                else:
                    B.log("Devoce type not recognized! - "+info["name"]);
                # end
                midiDevInfo.append(info);

            midi.quit() # THIS LINE FIXED IT
            return midiDevInfo;
        # end
        
        # % Select the MIDI device connection
        def selectMidiDeviceInput(B):
            import numpy as np;
            # % Get midi device info
            devInfo = B.getMidiDeviceInfo();

            # % Check if the imported midi name can be found otherwise load
            # % the one from the list
            preselectedMidiDevice = False;
            for dev in devInfo:
                if (B.midi_BridgeName == dev["name"]) and dev["is_input"]:
                    preselectedMidiDevice = True;
                    break;

            # If the preslected MIDI device is not found ask for selection       
            if not(preselectedMidiDevice):
                promptMsg = os.linesep+"Please select the MIDI bridge from input device IDs [%i:%i]:";
                # Get input device indices
                IDs =  [dI["device_id"] if dI["is_input"]==1 else np.nan for dI in devInfo];
                promptMsg = promptMsg % (np.nanmin(IDs),np.nanmax(IDs));
                noValidInput = True;
                # % Input validation until valid input is given
                while noValidInput:
                    input_deviceID = (input(promptMsg));
                    if input_deviceID.isnumeric() and  (int(input_deviceID) in IDs):
                        # Get the device input 
                        input_deviceID = int(input_deviceID);
                        # Match the input to the list of devices
                        for dev in devInfo:
                            if (input_deviceID == dev["device_id"]) and dev["is_input"]:
                                noValidInput = False;
                                break;
                            # end
                        # end
                        if noValidInput:
                            B.log("The input was not found in the list of devices!");
                            raise Exception("")
                        # end
                    else:
                        B.log('The numeric input is not valid! Please try again!');
                    # end
                # end

                # % After Validation
                B.midi_BridgeName = dev["name"];
            # end
            
            # % Load the selected device as an input to the Bridge.
            # % DAW(out)->(in)Bridge
            B.midiDevice = dev;#%'Output',midideviceName) 
            # Log and display the selected device
            B.log(os.linesep+"The currect selected device connection: ["+B.midi_BridgeName +"]"+
                  " ID:["+str(dev["device_id"])+"]"+os.linesep);
        # end
    
        # # % Get function to get the server URL
        def get_serverURL(B):
            serverURL = "";
            if not(B.Server_IP == ""):
                serverURL = B.Server_Protocol+"://"+B.Server_IP+":"+str(B.Server_ControlPort);
            # end
            return serverURL;
        # end

        # % Function to establish the connection to the server
        def establishServerConnection(B):
            configAvailable_server=True;
            configAvailable_autodiscover=True;
            serverFound=False;
            # % Maximum of connection retyr attempts
            connectionRetryLimit = 10000;
            for retry in range(connectionRetryLimit):
                if ~(B.get_serverURL=="") and configAvailable_server:
                    # % Connect to the preconfigured IP
                    testResult = B.testConnection();
                    serverFound = testResult[0];
                else:
                    B.log("Server Configuration in ["+B.configuration_filepath+"] not found!");
                    configAvailable_server= False;
                # end
            
                # % If the configured IP is not working try the autodiscover
                # % option
                if not(serverFound): 
                    if not(B.Server_autodiscover=="") and configAvailable_autodiscover:
                        # % Connect to the preconfigured IP
                        try:
                            B.log("Attempt autodiscover at ["+B.Server_autodiscover+"] ... ")
                            # If the preemble is missing add the protocol to the auto discover
                            if B.Server_autodiscover.find(B.Server_Protocol) < 0:
                                B.Server_autodiscover=B.Server_Protocol+"://"+B.Server_autodiscover;
                            # end
                            response = requests.get(B.Server_autodiscover);
                            # % Convert the response data to formated strings.
                            URIs = response.text.splitlines();
                            # % Get the correct control IP
                            URI = list(filter(lambda x: (":"+str(B.Server_ControlPort)) in x, URIs))[0];
                            B.log("Autodiscover found at ["+B.Server_autodiscover+"] is ["+URI+"]");
                            # % Split the URI
                            uriParts = URI.replace("://",":").split(':',3);
                            B.Server_Protocol = uriParts[0];
                            B.Server_IP = uriParts[1];
                            B.Server_ControlPort = int(uriParts[2]);
            
                        except:
                            B.log("Autodiscover at ["+B.Server_autodiscover+"] failed!");
                        # end
                    else:
                        B.log("Server autodiscover Configuration in ["+B.configuration_filepath+"] not found!");
                        configAvailable_autodiscover = False;
                    # end
                # end
            
                # % If configuration data is not available for both
                if serverFound:
                    B.STATE_FLAG="connected";
                    break;
                elif not(configAvailable_server) and not(configAvailable_autodiscover):
                    B.STATE_FLAG="exit";
                    break;
                else:
                    B.STATE_FLAG="connection_retry";
                    if retry < connectionRetryLimit-1:
                        B.log(os.linesep+"Retry connection ...");
                        time.sleep(1);
                    else:
                        B.log(os.linesep+"Connection retry limit reached ... exiting!");
                    # end
                # end           
            
            # end
            # % Just a new line for clarity
            B.log(" ");
        # end


        # % Connection test function
        def testConnection(B):
            connectionOK = False;
            response = [];
            URL = B.get_serverURL();
            try:
                B.log("Connecting to ["+URL+"] ... ");
                # Send a test request to the server
                response = requests.get(URL);
                B.log("Server found at ["+URL+"]");
                connectionOK = True;
            except:
                B.log("Connection to ["+URL+"] failed!");
            # end
            return [connectionOK , response];
        # end

        def handleLogin_(B):
            from handleLogin import handleLogin; 
            handleLogin(B); 
        # end

        # Import Triggers
        def importMidiTriggers(B):
            import csv;
            import pandas as pd;

            # Import the MIDI triggers as CSV table
            data = pd.read_csv(B.midi_HttpProtocolPreset,delimiter=",");
            
            # % Specify column names and types
            data.columns = ["HTTP_URL", "ServerAPI", "MidiMapping", "Description", "GroupType", "ActionTypeArguments", "MidimsgType", "MidiChanel", "MidiNote_CC", "ExternalExecutable", "ExternalCmd"];
            # opts.VariableTypes = ["string", "string", "categorical", "string", "categorical", "categorical", "string", "double", "double", "string", "string"];

            # % Specify file level properties
            # opts.ExtraColumnsRule = "ignore";
            # opts.EmptyLineRule = "read";

            # Pass the data
            B.MAP = data;
        # end

        # % Processing the tirggers and prepareing them for 
        def processTriggerMap(B):
            # % Only process the enabled mappings
            B.MAP = B.MAP.loc[B.MAP.MidiMapping == "enabled"];
            
            # % Make the HTTP Calls
            B.MAP.HTTP_URL = B.get_serverURL()+B.MAP.HTTP_URL;

            # Reset table indices
            B.MAP = B.MAP.reset_index();

            NoteAlph = [];
            # % Process the table entries
            for index,r in B.MAP.iterrows():
                # % Get the MIDI notes Alphabetical form
                if "Note".lower() in r.MidimsgType.lower():
                    NoteAlph.append(B.val2note(r.MidiNote_CC));
                else:
                    NoteAlph.append("");
                # end
            # # end
            # # % Put the alphabetical note from in the trigger table
            B.MAP['NoteAlph'] = NoteAlph;
        # end
    # end


    # % Main loop methods
    # methods
        
        # % Run main loop
        def runLoop(B):
            # Midi library imports 
            import pygame as pg;
            import pygame.midi;
            
            # Pygame and MIDI library initialization
            pg.init();
            pg.fastevent.init();
            pygame.midi.init();
            # Event aliases
            event_get = pg.fastevent.get;
            event_post = pg.fastevent.post;

            # Setup midi input handle  
            i_ = pygame.midi.Input(B.midiDevice['device_id']);

            # Mode setup display mode in pixels
            pg.display.set_mode((1, 1));

            # % Compute the time delay to maintain the loop
            tDelayInSeconds = 1./B.inLoopFPS;
            B.STATE_FLAG = 'running';# % Running state update

            uMidiChannels = list(pd.unique(B.MAP.MidiChanel));
            # uMidiTypes    = ["NoteOn","ControlChange"];
            uMidiTypes    = list(pd.unique(B.MAP.MidimsgType));
            Warning("... Other types need to be included but for now this is sufficient");

            def tic():
                # The function will return the start timer mark
                return time.time();

            def toc(startTime):
                # The function will return elapced time
                return time.time() - startTime;

            if B.diagnosticMode:
                # % Timers and counters
                totalTime = tic();#% Total time
                loopCount = 0;#% Total counter
                lastTime  = tic();#% Last time
                lastCount = 0;#% Last count

            # end
            
            # % Run the main control loop
            while True:
                cycleTime  = tic();#% Loop timing

                # Get events
                events = event_get();
                for e_ in events:
                    if e_.type in [pg.QUIT] or e_.type in [pg.KEYDOWN]:
                        B.STATE_FLAG = "stop";
                    if e_.type in [pygame.midi.MIDIIN]:
                        B.log(e_.__str__());
                
                # % Check if any new messages have been recieved
                if i_.poll():
                    # % Get the midi messages
                    midi_events = i_.read(10);
                    
                    # convert them into pygame events.
                    # midi_evs = pygame.midi.midis2events(midi_events, i_.device_id);                    
                    # for m_e in midi_evs:
                        # event_post(m_e);
                    # end

                    # % Loop over all messages that have been recieved
                    for single_midi_event in midi_events:

                        midiS = B.convertPygameEventToMIDIstruct(single_midi_event);
                        # % Ignore all messages that don't match the midi channel and the
                        # % midi message types in the cue trigger mapping database file
                        if (midiS.Channel in uMidiChannels) and (midiS.Type in uMidiTypes):
                            # % Call the callback function
                            B.handleMidiCallback(midiS);
                        # end
                    # end
                # end


                # % Time delay to maintain the refresh rate 
                currentDelay = (tDelayInSeconds - toc(cycleTime))*0.925;
                if currentDelay > 0:
                    # % Dealy
                    time.sleep(currentDelay);
                # end
                
                if B.diagnosticMode:
                    loopCount = loopCount+1;# % Increment the count the total count
                    lastCount = lastCount+1;# % Increment the count the last count                
                    # % Disagnostic for tuneing (not needed in deployment)
                    if not(mod(loopCount,B.inLoopFPS)):
                        diagnosticMsg = "FPS:%i | C:%i = Clast:%i | T:%f = T:%f | Rtot:%f = Rlast:%f"; 
                        diagnosticData = [B.inLoopFPS,loopCount,lastCount,toc(totalTime),toc(lastTime),loopCount/toc(totalTime),lastCount/toc(lastTime)];
                        B.log( diagnosticMsg % tuple(diagnosticData) );
                        lastTime  = tic();#% Last time reset
                        lastCount = 0;#% Last count reset
                    # end
                # end

                # Exit flag
                if not(B.STATE_FLAG=="running"):
                    break;
                # end

            # end

            # Free the input handle
            del i_;
            # close the midi module connection
            pygame.midi.quit();

        # end

        class convertPygameEventToMIDIstruct:
            # Proeprties
            Channel = 16;# Default midi channel
            Type    = "NoteOn";# Default midi type
            Note_CC = 0;# Default midi Note_CC
            Velocity= 0;# Default midi velocity
            Time    = 0;# Default midi message time
            # Constructor
            def __init__(midi_struct,midi_event):
                # Interface function toconvert between midi events from pygame and useable midi structures
                midi_struct.Note_CC  = midi_event[0][1];
                midi_struct.Velocity = midi_event[0][2];
                midi_struct.Time     = midi_event[1];
                # If the trigger has 0 velocity it is effectively "NoteOff" type 
                if midi_struct.Type =="NoteOn" and midi_struct.Velocity == 0:
                    midi_struct.Type="NoteOff";
                # end
            # end
        # end

        def handleMidiCallback(B,midi):
            # This function handles the callback 

            # % Filter the trigger table
            try:
                rowIndex = list(B.MAP.MidiChanel == midi.Channel) and list(B.MAP.MidiNote_CC == midi.Note_CC);
            except:
                "wait";
            # end

            if any(rowIndex) and sum(rowIndex)==1:
                # % Get the correct trigger
                trigger = B.MAP[rowIndex]; 

                # % "void action()" is the default command type                
                # % Support for "void action(int velocity)"
                if trigger.ActionTypeArguments.tolist() == "void action(int velocity)":
                    trigger.HTTP_URL=trigger.HTTP_URL+""+str(midi.Velocity-1);
                # end

                try:
                    # Send the HTTP command
                    response = requests.get(trigger.HTTP_URL.to_list()[0]);
                    net_http_StatusCode_TemporaryRedirect = 307;
                    if response.status_code == net_http_StatusCode_TemporaryRedirect:
                        B.handleLogin_();
                    # end
                except: 
                    B.testConnection();
                # end

                # % Match the midi note            
                B.log("MIDI event:"+B.getKeyValuePropertyPairs(midi).__repr__());
                B.log("HTTP call:"+trigger.values.__repr__().replace("\n","").replace("        "," ")+os.linesep);
            else:
                if sum(rowIndex) > 1:
                    B.log("[error]:Multiple MIDI triggers matching as shown in the table:");
                    B.log(B.MAP[rowIndex]);
                    errorMsg = "[error]:Multiple MIDI triggers matching!";
                    B.log(errorMsg); 
                    raise Exception();
                # end
                if sum(rowIndex) < 1:
                     B.log("No MIDI triggers matching the trigger map");
                # end
            # end
        # end

        def getKeyValuePropertyPairs(B,object):
            # Get Key value propery pairs
            return {key:value for key, value in object.__dict__.items() if not key.startswith('__') and not callable(key)}
            
        # end
    # end
    
    
    # % MIDI Properties
    # properties
        notesInOctave = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"];
    # end

    # % Extra MIDI methods
    # methods
        # def note2val(B,note):
        #     val = [];
        #     warning('finish this function');
        #     return val;
        # # end

        def val2note(B,val):
            if not(val.is_integer()):
                B.log('The MIDI note input value is not numeric!');
                raise Exception();
            # end

            if 0 <= val and val <= 127:
                noteStr = B.notesInOctave[ int( mod(val,B.notesInOctave.__len__()) + 1 ) ] + \
                            str( floor( val/B.notesInOctave.__len__()) - 1 );
            else: 
                B.log('MIDI notes range is [0:127] the input value is out of bounds!');
                raise Exception();
            # end
            return noteStr;
        # end
    # end
  
# end