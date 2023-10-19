import json

class Session:
    def __init__(self, phone_number, stage=0):
        self.Json_session={}
        self.Json_session[phone_number] = phone_number
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
        self.sessions = {}

    def create_session(self, phone_number):
        session = self.get_session(phone_number)
        if session is None:
            session = Session(phone_number)
            self.sessions[phone_number] = session
            print(f'new session: {session}')
        return session

    def get_session(self, phone_number):
        if phone_number in self.sessions:
            return self.sessions[phone_number]
        else:
            return None

    def remove_session(self, phone_number):
        if phone_number in self.sessions:
            del self.sessions[phone_number]

    def save_sessions(self):
        sessions_json = json.dumps(self.sessions)
        with open('sessions.json', 'w') as f:
            f.write(sessions_json)



    #def get_stage(self, session):

if __name__=="__main__":
    print("kaki")
    s=SessionManager()
    a=s.create_session("12345")
    b=s.create_session("54321")
    c=s.inc_stage("12345")
    d=s.get_session("12345")
    e=s.get_session("54321")
    x=1

