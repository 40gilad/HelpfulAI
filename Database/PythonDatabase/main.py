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
        query_conditions=[]
        query_params=[]
        for key,val in params.items():
            if val is not None:
                query_conditions.append(key)
                query_params.append(val)
        if query_conditions:
            query += " WHERE " + " AND ".join(query_conditions)
        return [query,query_params]

    # endregion

    # region FUNCTIONS: load_environment, connect_to_db
    def load_environment(self):
        try:
            load_dotenv(dotenv_path='DBhelpful.env')
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

    #region __init__ , close_connection Functions

    def __init__(self):
        """
        Connect to database according to .env file variables.

        Saves database connection as a class variable.

        """
        self.db = self.connect_to_db(*self.load_environment())
        if self.db == None:
            self.perror("Error connecting to Helpful database")
        else:
            self.cursor = self.db.cursor()
            self.psuccess("Helpful database is connected!")

    def close_connection(self):
        try:
            self.cursor.close()
            self.db.close()
            return True
        except Exception as err:
            self.perror(err)
            return False

    #endregion

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

    # endregion

    #region Read

    def execute_selection(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.psuccess("Selection succeed")
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            self.perror(err)
            return None

    def select_person_with(self, id=None, name=None):
        """
        Select person with specific person_id OR/AND with specific name

        With no params, returns all rows from person table
        :param id: String
        :param name: String
        :return: [tuples]
        """
        query = "SELECT * FROM person"
        conditions = {"person_name= %s": name, "person_id= %s": id}
        query, params = self.format_select_query(query, conditions)
        res = self.execute_selection(query, params)
        if res is None:
            self.perror("Failed to select person from DB")
            return None
        return res

    #endregion

if __name__ == "__main__":
    DBhelpful = Database()

    DBhelpful.insert_customer("1234","Dovi","Dovrat@Dogmail.com","4321","Waf waf")
    for x in DBhelpful.select_person_with():
        print (x)



    if(DBhelpful. close_connection()==False):
        raise Exception ("Database was not close properly. some changes may be gone")

