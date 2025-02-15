'''
Information:

1. Date headers are used for client time synchronization

2. row, followed by the configuration separated \n\rGET OPTION FROM: {{ serialNumber }}

3. The config alternative row: ATTLOG Attendance record OPERLOG Operation log ATTPHOTO Attendance photo When a client uploads a piece of data, its timestamp is uploaded as a cut-off function. The server should store this. When the tool reboots, the client requests the initialization of the data exchange again. Now the server must return the last stamp from the client so that the next data transmission is only the new one that is sent (not all of them are uploaded from the beginning).{{ logType }}Stamp

4. Configuration: how many seconds the interval retransmits data in case of an error.ErrorDelay

5. Configuration: The time when the client checks and sends back data periodically, in a 24-hour format (hour:minute).TransTimes

6. Configuration: Interval for the client to check and send new data (in minutes). If 0, no data is sentTransInterval

7. Configuration: Identify the data requested from the client. There are two formats,TransFlag

The first format to use bits, for example:

TransFlag = 1111000000

Copy
Which means:

Digit to	Data requested	Value
1	Attendance record	Yes
2	Operation log	Yes
3	Attendance photo	Yes
4	Enrolling a new user	Yes
5	Changing user information	Not
6	Enrolling a new fingerprint	Not
7	Changing a fingerprint	Not
8	Fingesprint image	Not
9	New enrolled face	Not
10	User picture	Not
The second format uses the first string, for example:

TransFlag = TransData AttLog<tab>OpLog<tab>AtPhoto...<dst>..

Copy
Where the requested data is listed with a string separated by a tab:

String	Description of Data Requested
AttLog	Attendance log
OpLog	Operation log
AttPhoto	Attendance photo
EnrollUser	Enrolling a new user
ChgUser	Changing user information
EnrollfP	Enrolling a new fingerprint
ChgFP	Changing a fingerprint
FPImag	Fingerprint image
FACE	New enrolled face
UserPic	Userpicture
Configuration: adjust the client record clock to be precise. Use 7 for WIB, 8 WITA, 9 WIT.Timezone

Configuration : set 2.2.14.ServerVer

Configuration: set 1 if you want to get realtime updates from the machine.Realtime
'''

from flask import request, make_response

class Connect:
    def handshake_intial_response(self): 
        sn = request.args.get('SN')
        # Custom response to mimic ZKTeco server response
        response_body = self.construct_response_body()

        response = make_response(response_body, 200)
        response.headers["Content-Type"] = "text/plain"
        response.headers["Server"] = "nginx/1.6.0"
        response.headers["Pragmar"] = "no-cache"
        response.headers["Cache-Control"] = "no-store"
        return response

    def construct_response_body(self) -> str:
        """
        This method constructs the params from this file doc string to pass to
        the device during handshake intiation. These are honored through out the 
        communication

        Args:
            None

        Returns:
            response_body: str
        """
        # TODO: Change the Realtime=1 to TransTimes=00:00;21:00 to start vm instance at same period.
        response_body = """\
        GET OPTION FROM: {sn}
        ATTLOGStamp=None
        OPERLOGStamp=9999
        ATTPHOTOStamp=None
        ErrorDelay=30
        Delay=10
        TransFlag=TransData AttLog OpLog AttPhoto EnrollUser ChgUser EnrollFP ChgFP UserPic
        Realtime=1
        Encrypt=None
        """
        
        return response_body
        

