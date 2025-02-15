from flask import Flask, request, make_response
from db import DB
from connect import Connect
from log_helper import DeviceLog
import random 

app = Flask(__name__)

# Ping endpoint for device
@app.route('/iclock/cdata.aspx', methods=['POST'])
def handle_device_log_request():
   return device_logging.handle_log_request(request)

@app.route('/iclock/getrequest.aspx', methods=["GET"])
def execute_cmd_on_request():
    """
    This method is to execute command by passing it in response to the device.
    For now, this is being used for getting user information if we don't have it
    in our database.

    Returns:
        response: A response object is returned either with user info command or OK
        based on the intermediate log store table entries.
    """
    cmdId = random.randint(1,1000)
    temp_entries = att_db.get_intermediate_table_entry()
    if len(temp_entries):
        temp_row = temp_entries[0]
        # intermediate log store is not empty, let's get the user info
        print("not empty making request")
        response_body = f"C:{cmdId}:DATA QUERY USERINFO PIN={temp_row.user_id}"
    else:
        print("intermediate table is empty, sending OK response")
        response_body = "OK"
    
    response = make_response(response_body, 200)
    return response

@app.route('/iclock/devicecmd.aspx', methods=["POST"])
def handle_device_cmd_output():
    """
    This method receives the requested user info from the device.
    Breaks the log back to the list and inserts into attendance db. 
    
    Keyword arguments:
    Return: "200 OK" response
    """

    raw_data = request.get_data(as_text=True)  # Get body as plain text
    print("User info received:")
    print(raw_data)
    rows = raw_data.strip().split("\n")  # Split by newlines
    parsed_rows = [row.split() for row in rows]
    print(parsed_rows)
    return "OK", 200 
                
@app.route('/iclock/cdata.aspx', methods=['GET'])
def handle_device_intiation():
   return connect.handshake_intial_response()

if __name__ == '__main__':
    att_db = DB()
    device_logging = DeviceLog(att_db)
    connect = Connect()
    app.run(host='0.0.0.0', port=4370, debug=True, ssl_context='adhoc')
    
    
