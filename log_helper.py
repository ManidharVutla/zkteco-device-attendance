from flask import make_response
from db import DB
from datetime import datetime  
 

class DeviceLog:
    
    def __init__(self, att_db):
        self.att_db = att_db
        
    def handle_log_request(self, request):
        """
        main function of handling log data (i.e)
        uploading to attendance db and generating response

        Args:
            request (_type_): request

        Returns:
            response: response object
        """
        lines_processed = self.process_log_data(request)
        response = self.generate_log_processed_response(lines_processed)
        return response


    def upload_each_row_to_db(self, raw_data) -> int:
        """
        Takes raw data (with rows), splits each row and calls upload method
        in db to update the database with attendance log

        Args:
            request (_type_): _description_
        
        """
        # Parsing rows of attendance data
        rows = raw_data.strip().split("\n") 
        parsed_rows = [row.split() for row in rows]  # Split each row into columns

        # Displaying parsed rows
        for row in parsed_rows:
            self.update_db_with_log(row)
            
        return len(rows)
        
    def process_log_data(self, request) -> int:
        """
        This method process log data from request and pushes 
            ATTLOG (Attendance log)
                - into the attendance table.
            OPERLOG (User Info log)
                - into user data 
                - update attendace table
                - removes entries from intermediate table

        Args:
            request (_type_): request object

        Returns:
            lines_processed (int): number of rows/lines processed.
        """
        # SN is the serial number
        sn = request.args.get('SN', 'Unknown_SN')
        # table is passed as part of the post request
        table = request.args.get('table', 'Unknown_Table')
        
        # Check type of table      
        if table == 'ATTLOG':
            lines_processed = self.upload_each_row_to_db(request.get_data(as_text=True))
        elif table == 'OPERLOG':
            # We are currently not processing any operation log except the user
            # info requests. Parse the user info and add to the user data and send 
            # the intermediate log to attendance logs
            body_data = request.data.decode('utf-8')
            user_data = body_data.strip().split('\t')

            user_id = self.upload_new_user_data(user_data)
            if user_id:
                # Get entries from intermediate storage and join logs into 
                # join the logs into single long string like raw data.
                entries = self.att_db.get_intermediate_table_entry(user_id)
                att_logs = "\n".join(item.log for item in entries)
                self.upload_each_row_to_db(att_logs)
                self.att_db.delete_entries_from_intermediate_store(user_id) 
            
            lines_processed = len(body_data)
            pass
        else:
            print(f"Unknown POST request from device {sn}")

        return lines_processed
        
    def upload_new_user_data(self, user_data):
        """
        This method parses user data to get the user name and user id.
        Pushes these details to the user_db.

        Args:
            user_data (_type_): _description_
            
        Returns:
            user_id if exists, else None
        """
        
        if len(user_data):
            # Get user name and id from the log
            user_name = next((item.split("=")[1] for item in user_data if item.startswith("Name=")), None)
            user_id = next((item.split("=")[1] for item in user_data if item.startswith("USER PIN=")), None)
            
            # Adding user to user db
            if user_name and user_id:
                self.att_db.add_user_to_database(user_id, user_name)
            return user_id
        return None
            
    
    def update_db_with_log(self, log):
        """
        This method pushes the logs into attendance database after checking
        if user exists on the user data base. Else pushes the log info to intermediate
        table until we get the user info.

        Args:
            log (_type_): _description_
        """
        if len(log) == 8:
            user_id = log[0]
            date = log[1]
            time = log[2]
            is_checkout = int(log[3])
            if not self.att_db.check_user_in_database(user_id):
                # User not found in existing db, hence add him to queue
                print(f"User {user_id} not found. Adding log to intermediate table")
                self.att_db.add_temp_entry(user_id, ' '.join(log))
            elif is_checkout:
                self.att_db.add_log_entry(user_id, date, check_out_time=time)
            else:
                self.att_db.add_log_entry(user_id, date, check_in_time=time)
    
    
    def generate_log_processed_response(self, number_of_processed_lines: int):
        """
        This method generates response for the processed logs mentioning
        number of lines process.
        
        Args:
            number_of_processed_lines (int) : number of lines processed.
            
        Returns: 
            response: response object
        """
        
        current_date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        response_body = f"""
        HITP/1.1 200 OK
        Server:nginx/1.60
        Date: {current_date}
        Content-Type: text/plain
        Content-Length:
        Connection: close
        Pragma: no-cache
        Cache-Control: no-store

        OK: {number_of_processed_lines}
        """
        
        response = make_response(response_body, 200)
        response.headers["Content-Type"] = "text/plain"
        return response