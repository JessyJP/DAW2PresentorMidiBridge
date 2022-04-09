%
% Description: Ths functions handles the authantication.
% Ideally the function will be able to auto-authenticate the process,
% however at the moment it will rely on the user to manually input the
% password in the web browser.
% 
% Author: JessyJP (2020) % License: GPLv3 @ LICENCE.md
%
function handleLogin(B)
    if strcmpi(B.Server_Name,"Quelea")  
%         import matlab.net.http.*
%         RM = RequestMessage;
%         [response,completedrequest,history] = RM.send(B.serverURL+'/'+'password='+B.Server_password);
        response = send(matlab.net.http.RequestMessage,B.serverURL);
        HTML = string(char(response.Body.Data'));
        if HTML.contains("<input name=""password"">")
            %         RM.Method = matlab.net.http.RequestMethod.POST;
            B.log("Opening ["+B.serverURL+"] in the default web brouwer to request password");        
            web(B.serverURL);
            while true
                [~,response] = B.testConnection();%response = send(matlab.net.http.RequestMessage,B.serverURL);
                HTML = string(char(response.Body.Data'));                
                if not(HTML.contains("<input name=""password"">"))
                    B.log("Login authenticated!");
                    break;
                end
                B.log('Waiting for password...')
                pause(3);
            end        
        else
            B.log("Login authenticated!");
        end
    end
end
