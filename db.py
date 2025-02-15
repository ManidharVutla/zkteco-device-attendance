from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Text, ForeignKey, select
from datetime import datetime
from collections import deque

# Database configuration
DATABASE_URL = "sqlite:///attendance.db"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, echo=False)
metadata = MetaData()

# Define tables
user_data = Table(
    "user_data", metadata,
    Column("user_id", Integer, primary_key=True),
    Column("user_name", String, nullable=False)
)

attendance_logs = Table(
    "attendance_logs", metadata,
    Column("log_id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("check_in_time", Text, nullable=True),
    Column("check_out_time", Text, nullable=True),
    Column("date", String, nullable=False)
)

intermediate_log_store = Table(
    "intermediate_log_store", metadata,
    Column("log_id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("log", String, nullable=False)
)

class DB:
    
    def __init__(self) -> None:
        metadata.drop_all(engine, tables=[intermediate_log_store, attendance_logs, user_data])
        metadata.create_all(engine)
        print("Database initialized.")
    
    # Check if a user exists in the user_data table
    def check_user_in_database(self, user_id):
        with engine.connect() as conn:
            query = select(user_data.c.user_id).where(user_data.c.user_id == user_id)
            result = conn.execute(query).fetchone()
            return result is not None

    # Add a new user to the user_data table
    def add_user_to_database(self, user_id, user_name):
        with engine.connect() as conn:
            if not self.check_user_in_database(user_id):
                query = user_data.insert().values(user_id=user_id, user_name=user_name)
                conn.execute(query)
                conn.commit()
                print(f"User {user_name} with ID {user_id} added to database.")

    # Add a log entry to the attendance_logs table
    def add_log_entry(self, user_id, date, check_in_time=None, check_out_time=None):
        with engine.connect() as conn:
            # Check if an entry already exists for the user on the same date
            query = select(attendance_logs).where(
                attendance_logs.c.user_id == user_id,
                attendance_logs.c.date == date
            )
            existing_entry = conn.execute(query).mappings().fetchone()

            if existing_entry:
                # Update check-out time if not set
                if not existing_entry["check_out_time"] and check_out_time:
                    update_query = attendance_logs.update().where(
                        attendance_logs.c.log_id == existing_entry["log_id"]
                    ).values(check_out_time=check_out_time)
                    conn.execute(update_query)
                    conn.commit()
                    print(f"Updated check-out time for user ID {user_id} on {date}.")
            else:
                # Insert new log entry
                insert_query = attendance_logs.insert().values(
                    user_id=user_id,
                    check_in_time=check_in_time,
                    check_out_time=check_out_time,
                    date=date
                )
                conn.execute(insert_query)
                conn.commit()
                print(f"New log entry added for user ID {user_id} on {date}.")


    def add_temp_entry(self, user_id, log):
        with engine.connect() as conn:
            query = intermediate_log_store.select().where(
                (intermediate_log_store.c.user_id == user_id) &
                (intermediate_log_store.c.log == log)
            )
            existing_entry = conn.execute(query).fetchone()
            
            if existing_entry:
                pass
            else:
                insert_query = intermediate_log_store.insert().values(
                    user_id=user_id,
                    log=log
                )
                conn.execute(insert_query)
                conn.commit()
                print(f"New user found and entry added in intermediate log store for user ID {user_id}.")
            
    
    def get_intermediate_table_entry(self, user_id=None) -> list:
        """
        This method returns an entry from the intermediate log store.
        If user_id is provided, it fetches the entry for that user.
        Otherwise, it returns the first available entry.

        Args:
            user_id (int, optional): The user ID to filter the entry. Defaults to None.

        Returns:
            - A list of Row objects or None if no entries exists
        """
        with engine.connect() as conn:
            if user_id is not None:
                select_query = intermediate_log_store.select().where(intermediate_log_store.c.user_id == user_id)  
            else:
                select_query = intermediate_log_store.select() 
            results = conn.execute(select_query).fetchall()
            return results if results else list()
            
    
    def delete_entries_from_intermediate_store(self, user_id):
        """
        This method deletes the intermediate attendance logs of user
        using the user id

        Args:
            user_id (_type_): _description_
        """
        
        with engine.connect() as conn:
            delete_query = intermediate_log_store.delete().where(intermediate_log_store.c.user_id == user_id)
            result = conn.execute(delete_query)
            conn.commit()  # 🔹 Commit the transaction
        