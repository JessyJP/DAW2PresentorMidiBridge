%
% Classname:   MIDI2HTTP_Bridge 
% Description: This is the main class that bridges MIDI to HTTP trigger
% translation for projection software and a DAW. 
% 
% Author: JessyJP (2020) % License: GPLv3 @ LICENCE.md
%
% Summary: This service program was developed to connect Reaper and Quelea but
% should work between any MIDI and HTTP capable software.
% 
% Code summary: 
% The constructor is called and all relevant settings are loaded.
% "daw2server_settingsConfiguration.ini" contains all relevant configuration settings.
% "*_Preset_cues.csv" contains the trigger mapping.
% Both files are pain text and can and should be edited to suit the user purposes.
% Then Connection checks are performed and then the control loop is ran.
%
classdef MIDI2HTTP_Bridge < handle

    % Properties to be imported from file
    properties
        % Get the platform the service is currently runing on
        platform=computer;

        % The preset file
        midi_BridgeName="";
        midi_HttpProtocolPreset;
        
        % The name of the DAW or midi player
        DAW_name="";
        %DAw(Reaper) audio interface sampling rate
        DAW_AudioFreqencyHz;
        %DAw(Reaper) audio interface samples per buffer, i.e. buffer size
        DAW_InterfaceBufferSamples;

        % Server Connection properties
        Server_Name="";
        Server_autodiscover="";
        Server_Protocol="";
        Server_IP="";
        Server_ControlPort;
        Server_password="";
        Server_loggedIN=false;
    end

    properties
        configuration_filepath = "./daw2server_settingsConfiguration.ini";% Default file name
        % MIDI device(bridge name)
        midiDevice;
        % Limiter
        inLoopFPS;
        % State flag for the sate of the program can also be used as a
        % control flag 
        STATE_FLAG;
        diagnosticMode=0;

        serverURL;
        MAP;
    end
   

    % Constructor methods
    methods

        % Constructor
        function [B] = MIDI2HTTP_Bridge()
            B.STATE_FLAG="Initialization";
            % Print welcome message
            B.printWelcome();

            %% Import properties from file
            % Check if file exists otherwise locate it
            if ~isdeployed% Check if it is deployed to adjust the root paths
                B.configuration_filepath = "."+B.configuration_filepath;
            end
            if ~exist(B.configuration_filepath,"file")
                [configFileName,configFilePath] = uigetfile(B.configuration_filepath);
                B.configuration_filepath = fullfile(configFilePath,configFileName);
            end
            % Get the raw file properties
            rawPropertyText = importConfigurationSettings(B.configuration_filepath);
            % Assign the file properties
            B.loadFileProperties(rawPropertyText);
            % Compute the application loop FPS limiter to match the cycle
            % rate of the DAW's audio interface (it will be approximate)
            B.inLoopFPS = B.DAW_AudioFreqencyHz/B.DAW_InterfaceBufferSamples;

            if ~isdeployed% Check if it is deployed to adjust the root paths
                B.midi_HttpProtocolPreset = "."+B.midi_HttpProtocolPreset;
            end
            
            B.STATE_FLAG="Configured";
        end

        % Loggin and output function
        function log(~,msg)
            if ~isstring(msg)
                msg=formattedDisplayText(msg)+newline;
            end

            % To standart output
            fprintf(1,msg+"\n");

            % Display diagnostic messages
