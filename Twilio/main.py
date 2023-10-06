import os
from dotenv import load_dotenv
from twilio.rest import Client

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse, Message
import TwilioSession as ts

app = Flask(__name__)
session_manager = ts.SessionManager()



def send_msg(_to,_body,_from="whatsapp:+14155238886"):
    message = client.messages.create(
        from_=_from,
        body=_body,
        to=_to
    )

@app.route("/",methods=["GET", "POST"])
def wa_reply():
    resp = MessagingResponse()
    msg_received = request.form.get('Body')
    sender_phone_number = request.form.get('From')
    # Check if the sender has a session
    session = session_manager.get_session(sender_phone_number)
    if session is None:
        session = session_manager.create_session(sender_phone_number)
        send_msg(sender_phone_number,"Session started")


    else: #phone number validated and during session
        session_stage=session.session["stage"]
        print(session.session)
        if session_stage == 0:
            send_msg(sender_phone_number,"Hi! you are on stage 0 of conversation")
            session.inc_stage(sender_phone_number)
        elif session_stage == 1:
            send_msg(sender_phone_number,"Stage 1!")
            session.inc_stage(sender_phone_number)


if __name__ == "__main__":

    load_dotenv(dotenv_path='Twilio.env')
    account_sid = os.getenv('SID')
    auth_token = os.getenv('TOKEN')
    phone_number = os.getenv('PHONE_NUMBER')
    client = Client(account_sid, auth_token)
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

