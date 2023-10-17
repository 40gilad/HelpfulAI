import os
import sys
sys.path.append(os.path.abspath("C:\\Users\\40gil\\OneDrive\\Desktop\\Helpful\\HelpfulAI\\Database\\PythonDatabase"))
import DBmain as Database
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
    curr_session = session_manager.get_session(sender_phone_number)
    if curr_session is None:
        curr_session = session_manager.create_session(sender_phone_number)
        send_msg(sender_phone_number,"Session started")


    else: #phone number validated and during session
        session_stage=curr_session.get_stage()
        if session_stage == 0:
            send_msg(sender_phone_number,"Hi! you are on stage 0 of conversation")
            curr_session.inc_stage()
        elif session_stage == 1:
            send_msg(sender_phone_number,"Stage 1!")
            curr_session.inc_stage()


if __name__ == "__main__":
    hdb = Database.Database()
    #kaki=hdb.select_with("employee", personal_id="313416562")
    for x in hdb.select_with("employee"):
        print(x)
    load_dotenv(dotenv_path='Twilio.env')
    account_sid = os.getenv('SID')
    auth_token = os.getenv('TOKEN')
    phone_number = os.getenv('PHONE_NUMBER')
    client = Client(account_sid, auth_token)
    app.run(debug=True)