%             disp(msg);
        end
        
        % Prints the welcome message
        function [welcome] = printWelcome(B)

            welcome = [
                    "% Classname:   MIDI2HTTP_Bridge "
                    "% Description: This is the main class that bridges MIDI to HTTP trigger"
                    "% translation for projection software and a DAW."
                    "% "
                    "% Author: JessyJP (2020) % License: GPLv3 @ LICENCE.md"
                    ""
                ];
            for r =1:numel(welcome)
                disp(welcome(r));
            end

            B.log("Log started at: "+formattedDisplayText(datetime));
        end

        % Function for loading the imported file properties
        function loadFileProperties(B,propData)
            % The function can check if the file contains comments  
            function [yesItIsComment] = isComment(S)
                yesItIsComment = false;
                % If the first character is not aphabetic character then
                % the line is a comment
                if not( ('a' <= S(1) && S(1) <= 'z') || ('A' <= S(1) && S(1) <= 'Z') )
                    yesItIsComment = true;
                end
            end

            % Loop over all imported property strings
            for r = 1:height(propData)
                % Field name
                fn = propData{r,1}; 
                % If it is comment or empty line skip over it
                if isComment(fn) || isempty(fn)
                    continue; 
                end
                try                    
                    % shorturl.at/oA037  -- about the sublevel assigment
                    B.(fn) = propData{r,2};
                    % If the property value is alphabetic i.e. char array
                    % convert that to string
                    if ischar(B.(fn))
                        B.(fn) = string(B.(fn));
                    end
                catch %(err) Could catch the original message and merge it the one in the catch
                    error(['Not found Property:[',fn,']',...
                           ' Associated data:[',num2str(propData{r,2}),']']);
                end
            end
        end

    end


    % Setup methods
    methods 

        % Get MIDI device info
        function [info] = getMidiDeviceInfo(B)
            info = mididevinfo;% Get midi device info
            B.log(evalc('mididevinfo'));%display the available midi devices
        end
        
        % Select the MIDI device connection
        function selectMidiDeviceInput(B)
            % Get midi device info
            devInfo = B.getMidiDeviceInfo();
            % Convert the input midi devices info to table
            inDevInfo = struct2table(devInfo.input);

            % Check if the imported midi name can be found otherwise load
            % the one from the list
            if ~contains(B.midi_BridgeName,inDevInfo.Name)
                promptMsg = '\nPlease select the MIDI bridge from input device IDs [%i:%i]:';
                promptMsg = sprintf(promptMsg,min(inDevInfo.ID),max(inDevInfo.ID));
                noValidInput = true;
                % Input validation until valid input is given
                while noValidInput
                    deviceID = input(promptMsg,"s");
                    if isempty(str2double(deviceID))
                        fprintf('The numeric input is not valid! Please try again!\n');
                    else 
                        deviceID = str2double(deviceID);
                        noValidInput = false;
                    end
                end

                % After Validation
                B.midi_BridgeName = devInfo.input(deviceID).Name;
            end
            
            % Load the selected device as an input to the Bridge.
            % DAW(out)->(in)Bridge
            B.midiDevice = mididevice('Input',B.midi_BridgeName);%'Output',midideviceName) 

        end
    
        % Get function to get the server URL
        function [serverURL] = get.serverURL(B)
            serverURL = "";
            if ~isempty(B.Server_IP.char)
                serverURL = B.Server_Protocol+"://"+B.Server_IP+":"+B.Server_ControlPort;
            end

        end
    
        % Processing the tirggers and prepareing them for 
        function processTriggerMap(B)
            % Only process the enabled mappings
            B.MAP = B.MAP(B.MAP.MidiMapping=='enabled',:);
            % Process the table entries
            for r = 1:numel(B.MAP.HTTP_URL)
                % Make the HTTP Calls
                B.MAP.HTTP_URL(r) = B.serverURL+B.MAP.HTTP_URL(r);
                % Get the MIDI notes Alphabetical form
                if contains(B.MAP.MidimsgType(r),'Note')
                    NoteAlph(r) = B.val2note(B.MAP.MidiNote_CC(r));
                else
                    NoteAlph(r) = "";
                end
            end
            % Put the alphabetical note from in the trigger table
            B.MAP.NoteAlph = NoteAlph';
        end

        % Function to establish the connection to the server
        function establishServerConnection(B)
            configAvailable.server=true;
            configAvailable.autodiscover=true;
            serverFound=false;
            %Maximum of connection retyr attempts
            connectionRetryLimit = 10000;
            for retry=1:connectionRetryLimit
    
                if ~(B.serverURL=="") && configAvailable.server
                    % Connect to the preconfigured IP
                    [serverFound] = testConnection(B);
                else
                    B.log("Server Configuration in ["+B.configuration_filepath+"] not found!");
                    configAvailable.server= false;
                end
    
                % If the configured IP is not working try the autodiscover
                % option
                if not(serverFound) 
                if ~(B.Server_autodiscover=="") && configAvailable.autodiscover
                    % Connect to the preconfigured IP
                    try
                        B.log("Attempt autodiscover at ["+B.Server_autodiscover+"] ... ")
                        response = send(matlab.net.http.RequestMessage,B.Server_autodiscover);
                        % Convert the response data to formated strings.
                        URIs = string(char(response.Body.Data')).split(newline);
                        % Get the correct control IP
                        URI=URIs(URIs.contains(":"+B.Server_ControlPort));
                        B.log("Autodiscover found at ["+B.Server_autodiscover+"] is ["+URI+"]");
                        % Split the URI
                        uriParts = URI.split({'://',':'});
                        B.Server_Protocol = uriParts(1);
                        B.Server_IP = uriParts(2);
                        B.Server_ControlPort = str2double(uriParts(3));
                        
                    catch
                        B.log("Autodiscover at ["+B.Server_autodiscover+"] failed!");
                    end
                else
                    B.log("Server autodiscover Configuration in ["+B.configuration_filepath+"] not found!");
                    configAvailable.autodiscover = false;
                end
                end
    
                % If configuration data is not available for both
                if serverFound
                    B.STATE_FLAG="connected";
                    break;
                elseif not(configAvailable.server) && not(configAvailable.autodiscover)
                    B.STATE_FLAG="exit";
                    break;
                else
                    B.STATE_FLAG="connection_retry";
                    if retry ~= connectionRetryLimit
                        B.log(newline+"Retry connection ...");
                        pause(1);
                    else
                        B.log(newline+"Connection retry limit reached ... exiting!");
                    end
                end           

            end
            % Just a new line for clarity
            B.log(" ");

            %% Network autodiscover
            % First check the OS then get the adaptors 
%             if ispc
%                 [~, result] = system('ipconfig -all');
%             elseif isunix
%             elseif ismac
%             else
%                 error('The platform is not suppported for autodiscovery.')
%             end
%
%           -- After that get the subnet mask and the IP in range and start
%           checking
        end
    
        % Connection test function
        function [connectionOK,response] = testConnection(B)
            connectionOK = false;
            try
                B.log("Connecting to ["+B.serverURL+"] ... ");
                response = send(matlab.net.http.RequestMessage,B.serverURL);
                B.log("Server found at ["+B.serverURL+"]");
                connectionOK = true;
            catch
                B.log("Connection to ["+B.serverURL+"] failed!");
            end
        end

        function handleLogin_(B); handleLogin(B); end
    end


    % Main loop methods
    methods
        
        % Run main loop
        function runLoop(B)
            
            tDelayInSeconds = 1./B.inLoopFPS;% Compute the time delay to maintain the loop
            B.STATE_FLAG = 'running';% Running state

            uMidiChannels = unique(B.MAP.MidiChanel);
            uMidiTypes    = [midimsgtype.NoteOn];%unique(B.MAP.MidimsgType);midimsgtype.ControlChange
                warning("... Other types need to be included but for now this is sufficient");

            if B.diagnosticMode
                % Timers and counters
                totalTime = tic;% Total time
                loopCount = 0;% Total counter
                lastTime  = tic;% Last time
                lastCount = 0;% Last count
            end
            % Run the main control loop
            while true
                cycleTime  = tic;% Loop timing

                % Check if any new messages have been recieved
                if hasdata(B.midiDevice)
                    % Get the midi messages
                    msgs = midireceive(B.midiDevice);
                    % Loop over all messages that have been recieved
                    for i = 1:numel(msgs)
                        % Ignore all messages that don't match the midi channel and the
                        % midi message types in the cue trigger mapping database file
                        if any(uMidiChannels == msgs(i).Channel) && any(uMidiTypes==msgs(i).Type)
                            % Call the callback function
                            B.handleMidiCallback(msgs(i));
                        end
                    end
                end

                % Time delay to maintain the refresh rate 
                currentDelay = (tDelayInSeconds - toc(cycleTime))*0.925;
                if currentDelay > 0
                    % Dealy
                    pause(currentDelay);
                end
                
                if B.diagnosticMode
                    loopCount = loopCount+1; % Increment the count the total count
                    lastCount = lastCount+1; % Increment the count the last count                
                    % Disagnostic for tuneing (not needed in deployment)
                    if ~mod(loopCount,B.inLoopFPS)
                        B.log( sprintf("FPS:%i | C:%i = Clast:%i | T:%f = T:%f | Rtot:%f = Rlast:%f",...
                            [B.inLoopFPS,loopCount,lastCount,toc(totalTime),toc(lastTime),loopCount/toc(totalTime),lastCount/toc(lastTime)]) );
                        lastTime  = tic;% Last time reset
                        lastCount = 0;% Last count reset
                    end
                end
            end

        end

        function handleMidiCallback(B,midi)
%             import matlab.net.*
            import matlab.net.http.*
            
            % Filter the trigger table
            try
            rowIndex = (B.MAP.MidiChanel == midi.Channel) & (B.MAP.MidiNote_CC == midi.Note);
            catch
                "wait";
            end
            if any(rowIndex) && sum(rowIndex)==1
                % Get the correct trigger
                trigger = B.MAP(rowIndex,:);    
                
                % "void action()" is the default command type                
                % Support for "void action(int velocity)"
                if trigger.ActionTypeArguments == "void action(int velocity)"
                    trigger.HTTP_URL=trigger.HTTP_URL+""+(midi.Velocity-1);
                end

                try
                    [response,completedrequest,history] = send(RequestMessage,trigger.HTTP_URL);
                    if response.StatusCode == matlab.net.http.StatusCode.TemporaryRedirect
                        B.handleLogin_();
                    end
                catch 
                    B.testConnection()
                end

                % Match the midi note               
                B.log(midi);
                B.log(formattedDisplayText(trigger));
            else
                if sum(rowIndex) > 1
                    B.log("[error]:Multiple MIDI triggers matching as shown in the table:");
                    B.log(B.MAP(rowIndex,:));
                    errorMsg = "[error]:Multiple MIDI triggers matching!";
                    B.log(errorMsg); 
                    error(errorMsg);
                end
%                 if sum(rowIndex) < 1
%                     B.log("No MIDI triggers matching the trigger map");
%                 end
            end
        end

    end

    
    
    % MIDI Properties
    properties
        notesInOctave = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"];
    end

    % Extra MIDI methods
    methods
        function [val] = note2val(B,note)
            warning('finish this function');
        end

        function [noteStr] = val2note(B,val)
            if ~isnumeric(val)
                error('The MIDI note input value is not numeric!')
            end

            if 0 <= val && val <= 127
                noteStr = B.notesInOctave( mod(val,numel(B.notesInOctave)) + 1 ) + ...
                          num2str( floor( val/numel(B.notesInOctave) ) - 1 );
            else 
                error('MIDI notes range is [0:127] the input value is out of bounds!');
            end
        end
    end
  
end






