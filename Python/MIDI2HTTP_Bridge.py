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
import sys , os ;
import time;

# Custom functions imports
# from ExtraFunctions import *;
from ExtraFunctions import uigetfile,getTimeNow,importConfigurationSettings,formattedDisplayText;


# ==============================================================
# The extra functions file imports from .ExtraFunctions import *;
# ==============================================================

from tkinter.tix import FileSelectBox



# ==============================================================


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
        diagnosticMode=0;

        serverURL="";
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
                    B.log("Assign Property: ["+key+"] = ["+B.__getattribute__(key)+"]")
             
            #         # % If the property value is alphabetic i.e. char array
            #         # % convert that to string
            #         if isinstance(B.(fn),__char):
            #             B.(fn) = string(B.(fn));
            #         # end

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
            info = ""#Remove this
            # info = mididevinfo;# % Get midi device info
            # B.log(evalc('mididevinfo'));# %display the available midi devices
            return info;
        # end
        
        # % Select the MIDI device connection
        def selectMidiDeviceInput(B):
            # % Get midi device info
            devInfo = B.getMidiDeviceInfo();
            # % Convert the input midi devices info to table
            # inDevInfo = struct2table(devInfo.input);

            # % Check if the imported midi name can be found otherwise load
            # % the one from the list
            # if not(contains(B.midi_BridgeName,inDevInfo.Name)):
            #     promptMsg = "\nPlease select the MIDI bridge from input device IDs [%i:%i]:";
            #     promptMsg = sprintf(promptMsg,min(inDevInfo.ID),max(inDevInfo.ID));
            #     noValidInput = True;
            #     # % Input validation until valid input is given
            #     while noValidInput:
            #         deviceID = input(promptMsg,"s");
            #         if isempty(str2double(deviceID)):
            #             fprintf('The numeric input is not valid! Please try again!\n');
            #         else 
            #             deviceID = str2double(deviceID);
            #             noValidInput = false;
            #         # end
            #     # end

            #     # % After Validation
            #     B.midi_BridgeName = devInfo.input(deviceID).Name;
            # # end
            
            # # % Load the selected device as an input to the Bridge.
            # # % DAW(out)->(in)Bridge
            # B.midiDevice = mididevice('Input',B.midi_BridgeName);%'Output',midideviceName) 

        # end
    
        # # % Get function to get the server URL
        # def get.serverURL(B):
        #     serverURL = "";
        #     if ~isempty(B.Server_IP.char):
        #         serverURL = B.Server_Protocol+"://"+B.Server_IP+":"+B.Server_ControlPort;
        #     # end
        #     return serverURL;
        # # end
    
        # % Processing the tirggers and prepareing them for 
        def processTriggerMap(B):
            # % Only process the enabled mappings
            # B.MAP = B.MAP(B.MAP.MidiMapping=='enabled',:);
            # # % Process the table entries
            # for r in range(1,numel(B.MAP.HTTP_URL)):
            #     # % Make the HTTP Calls
            #     B.MAP.HTTP_URL[r] = B.serverURL+B.MAP.HTTP_URL[r];
            #     # % Get the MIDI notes Alphabetical form
            #     if contains(B.MAP.MidimsgType(r),'Note'):
            #         NoteAlph[r] = B.val2note(B.MAP.MidiNote_CC[r]);
            #     else:
            #         NoteAlph[r] = "";
            #     # end
            # # end
            # # % Put the alphabetical note from in the trigger table
            # B.MAP.NoteAlph = NoteAlph';
            True#remove this 
        # end

        # % Function to establish the connection to the server
        def establishServerConnection(B):
            configAvailable_server=True;
            configAvailable_autodiscover=True;
            serverFound=False;
            # % Maximum of connection retyr attempts
            connectionRetryLimit = 10000;
            for retry in range(1,connectionRetryLimit):
                if ~(B.serverURL=="") and configAvailable_server:
                    # % Connect to the preconfigured IP
                    serverFound = B.testConnection();
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
            #                 response = send(matlab.net.http.RequestMessage,B.Server_autodiscover);
            #                 # % Convert the response data to formated strings.
            #                 # URIs = string(char(response.Body.Data')).split(os.linesep);
            #                 # # % Get the correct control IP
            #                 # URI=URIs(URIs.contains(":"+B.Server_ControlPort));
                            URI = "";#Remove this
                            B.log("Autodiscover found at ["+B.Server_autodiscover+"] is ["+URI+"]");
                            # % Split the URI
            #                 uriParts = URI.split({'://',':'});
            #                 B.Server_Protocol = uriParts[1];
            #                 B.Server_IP = uriParts[2];
            #                 B.Server_ControlPort = str2double(uriParts[3]);
            #
                        except:
                            B.log("Autodiscover at ["+B.Server_autodiscover+"] failed!");
                        # end
            #         else:
            #             B.log("Server autodiscover Configuration in ["+B.configuration_filepath+"] not found!");
            #             configAvailable_autodiscover = false;
            #         # end
            #     # end
            #
            #     # % If configuration data is not available for both
            #     if serverFound:
            #         B.STATE_FLAG="connected";
            #         break;
            #     elif not(configAvailable_server) and not(configAvailable_autodiscover):
            #         B.STATE_FLAG="exit";
            #         break;
            #     else:
            #         B.STATE_FLAG="connection_retry";
            #         if retry != connectionRetryLimit:
            #             B.log(os.linesep+"Retry connection ...");
            #             time.sleep(1);
            #         else:
            #             B.log(os.linesep+"Connection retry limit reached ... exiting!");
            #         # end
            #     # end           
            #
            # end
            # % Just a new line for clarity
            B.log(" ");

            # %% Network autodiscover
            # % First check the OS then get the adaptors 
