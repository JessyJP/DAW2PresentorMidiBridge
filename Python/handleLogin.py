# %
# % Description: Ths functions handles the authantication.
# % Ideally the function will be able to auto-authenticate the process,
# % however at the moment it will rely on the user to manually input the
# % password in the web browser.
# % 
# % Author: JessyJP (2020) % License: GPLv3 @ LICENCE.md
# %

# Library for HTTP requests
import requests;
#  webbrowser module provides a high-level interface to open a web page 
import webbrowser;
# Import the time library
import time;



def handleLogin(B):
    # If the server name is Quelea
    if (B.Server_Name == "Quelea"):  
        # Get a test response
        # response = requests.get(B.get_serverURL()+'/'+'password='+B.Server_password);
        response = B.testConnection()[1];
        # Get the response and check if it is HTML page asking for user inputed password 
        HTML = response.text;
        if "<input name=\"password\">" in HTML:
            # %         RM.Method = matlab.net.http.RequestMethod.POST;
            B.log("Opening ["+B.get_serverURL()+"] in the default web brouwer to request password");        
            webbrowser.open(B.get_serverURL(), new=2)
            while True:
                response = B.testConnection()[1];#%response = send(matlab.net.http.RequestMessage,B.get_serverURL());
                HTML = response.text;              
                if not("<input name=\"password\">" in HTML):
                    B.log("Login authenticated!");
                    break;
                # end
                B.log('Waiting for password...');
                time.sleep(3);
            # end   
        else:
            B.log("Login authenticated!");
        # end
    # end
# end
