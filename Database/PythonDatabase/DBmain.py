import mysql.connector
import os
from dotenv import load_dotenv
from colorama import Fore, Style


class Database:
    """
    class variables: cursor, db
    """

    # region Support Functions

    @staticmethod
    def psuccess(message):
        print(f"{Fore.LIGHTCYAN_EX} {message}")
        print(Style.RESET_ALL)

    @staticmethod
    def perror(message):
        print(f"{Fore.RED}Error: {message}")
        print(Style.RESET_ALL)

    def format_select_query(self, query, params={None}):
        query_conditions = []
        query_params = []
        for key, val in params.items():
            if val is not None:
                query_conditions.append(key)
                query_params.append(val)
        if query_conditions:
            query += " WHERE " + " AND ".join(query_conditions)
        return [query, query_params]

    def format_phone(self, phone_number):
        """Formats a phone number to start with `0` if it starts with `+972`.

        Args:
          phone_number: A string representing a phone number.

        Returns:
          A string representing the formatted phone number.
        """

        # Remove any whitespace or hyphens from the phone number.
        phone_number = phone_number.strip().replace('whatsapp:', '').replace('-', '').replace(' ', '')
        # If the phone number starts with `+972`, remove the `+` and prepend a `0`.
        if phone_number.startswith('+972'):
            phone_number = phone_number[4:]
            phone_number = '0' + phone_number

        return phone_number

    # endregion

    # region Init, open and close connection

    def __init__(self, is_qa=None):
        """
        Connect to database according to .env file variables.

        Saves database connection as a class variable.

        is_qa: Variable Which indicates on QA for running the DBmain.py file. None for regular run

        """
        if (not is_qa):
            self.db = self.connect_to_db(*self.load_environment())
        elif (is_qa):
            self.db = self.connect_to_db(*self.load_environment(path="DBhelpful.env"))
        if self.db == None:
            self.perror("Error connecting to Helpful database")
        else:
            self.cursor = self.db.cursor()
            self.psuccess("Helpful database is connected!")

    def load_environment(self, path='..\Database\PythonDatabase\DBhelpful.env'):
        try:
            load_dotenv(dotenv_path=path)
            host = os.getenv('HOST')
            user = os.getenv('USER')
            password = os.getenv('PASS')
            dbname = os.getenv('DBNAME')
        except Exception as err:
            self.perror(err)
        return host, user, password, dbname

    def connect_to_db(self, host, user, password, dbname):
        try:
            db = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=dbname
            )
            if db.is_connected():
                return db
        except mysql.connector.Error as err:
            self.perror(err)
            return None

    def close_connection(self):
        try:
            self.cursor.close()
            self.db.close()
            self.psuccess(f"Connection to DB closed")
            return True
        except Exception as err:
            self.perror(err)
            return False

    # endregion

    # region Insertions to DB Functions

    def execute_insertion(self, command, params=None):
        try:
            self.cursor.execute(command, params)
            self.db.commit()
            self.psuccess("Insertion succeed")
            return True
        except mysql.connector.Error as err:
            self.perror(err)
            return False

    def insert_board(self):
        print("insert_board")

    def insrt_daily_msg(self,msg_id,customer_phone,status=0):
        command="INSERT INTO daily_answers(msg_id,quoted_phone,status) VALUES (%s,%s,%s)"
        params=[msg_id,customer_phone,status]
        self.execute_insertion(command,params)

    def insert_sent_message(self,msg_id,emp_phone):
        command="INSERT INTO sent_messages(msg_id,quoter_phone) VALUES (%s,%s)"
        params=[msg_id,emp_phone]
        self.execute_insertion(command,params)

    def insert_role(self, r_id, r_name):
        print("is insert role needed? ")

    def insert_conversation(self,conv_id,conv_name,customer_phone,emp_phone):
        command = ("INSERT INTO conversations(conv_id,conv_name,customer_id,employee_id) VALUES (%s,%s,%s,%s)")
        params = (conv_id,conv_name,self.get_system_id(customer_phone),self.get_system_id(emp_phone))
        self.execute_insertion(command, params)

    def insert_person(self, _id, name, email, phone):
        command = ("INSERT INTO person(person_id,person_name,email,phone) VALUES (%s,%s,%s,%s)")
        params = (_id, name, email, phone)
        self.execute_insertion(command, params)

    def insert_employee(self, _id, name, email, phone, role="employee"):
        self.insert_person(_id, name, email, phone)
        command = ("INSERT INTO employee(system_id, premission) "
                   "SELECT "
                   "(SELECT system_id FROM person WHERE person_id = %s), "
                   "(SELECT role_id FROM _role WHERE role_name = %s)")
        params = (_id, role)
        self.execute_insertion(command, params)

    def insert_customer(self, _id, name, email, phone, buisness_name):
        self.insert_person(_id, name, email, phone)
        query = ("INSERT INTO customer(system_id, buisness_name) "
                 "SELECT "
                 "(SELECT system_id FROM person WHERE person_id = %s), %s")
        params = (_id, buisness_name)
        self.execute_insertion(query, params)

    def insert_message(self, msg_id, conv_id, quoted_phone, quoter_phone, msg, time_stamp,status=0):
        query = (
            "INSERT INTO messages(msg_id,conv_id,quoted_phone,quoter_phone,content,timestamp,status) VALUES (%s,%s,%s,%s,%s,%s,%s)")
        params = (msg_id, conv_id, quoted_phone, quoter_phone, msg, time_stamp,status)
        self.execute_insertion(query, params)

    def insert_session(self, sys_id, stage=0):
        command = ("INSERT INTO sessions(system_id,stage) VALUES (%s,%s)")
        params = [sys_id, stage]
        self.execute_insertion(command, params)

    # endregion

    # region Read

    def execute_selection(self, command, params=None):
        try:
            self.cursor.execute(command, params)
            self.psuccess("Selection succeed")
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            self.perror(err)
            return None

    def select_with(self, table_name, phone=None, personal_id=None, name=None, system_id=None,
                    status=None, conv_id=None, col='*', quoted_phone=None, quoter_phone=None):
        """
        Select table with contrains

        With no params, returns all rows from selected table
        :param table_name: String
        :param phone: String
        :param personal_id: String
        :param name: String
        :param system_id: String
        :param buisness_name: String
        :return: [tuples]
        """

        query = f"SELECT {col} FROM {table_name}"
        conditions={}
        if name is not None:
            conditions["person_name= %s"]=name
        if phone is not None:
            conditions["phone= %s"]=phone
        if system_id is not None:
            conditions["system_id= %s"]= system_id
        if conv_id is not None:
            conditions["conv_id= %s"]= conv_id
        if quoted_phone is not None:
            conditions["quoted_phone= %s"]= quoted_phone
        if quoter_phone is not None:
           conditions["quoter_phone= %s"]= quoter_phone
        if status is not None:
            conditions["status= %s"]=status

        query, params = self.format_select_query(query, conditions)
        res = self.execute_selection(query, params)
        if res is None:
            self.perror("Failed to select person from DB")
            return None
        return res

    def get_daily(self,customer_number,status=1):
        row=self.execute_selection(f"select d.quoted_phone ,m.content ,d.status from daily_answers d inner join messages m on d.msg_id=m.msg_id where d.quoted_phone=m.quoted_phone and d.status=%s and d.quoted_phone=%s",
                                   params=[status,customer_number])

        if row == None:
            return None
        else:
            return row

    def get_system_id(self, phone_number):
        row = self.select_with("person", phone=phone_number)
        if row == []:
            return None
        else:
            return row[0][0]

    def get_sent_message(self,emp_phone):
        row=self.select_with("sent_messages",quoter_phone=emp_phone)
        if row == []:
            return None
        else:
            return row[0][0]

    def get_employees_from_conv(self, conv_id):
        row = self.select_with("conversations", conv_id=conv_id)
        if row == []:
            return -1
        else:
            return row[0][3:]

    def get_customer_from_conv(self, conv_id):
        row = self.select_with("conversations", conv_id=conv_id)
        if row == []:
            return -1
        else:
            return row[0][2]

    def get_conv_name(self, conv_id):
        row = self.select_with("conversations", conv_id=conv_id)
        if row == []:
            return -1
        else:
            return row[0][1]

    def get_employee_name(self,phone_number=None,system_id=None,full_name=False):
        if system_id is None:
            system_id=self.get_system_id(phone_number)
        row = self.select_with(table_name="person",system_id=system_id)
        if full_name:
            return row[0][2]
        return row[0][2].split(' ')[0]

    def get_premission(self, phone_number):
        return self.get_system_id(self.format_phone(phone_number))

    def get_QnA_dict(self):
        nums = self.execute_selection(
            "    select quoted_phone,quoter_phone from messages where status=0 group by quoter_phone,quoted_phone")
        poll = []
        for t in nums:
            customer, emp = t
            questions = self.select_with("messages", quoter_phone=emp, quoted_phone=customer,status='0', col="msg_id,content")
            poll_record = {"emp": emp, "customer": customer}
            poll_record['questions']=[]
            for q in questions:
                poll_record['questions'].append((q[0],q[1]))
            poll.append(poll_record)
        return poll

    def get_QnA_emps(self):
        return self.execute_selection("select quoter_phone from messages where status=0 group by quoter_phone")

    def get_buisness_name(self,phone_number):
         return self.select_with(table_name="customer",system_id=self.get_system_id(phone_number),col='buisness_name')[0][0]

    # endregion

    # region Update
    def execute_update(self,command,params=None):
        try:
            self.cursor.execute(command, params)
            self.db.commit()
            self.psuccess("Update succeed")
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            self.perror(err)
            return None

    def update_stage(self,system_id,stage):
        command=f"update sessions set stage=%s where system_id=%s"
        params=[stage,system_id]
        self.execute_update(command,params)
    # endregion

    def update_msg_status(self,msg_id,status=1):
        command=f"update messages set status=%s where msg_id=%s"
        params=[status,msg_id]
        self.execute_update(command,params)

    # region Session
    def get_session(self, phone_number=None):
        if phone_number is None:
            ses = self.select_with('sessions')
        else:
            ses = self.select_with('sessions', system_id=self.get_system_id(phone_number))
            if ses==[]:
                return None
            return ses

    def delete_daily(self,customer_number):
        self.execute_update("SET SQL_SAFE_UPDATES = 0")
        command=f"delete from daily_answers where quoted_phone=%s"
        params=[customer_number]
        self.execute_update(command,params)
        self.execute_update("SET SQL_SAFE_UPDATES = 1")

    def delete_sent_message(self,msg_id):
        self.execute_update("SET SQL_SAFE_UPDATES = 0")
        command=f"delete from sent_messages where msg_id=%s"
        params=[msg_id]
        self.execute_update(command,params)
        self.execute_update("SET SQL_SAFE_UPDATES = 1")
    # endregion


if __name__ == "__main__":
    DBhelpful = Database(is_qa=1)
    DBhelpful.get_QnA_emps()
    if (DBhelpful.close_connection() == False):
        raise Exception("Database was not close properly. some changes may be gone")
    kaki=1
