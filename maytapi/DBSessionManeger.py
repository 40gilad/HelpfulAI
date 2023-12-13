import json
import sys
import os
sys.path.append(os.path.abspath("C:\\Users\\40gil\\OneDrive\\Desktop\\Helpful"))
from HelpfulAI.Database.PythonDatabase import DBmain as Database

hdb = Database.Database()
sessions=hdb.get_session()

def create_new_session(self, sys_id):
    hdb.insert_session(sys_id)


def get_session(phone_number=None):

    sess = hdb.get_session(phone_number)
    if sess is not None:
        return {key: value for key, value in sess}
    return None

def inc_stage(system_id=None,phone_number=None,stage=None):
    if phone_number is None and system_id is None:
        raise Exception ("Function must receive system_id or phone_number")
    sess=get_session(phone_number)
    if system_id is None:
        system_id=next(iter(sess))
    if stage is None:
        stage=sess[system_id]+1
    hdb.update_stage(system_id,stage)





"""
    def inc_stage(self, phone_number,stage=None):
        session = self.get_session(phone_number)
        if session is not None:
            if stage is None:
                session.inc_stage()
            else:
                session.inc_stage(stage)
            self.save_sessions()


    def save_sessions(self):
        with open('sessions.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            for kaki in self.sessions:
                writer.writerow([kaki.Json_session['phone_number'], kaki.Json_session['stage']])

    def load_sessions(self):
        try:
            with open('sessions.csv', 'r', newline='') as f:
                reader = csv.reader(f)
                for row in reader:
                    phone_number, stage = row
                    session = Session(phone_number, stage)
                    self.sessions.append(session)
        except FileNotFoundError:
            print('Creating new sessions.csv file...')
            with open('sessions.csv', 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['phone_number', 'stage'])

"""


if __name__=="__main__":
    print("kaki")
    kaki=1


