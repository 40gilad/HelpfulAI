import json
import csv

class Session:
    def __init__(self, phone_number, stage=0):
        self.Json_session={}
        self.Json_session['phone_number'] = phone_number
        self.Json_session["stage"] = stage

    def to_json(self):
        return json.dumps({
            'phone_number': self.phone_number,
            'stage': self.stage
        })


    def inc_stage(self,stage=None):
        if stage is None:
            self.Json_session["stage"]+=1
        else:
            self.Json_session["stage"] = stage


    def get_stage(self):
        return self.Json_session["stage"]

    @staticmethod
    def from_json(json_string):
        data = json.loads(json_string)
        return Session(data['phone_number'], data['session_key'], data['stage'])

class SessionManager:
    def __init__(self):
        self.sessions = []
        self.load_sessions()

    def create_session(self, phone_number):
        session = self.get_session(phone_number)
        if session is None:
            session = Session(phone_number)
            self.sessions.append(session)
            self.save_sessions()
            print(f'new session: {session.Json_session}')
        return session

    def get_session(self, phone_number):
        for sess in self.sessions:
            if sess.Json_session['phone_number'] == phone_number:
                return sess
        else:
            return None


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




if __name__=="__main__":
    print("kaki")
    s=SessionManager()
    a=s.create_session("12345")
    b=s.create_session("54321")
    c=s.inc_stage("12345")
    d=s.get_session("12345")
    e=s.get_session("54321")
    x=1

