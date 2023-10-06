import os
from dotenv import load_dotenv
from twilio.rest import Client

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse, Message
import TwilioSession as ts

app = Flask(__name__)
session = ts.SessionManager()




@app.route("/wa")
def wa_reply():
    resp = MessagingResponse()
    msg_received = request.form.get('Body')
    phone_number = request.headers.get('X-Twilio-Phone-Number')
    # Check if the sender has a session
    curr_session= session.get_session(phone_number)
    if curr_session is None: #new message. sender do not have session yet
    # if phone number exist in DATABASE and premission is ok:
        session.create_session(phone_number)
    else: #phone number validated and during session
        session_stage=curr_session.get_session(phone_number)["stage"]

        if session_stage == 0:
            resp.message(f"Hi! you are on stage 0 of conversation")
            session.inc_stage(phone_number)
        elif session_stage == 1:
            resp.message(f"Stage 1!")
            session.inc_stage(phone_number)



if __name__ == "__main__":
    load_dotenv(dotenv_path='Twilio.env')
    account_sid = os.getenv('SID')
    auth_token = os.getenv('TOKEN')
    phone_number = os.getenv('PHONE_NUMBER')
    client = Client(account_sid, auth_token)
    message = client.messages \
        .create(
        body="Join Earth's mightiest heroes. Like Kevin Bacon.",
        from_='whatsapp: +12052931608',
        to='whatsapp: +972526263862'
    )
    app.run(debug=True)
    """
    print("kaki")
    s=ts.SessionManager()
    s.create_session("12345")
    s.create_session("54321")
    s.inc_stage("12345")
    d=s.get_session("12345")
    e=s.get_session("54321")
    print(d["stage"])
    f=s.get_session("1111")
    x=1
    """


"""
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse, Message
import TwilioSession as ts

app = Flask(__name__)
session = ts.SessionManager()


@app.route("/")
def wa_reply():
    msg_received = request.form.get('Body')
    phone_number = request.headers.get('X-Twilio-Phone-Number')
    # Check if the sender has a session

    if not session.get_session(phone_number):
        session.create_session(phone_number)

    # Get the sender's session
    session = session['session']

    # Check if the sender's session is valid
    if not session.is_valid():
        # Create a new session for the sender
        session = session['session'] = TwilioSession.Session('+15555555555', '1234567890abcdef')

    # Handle the sender's message

@app.route("/wa", methods=['POST'])
def sms_reply():
    # Fetch the message
    print (request.form)
    msg_recieved = request.form.get('Body')



    resp = MessagingResponse()
    resp.message(f"You said: {msg_recieved}")

    return str(resp)
"""

