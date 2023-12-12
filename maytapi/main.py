from flask import Flask, request, jsonify
import requests
import sys
import json
import os
from dotenv import load_dotenv
import DBSessionManeger as dbs
from datetime import datetime

sys.path.append(os.path.abspath("C:\\Users\\40gil\\OneDrive\\Desktop\\Helpful"))
from HelpfulAI.Database.PythonDatabase import DBmain as Database

# region Globals and initializations

app = Flask(__name__)
load_dotenv(dotenv_path='Maytapi.env')
PRODUCT_ID = os.getenv("PRODUCT_ID")
PHONE_ID = os.getenv("PHONE_ID")
API_TOKEN = os.getenv("TOKEN")
TRIAL_GROUP_ID = os.getenv("GROUP_ID")
ANGEL_SIGN = os.getenv("ACK_SIGN").split(',')
ADMIN_SESSION_DICT = json.loads(os.getenv("ADMIN_SESSION_DICT"))
INSTANCE_URL = os.getenv('INSTANCE_URL')

Tstamp_format="%d/%m/%Y %H:%M"
private_chat_type = 'c'
group_chat_type = 'g'
hdb = Database.Database()
sessions = dbs.get_session()
url = f"{INSTANCE_URL}/{PRODUCT_ID}/{PHONE_ID}/sendMessage"
headers = {"Content-Type": "application/json", "x-maytapi-key": API_TOKEN, }
Qpoll = None


# endregion

# region Support functions

