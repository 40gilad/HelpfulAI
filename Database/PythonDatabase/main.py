import mysql.connector
import os
from dotenv import load_dotenv
from colorama import Fore, Back, Style

class Database:
    """
    class variables: cursor, db
    """
    #region Support Functions

    def psuccess(self,message):
        print(Fore.LIGHTCYAN_EX + message)
        print(Style.RESET_ALL)

    def perror(self,message):
        print(f"{Fore.RED}Error: {message})
        print(Style.RESET_ALL)

    #endregion

    #region FUNCTIONS: load_environment, connect_to_db
    def load_environment(self):
        load_dotenv(dotenv_path='DBhelpful.env')
        host = os.getenv('HOST')
        user = os.getenv('USER')
        password = os.getenv('PASS')
        dbname = os.getenv('DBNAME')
        return host, user, password, dbname


    def connect_to_db(self,host, user, password, dbname):
        try:
            db = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=dbname
            )
            if db.is_connected():
                self.psuccess(f"Successfully connected to the database: {dbname}.")
                return db
        except mysql.connector.Error as err:
            self.perror(err)
            return None
    #endregion

    def __init__(self):

        self.db=self.connect_to_db(*self.load_environment())
        self.cursor=db.cursor()


    #region Insertions to DB Functions

    def insert_board(self):
        print("insert_board")

    def insert_role(self):
        print("insert_role")

    def insert_person(self,_id,name,email,phone):
        try:
            self.cursor.execute(f"INSERT INTO person(person_id,person_name,email,phone)"
                                f" VALUES ({_id},{name},{email},{phone})")
            self.db.commit()
            return True
        except mysql.connector.Error as err:
            self.perror(f"insert person {err}")

    def insert_employee(self,_id,name,email,phone):
        self.insert_person(_id,name,email,phone)

    def insert_customer(self):
        self.insert_person()


    #endregion

if __name__ == "__main__":
    host, user, password, dbname = load_environment()
    db = connect_to_db(host, user, password, dbname)

    initialize()

    if db and db.is_connected():
        try:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM person;")
            result = cursor.fetchone()
            print(result)
        except mysql.connector.Error as err:
            print(f"SQL Error: {err}")
        finally:
            cursor.close()
            db.close()
            print("Database connection closed.")
    else:
        print("Could not establish database connection.")
