import os
from dotenv import load_dotenv
from twilio.rest import Client

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



if __name__ == "__main__":

    app.run(debug=True)



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

if __name__ == "__main__":

    app.run(debug=True)


"""

