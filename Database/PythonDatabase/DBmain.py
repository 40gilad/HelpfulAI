import mysql.connector
import os
from dotenv import load_dotenv
from colorama import Fore, Back, Style


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

    def format_phone(self,phone_number):
        """Formats a phone number to start with `0` if it starts with `+972`.

        Args:
          phone_number: A string representing a phone number.

        Returns:
          A string representing the formatted phone number.
        """

        # Remove any whitespace or hyphens from the phone number.
        phone_number=phone_number.strip().replace('whatsapp:','').replace('-', '').replace(' ', '')
        # If the phone number starts with `+972`, remove the `+` and prepend a `0`.
        if phone_number.startswith('+972'):
            phone_number = phone_number[4:]
            phone_number = '0' + phone_number

        return phone_number

    # endregion

    # region FUNCTIONS: load_environment, connect_to_db
    def load_environment(self,path='..\Database\PythonDatabase\DBhelpful.env'):
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

    # endregion

    # region __init__ , close_connection Functions

    def __init__(self,is_qa=None):
        """
        Connect to database according to .env file variables.

        Saves database connection as a class variable.

        is_qa: Variable Which indicates on QA for running the DBmain.py file. None for regular run

        """
        if(not is_qa):
            self.db = self.connect_to_db(*self.load_environment())
        elif (is_qa):
            self.db = self.connect_to_db(*self.load_environment(path="DBhelpful.env"))
        if self.db == None:
            self.perror("Error connecting to Helpful database")
        else:
            self.cursor = self.db.cursor()
            self.psuccess("Helpful database is connected!")

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

    def insert_role(self, r_id, r_name):
        print("is insert role needed? ")

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

    def insert_message(self,msg_id,conv_id,quoted_phone,quoter_phone,msg):
        query=("INSERT INTO messages(msg_id,conv_id,quoted_phone,quoter_phone,content) VALUES (%s,%s,%s,%s,%s)")
        params=(msg_id,conv_id,quoted_phone,quoter_phone,msg)
        self.execute_insertion(query,params)
    # endregion

    # region Read

    def execute_selection(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.psuccess("Selection succeed")
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            self.perror(err)
            return None

    def select_with(self, table_name,phone=None, personal_id=None, name=None, system_id=None, buisness_name=None,conv_id=None):

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
        query = f"SELECT * FROM {table_name}"

        if table_name == "person":
            conditions = {"person_name= %s": name, "phone= %s": phone}
        elif table_name == "customer":
            conditions = {"system_id= %s": system_id, "buisness_name=": buisness_name}
        elif table_name == "employee":
            conditions = {"system_id= %s": system_id}
        elif table_name=="conversations":
            conditions = {"conv_id= %s":conv_id}

        query, params = self.format_select_query(query, conditions)
        res = self.execute_selection(query, params)
        if res is None:
            self.perror("Failed to select person from DB")
            return None
        return res

    def get_system_id(self,phone_number):
        row=self.select_with("person",phone=phone_number)
        if row == []:
            return -1
        else:
            return row[0][0]

    def get_employees_from_conv(self,conv_id):
        row=self.select_with("conversations",conv_id=conv_id)
        if row == []:
            return -1
        else:
            return row[0][3:]

    def get_customer_from_conv(self,conv_id):
        row=self.select_with("conversations",conv_id=conv_id)
        if row == []:
            return -1
        else:
            return row[0][2]

    def get_conv_name(self,conv_id):
        row=self.select_with("conversations",conv_id=conv_id)
        if row == []:
            return -1
        else:
            return row[0][1]

    # endregion

    #region Update

    #endregion



    def get_premission(self,phone_number):
        return self.get_system_id(self.format_phone(phone_number))




if __name__ == "__main__":
    DBhelpful = Database(is_qa=1)
    """
    #DBhelpful.insert_employee("313416562","Gilad Meir","40gilad@gmail.com","0526263862",role="admin")
    print(DBhelpful.get_premission("0526263862"))
    for x in DBhelpful.select_with("employee", system_id="14"):
        print(x)
        """
    if (DBhelpful.close_connection() == False):
        raise Exception("Database was not close properly. some changes may be gone")