# %             if ispc
# %                 [~, result] = system('ipconfig -all');
# %             elseif isunix
# %             elseif ismac
# %             else
# %                 error('The platform is not suppported for autodiscovery.')
# %             end
# %
# %           -- After that get the subnet mask and the IP in range and start
# %           checking
#         end
    
        # % Connection test function
        def testConnection(B):
            connectionOK = False;
            try:
                B.log("Connecting to ["+B.serverURL+"] ... ");
                # response = send(matlab.net.http.RequestMessage,B.serverURL);
                response ="";#remove this
                B.log("Server found at ["+B.serverURL+"]");
                connectionOK = True;
            except:
                B.log("Connection to ["+B.serverURL+"] failed!");
            # end
            return connectionOK , response;
        # end

        # def handleLogin_(B): handleLogin(B); # end
    # end


    # % Main loop methods
    # methods
        
        # % Run main loop
        def runLoop(B):
            
            tDelayInSeconds = 1./B.inLoopFPS; # % Compute the time delay to maintain the loop
            B.STATE_FLAG = 'running';# % Running state

#             uMidiChannels = unique(B.MAP.MidiChanel);
#             uMidiTypes    = [midimsgtype.NoteOn];%unique(B.MAP.MidimsgType);midimsgtype.ControlChange
#                 warning("... Other types need to be included but for now this is sufficient");

#             if B.diagnosticMode
#                 % Timers and counters
#                 totalTime = tic;% Total time
#                 loopCount = 0;% Total counter
#                 lastTime  = tic;% Last time
#                 lastCount = 0;% Last count
#             end
#             % Run the main control loop
#             while true
#                 cycleTime  = tic;% Loop timing

#                 % Check if any new messages have been recieved
#                 if hasdata(B.midiDevice)
#                     % Get the midi messages
#                     msgs = midireceive(B.midiDevice);
#                     % Loop over all messages that have been recieved
#                     for i = 1:numel(msgs)
#                         % Ignore all messages that don't match the midi channel and the
#                         % midi message types in the cue trigger mapping database file
#                         if any(uMidiChannels == msgs(i).Channel) and any(uMidiTypes==msgs(i).Type)
#                             % Call the callback function
#                             B.handleMidiCallback(msgs(i));
#                         end
#                     end
#                 end

#                 % Time delay to maintain the refresh rate 
#                 currentDelay = (tDelayInSeconds - toc(cycleTime))*0.925;
#                 if currentDelay > 0
#                     % Dealy
#                     pause(currentDelay);
#                 end
                
#                 if B.diagnosticMode
#                     loopCount = loopCount+1; % Increment the count the total count
#                     lastCount = lastCount+1; % Increment the count the last count                
#                     % Disagnostic for tuneing (not needed in deployment)
#                     if ~mod(loopCount,B.inLoopFPS)
#                         B.log( sprintf("FPS:%i | C:%i = Clast:%i | T:%f = T:%f | Rtot:%f = Rlast:%f",...
#                             [B.inLoopFPS,loopCount,lastCount,toc(totalTime),toc(lastTime),loopCount/toc(totalTime),lastCount/toc(lastTime)]) );
#                         lastTime  = tic;% Last time reset
#                         lastCount = 0;% Last count reset
#                     end
#                 end
#             end

#         end

#         function handleMidiCallback(B,midi)
# %             import matlab.net.*
#             import matlab.net.http.*
            
#             % Filter the trigger table
#             try
#             rowIndex = (B.MAP.MidiChanel == midi.Channel) and (B.MAP.MidiNote_CC == midi.Note);
#             catch
#                 "wait";
#             end
#             if any(rowIndex) and sum(rowIndex)==1
#                 % Get the correct trigger
#                 trigger = B.MAP(rowIndex,:);    
                
#                 % "void action()" is the default command type                
#                 % Support for "void action(int velocity)"
#                 if trigger.ActionTypeArguments == "void action(int velocity)"
#                     trigger.HTTP_URL=trigger.HTTP_URL+""+(midi.Velocity-1);
#                 end

#                 try
#                     [response,completedrequest,history] = send(RequestMessage,trigger.HTTP_URL);
#                     if response.StatusCode == matlab.net.http.StatusCode.TemporaryRedirect
#                         B.handleLogin_();
#                     end
#                 catch 
#                     B.testConnection()
#                 end

#                 % Match the midi note               
#                 B.log(midi);
#                 B.log(formattedDisplayText(trigger));
#             else
#                 if sum(rowIndex) > 1
#                     B.log("[error]:Multiple MIDI triggers matching as shown in the table:");
#                     B.log(B.MAP(rowIndex,:));
#                     errorMsg = "[error]:Multiple MIDI triggers matching!";
#                     B.log(errorMsg); 
#                     error(errorMsg);
#                 end
# %                 if sum(rowIndex) < 1
# %                     B.log("No MIDI triggers matching the trigger map");
# %                 end
#             end
#         end

#     end

    
    
    # % MIDI Properties
    # properties
        # notesInOctave = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"];
    # end

#     % Extra MIDI methods
#     methods
#         function [val] = note2val(B,note)
#             warning('finish this function');
#         end

#         function [noteStr] = val2note(B,val)
#             if ~isnumeric(val)
#                 error('The MIDI note input value is not numeric!')
#             end

#             if 0 <= val and val <= 127
#                 noteStr = B.notesInOctave( mod(val,numel(B.notesInOctave)) + 1 ) + ...
#                           num2str( floor( val/numel(B.notesInOctave) ) - 1 );
#             else 
#                 error('MIDI notes range is [0:127] the input value is out of bounds!');
#             end
#         end
#     end
  
# end