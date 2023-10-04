import json

class Session:
    def __init__(self, phone_number, stage=0):
        session_key=self.create_session_key()
        self.phone_number = phone_number
        self.session_key = session_key
        self.stage = stage

    def to_json(self):
        return json.dumps({
            'phone_number': self.phone_number,
            'session_key': self.session_key,
            'stage': self.stage
        })

    def create_session_key(self):
        s="12345"
        return s

    def inc_stage(self):
        self.stage+=1

    @staticmethod
    def from_json(json_string):
        data = json.loads(json_string)
        return Session(data['phone_number'], data['session_key'], data['stage'])

class SessionManager:
    def __init__(self):
        self.sessions = {}

    def create_session(self, phone_number):
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

    def inc_stage(self, phone):
        for p, session in self.sessions.items():
            if p == phone:
                session.inc_stage()


    def get_stage(self, session):