def send_msg(body):
    print("Request Body", body, file=sys.stdout, flush=True)

    try:
        response = requests.post(url, json=body, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        print("Response:", response.json())
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Oops! Something went wrong:", err)


def format_phone_for_selection(phone_number):
    # Remove leading '+' if present
    if phone_number.startswith('+'):
        phone_number = phone_number.lstrip('+')

    # Check if the number starts with '972' and remove it
    if phone_number.startswith('972'):
        phone_number = phone_number[3:]

    # Check if the number starts with '0', if not, add '0' at the beginning
    if not phone_number.startswith('0'):
        phone_number = '0' + phone_number

    if phone_number.endswith('@c.us'):
        phone_number = phone_number[:10]

    return phone_number


def is_angel(phone_number, group_id=None):
    if group_id is None:
        return False
    formatted_phone = format_phone_for_selection(phone_number)
    sys_id = hdb.get_system_id(formatted_phone)
    if hdb.get_premission(formatted_phone) >= 1 \
            and sys_id in hdb.get_employees_from_conv(group_id):  # employee in group with premission
        return True
    return False


def is_customer(phone_number, group_id=None):
    if group_id is None:
        return False
    formatted_phone = format_phone_for_selection(phone_number)
    sys_id = hdb.get_system_id(formatted_phone)
    if sys_id == hdb.get_customer_from_conv(group_id):  # customer is in conversation
        return True
    return False


def is_angel_ack(txt, e_phone, c_phone, group_id):
    """
    if msg is ack sign
    AND quoter is angel from the relevant group with premission
    AND quoted is customer of the relevant group

    """
    if txt in ANGEL_SIGN and \
            is_angel(e_phone, group_id) and \
            is_customer(c_phone, group_id):
        return True


# endregion

# region Group chat handlers

def handle_group_msg(json_data):
    wttype = json_data["type"]
    if wttype == "message":
        message = json_data["message"]
        _type = message["type"]
        if message["fromMe"]:
            return
        if _type == "text" and 'quoted' in json_data:
            group_id = json_data["conversation"]
            angel_phone = json_data["user"]["phone"]
            customer_phone = json_data["quoted"]["user"]["phone"]
            if is_angel_ack(message["text"], angel_phone, customer_phone, group_id):
                hdb.insert_message(json_data["quoted"]["id"], group_id, customer_phone, angel_phone,
                                   json_data["quoted"]["text"],json_data["timestamp"])


# endregion

# region Private chat handles

def send_private_txt_msg(msg, to):
    body = {
        "type": "text",
        "message": msg,
        "to_number": to
    }
    send_msg(body)


def handle_income_private_msg(json_data):
    raw_phone_number = json_data['user']['id']
    formatted_phone_number = format_phone_for_selection(raw_phone_number)

    sys_id = hdb.get_system_id(formatted_phone_number)
    if sys_id is None:
        send_private_txt_msg("You are not registered in the system! Please contact the system administrator",
                             raw_phone_number)
        return
    elif sys_id not in sessions:
        # has system ID but no session
        dbs.create_new_session(sys_id)
        sessions.append(dbs.get_session(formatted_phone_number))

    ses_stage = hdb.get_session(formatted_phone_number)[0][1]
    ses_permission = hdb.get_premission(formatted_phone_number)
    run_conversation(ses_stage, ses_permission, raw_phone_number, json_data['message']['text'],sys_id)


def run_conversation(ses_stage, permission, raw_phone_number,income_msg,sys_id):

    income_msg=income_msg.lower()
    if ses_stage >= 99:
        if income_msg!='yes' and income_msg != 'no':
            send_private_txt_msg('please answer only yes or no')
            return
        elif ses_stage==100:
            if income_msg=='yes':
                status=1
            elif income_msg=='no':
                status=0
            pop_question(raw_phone_number,ses_stage,status)
        else:
            if ses_stage==99:
                if income_msg == 'yes':
                    hdb.update_stage(system_id=sys_id,stage=ses_stage+1)
                elif income_msg == 'no':
                    return
        send_next_QnA(raw_phone_number,ses_stage,sys_id)


def pop_question(emp_phone,ses_stage,status):
    emp_phone = emp_phone.split('@')[0]
    global Qpoll
    indx=ses_stage-100
    for d in Qpoll:
        if d['emp']==emp_phone:
            answerd = d['questions'].pop(0)
            insert_answer(answerd[0],status)
            return


def insert_answer(q_id,status):
    print(q_id)
    pass

def handle_admin(ses_stage, raw_phone_number):
    if ses_stage == ADMIN_SESSION_DICT['SendMenu']:
        send_admin_menu(raw_phone_number)
    """
    if recieved == 'Menu' or recieved == 'menu':
        session_manager.inc_stage(sender_phone_number,admin_session_dict["SendMenu"])
    if session_stage==admin_session_dict["SendMenu"]: # need to send menu
        send_menu(1,sender_phone_number)
        session_manager.inc_stage(sender_phone_number)
    elif session_stage ==admin_session_dict["GetMenuAnswer"]: #got menu answer
        if recieved == '1' or session_stage>1 and session_stage<8:
            admin_insert_employee(sender_phone_number,session_stage,recieved)
            """


def handle_team_maneger(ses_stage, raw_phone_number):
    pass


def handle_employee(ses_stage, raw_phone_number):
    pass

def start_QnA():
    global Qpoll;
    sent=[]
    Qpoll= hdb.get_QnA_dict()
    for d in Qpoll:
        emp_phone=d['emp']
        if emp_phone not in sent:
            sent.append(emp_phone)
        else:
            continue
        emp_sys_id=hdb.get_system_id(format_phone_for_selection(emp_phone))
        if emp_sys_id==1: #for QA only. need to send messages to valid numbers
            is_ready_for_QnA(emp_phone)
    #send_QnA(emp_phone,stage)


def is_ready_for_QnA(emp_phone):
    send_private_txt_msg(f"*Hi {hdb.get_employee_name(phone_number=format_phone_for_selection(emp_phone))}!*\nare you ready for day summary questions?"
                         ,emp_phone)

def send_next_QnA(emp_phone,stage,sys_id):
    #stage=stage+1
    formatted_phone=format_phone_for_selection(emp_phone)
    #hdb.update_stage(sys_id,stage=stage)
    question=get_next_question(emp_phone,stage)
    send_private_txt_msg(f"{question['BN']} asked you:\n {question['Q']}",emp_phone)

def get_next_question(emp_phone,stage):
    #indx=stage-100
    indx=0
    emp_phone=emp_phone.split('@')[0]
    for d in Qpoll:
        if d['emp']==emp_phone and d['questions'] != []:
            return {'Q':d['questions'][indx][1],'BN':hdb.get_buisness_name(format_phone_for_selection(d['customer']))}
        elif d['questions']==[]:
            del(d)

def finish_QnA(emp_phone):
    pass

# endregion

# region Menus

def send_admin_menu(raw_phone_number):
    pass


# endregion

@app.route("/", methods=["POST"])
def webhook():
    json_data = request.get_json()
    json_data['timestamp'] = datetime.now().strftime(Tstamp_format)
    #-------------- for QA ONLY -----------#
    # invented numbers so bot sends messages to error numbers
    if json_data['type'] == 'error':
        return 'error'
    #---------------------------------------#
    if json_data['type'] != 'ack':
        conv_type = json_data["conversation"].split('@')[1][0]
        if conv_type == group_chat_type:
            handle_group_msg(json_data)
        elif conv_type == private_chat_type:
            handle_income_private_msg(json_data)
    else:
        print("Unknow Message", file=sys.stdout, flush=True)
    return jsonify({"success": True}), 200


if __name__ == '__main__':
    start_QnA()
    app.run()
