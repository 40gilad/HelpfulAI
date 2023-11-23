import os
import sys
sys.path.append(os.path.abspath("C:\\Users\\40gil\\OneDrive\\Desktop\\Helpful"))
from HelpfulAI.Database.PythonDatabase import DBmain as Database
from dotenv import load_dotenv
from twilio.rest import Client
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse, Message
import TwilioSession as ts
admin_session_dict={"SendMenu":0,"GetMenuAnswer":1,"GetEmployeeName":2,"GetEmployeeId":3,"GetEmployeeName":4,
                    "GetEmployeePhone":5,"GetEmployeeRole":6,"GetEmployeeEmail":7}
data_from_msg ={"name":None,"id":None,"phone":None,"role":None,"email":None}
default_num=os.getenv('PHONE_NUMBER')

#region Globals

app = Flask(__name__)
session_manager = ts.SessionManager()
hdb = Database.Database()

#endregion
#region twilio
#region Premission Handlers

def handle_admin(response,recieved,sender_phone_number,session_stage,curr_session):
    session_stage=int(session_stage)
    if recieved == 'Menu' or recieved == 'menu':
        session_manager.inc_stage(sender_phone_number,admin_session_dict["SendMenu"])
    if session_stage==admin_session_dict["SendMenu"]: # need to send menu
        send_menu(1,sender_phone_number)
        session_manager.inc_stage(sender_phone_number)
    elif session_stage ==admin_session_dict["GetMenuAnswer"]: #got menu answer
        if recieved == '1' or session_stage>1 and session_stage<8:
            admin_insert_employee(sender_phone_number,session_stage,recieved)


def handle_team_maneger(response,recieved,sender_phone_number,session_stage):
    print("handle_team_maneger")


def handle_employee(response,recieved,sender_phone_number,session_stage):
    print("handle_employee")


#endregion

#region Admin Actions

def admin_insert_employee(sender_phone_number,session_stage,recieved):
    if session_stage == admin_session_dict["GetMenuAnswer"]:
        send_msg(sender_phone_number,"What is the employees full name?")
        session_manager.inc_stage(sender_phone_number,admin_session_dict["GetEmployeeName"])
    elif session_stage==admin_session_dict["GetEmployeeName"]:
        data_from_msg['name']=recieved
        send_msg(sender_phone_number, "What is the employees ID?")
        session_manager.inc_stage(sender_phone_number, admin_session_dict["GetEmployeeId"])
    elif session_stage==admin_session_dict["GetEmployeeId"]:
        data_from_msg['id']=recieved
        send_msg(sender_phone_number, "What is the employees phone?")
        session_manager.inc_stage(sender_phone_number, admin_session_dict["GetEmployeePhone"])
    elif session_stage==admin_session_dict["GetEmployeePhone"]:
        data_from_msg['phone']=recieved
        send_msg(sender_phone_number, "What is the employees role?")
        session_manager.inc_stage(sender_phone_number, admin_session_dict["GetEmployeeRole"])
    elif session_stage==admin_session_dict["GetEmployeeRole"]:
        data_from_msg['role']=recieved
        send_msg(sender_phone_number, "What is the employees mail?")
        session_manager.inc_stage(sender_phone_number, admin_session_dict["GetEmployeeEmail"])
    elif session_stage==admin_session_dict["GetEmployeeEmail"]:
        data_from_msg['email']=recieved
        send_msg(sender_phone_number, "Collected data OK")
        session_manager.inc_stage(sender_phone_number, admin_session_dict["SendMenu"])
        print(data_from_msg)
        hdb.insert_employee(data_from_msg['id'],data_from_msg['name'],data_from_msg['email']
                                 ,data_from_msg['phone'],role=data_from_msg['role'])
#endregion


def send_msg(_to,_body,_from=default_num):
    message = client.messages.create(
        from_=_from,
        body=_body,
        to=_to
    )

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
    elif premission==2:
        handle_team_maneger(response,recieved,sender_phone_number,session_stage,curr_session)
    elif premission==3:
        handle_employee(response,recieved,sender_phone_number,session_stage,curr_session)


def handle_income_msg(response,recieved,sender_phone_number):
    print(recieved)
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

def create_conversation(twilio_client):

    numbers=['+972526263862','+972528449529']
    for number in numbers:
        new_participant = twilio_client.conversations.conversations(conversation.sid).participants.create({
           'messaging_binding.address': f'whatsapp:{number}',
           'messaging_binding.proxy_address': f'whatsapp:+972543934205'
        })

        message = twilio_client.messages.create({
            'to': f'whatsapp:{number}',
            'from': default_num,
            'body': 'HelpfulAI has invited you to join a group conversation. *Please tap the button below to confirm your participation.*'
        })

    return conversation.sid

#endregion

@app.route("/",methods=["GET", "POST"])
def wa_reply():
    resp = MessagingResponse()
    msg_received = request.form.get('Body')
    sender_phone_number = request.form.get('From')
    handle_income_msg(resp,msg_received,sender_phone_number)
    return str(resp)



if __name__ == "__main__":
    load_dotenv(dotenv_path='Twilio.env')
    account_sid = os.getenv('SID')
    auth_token = os.getenv('TOKEN')
    phone_number = os.getenv('PHONE_NUMBER')
    client = Client(account_sid, auth_token)
    create_conversation(twilio_client=client)
    #client.conversations.Conversations().create()
    app.run(debug=True)



