import os
import sys
sys.path.append(os.path.abspath("C:\\Users\\40gil\\OneDrive\\Desktop\\Helpful\\HelpfulAI\\Database\\PythonDatabase"))
import DBmain as Database
from dotenv import load_dotenv
from twilio.rest import Client
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse, Message
import TwilioSession as ts
admin_session_dict={"SendMenu":0,"GetMenuAnswer":1,"GetEmployeeName":2,"GetEmployeeId":3,"GetEmployeeName":4,
                    "GetEmployeePhone":5,"GetEmployeeRole":6}

#region Globals

app = Flask(__name__)
session_manager = ts.SessionManager()
hdb = Database.Database()

#endregion


def send_msg(_to,_body,_from="whatsapp:+14155238886"):
    message = client.messages.create(
        from_=_from,
        body=_body,
        to=_to
    )

#region premission handlers

def handle_admin(response,recieved,sender_phone_number,session_stage,curr_session):
    if session_stage==admin_session_dict["SendMenu"]: # need to send menu
        send_menu(1,phone_number)
        curr_session.inc_stage()
        #    def insert_employee(self, _id, name, email, phone, role="employee"):
    elif session_stage ==admin_session_dict["GetMenuAnswer"]: #got menu answer
        if recieved == '1':
            send_msg(sender_phone_number,"What is the employees full name?")
            curr_session.inc_stage(admin_session_dict["GetEmployeeName"])
    elif session_stage==admin_session_dict["GetEmployeeName"]:



def handle_team_maneger(response,recieved,sender_phone_number,session_stage):
    print("handle_team_maneger")


def handle_employee(response,recieved,sender_phone_number,session_stage):
    print("handle_employee")


#endregion

def send_menu(premission,phone_number):
    if premission == 1:
        send_msg(phone_number,"Admin menu")
    elif premission == 2:
        send_msg(phone_number,"Team Maneger menu")
    elif premission == 3:
        send_msg(phone_number,"Employee menu")

def run_conversation(response,recieved,sender_phone_number,premission,session_stage,curr_session):
    if premission==1:
        handle_admin(response,recieved,sender_phone_number,session_stage,curr_session)
    if premission==2:
        handle_team_maneger(response,recieved,sender_phone_number,session_stage,curr_session)
    if premission==3:
        handle_employee(response,recieved,sender_phone_number,session_stage,curr_session)


def handle_income_msg(response,recieved,sender_phone_number):
    curr_session = session_manager.get_session(sender_phone_number)
    premission=hdb.get_premission(sender_phone_number)
    if premission == -1:
        send_msg(sender_phone_number, "Sorry, you are not in the system. Please contact the admin")

    else:
        if curr_session is None:
            curr_session = session_manager.create_session(sender_phone_number)
        session_stage = curr_session.get_stage()
        run_conversation(response,recieved,sender_phone_number,premission,session_stage,curr_session)
            #send_msg(sender_phone_number,"Session started")



@app.route("/",methods=["GET", "POST"])
def wa_reply():
    resp = MessagingResponse()
    msg_received = request.form.get('Body')
    sender_phone_number = request.form.get('From')
    handle_income_msg(resp,msg_received,sender_phone_number)



if __name__ == "__main__":
    load_dotenv(dotenv_path='Twilio.env')
    account_sid = os.getenv('SID')
    auth_token = os.getenv('TOKEN')
    phone_number = os.getenv('PHONE_NUMBER')
    client = Client(account_sid, auth_token)
    app.run(debug=True)


