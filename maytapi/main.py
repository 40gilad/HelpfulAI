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

ROBOT_SIGN='🤖'
Tstamp_format = "%d/%m/%Y %H:%M"
private_chat_type = 'c'
group_chat_type = 'g'
hdb = Database.Database()
url = f"{INSTANCE_URL}/{PRODUCT_ID}/{PHONE_ID}"
headers = {"Content-Type": "application/json", "x-maytapi-key": API_TOKEN, }
Qpoll = None


# endregion

# region Support functions

def create_group(name,numbers):
    """
    name=String
    numbers=[]

    """

    if not isinstance(numbers,list):
        raise TypeError("Numbers must be a list of strings")
    body={
        "name": name,
        "numbers": numbers
    }
    try:
        response = requests.post(f'{url}/createGroup', json=body, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        print("Response:", response.json())
        return response.json()['data']['id']
    except requests.exceptions.HTTPError as errh:
        print("HTTP Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Oops! Something went wrong:", err)

def send_msg(body):
    print("Request Body", body, file=sys.stdout, flush=True)

    try:
        response = requests.post(f'{url}/sendMessage', json=body, headers=headers)
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


def format_phone_for_sending(phone_number):
    if phone_number.startswith('0'):
        phone_number = phone_number[1:]
        phone_number = '972' + phone_number
        return phone_number


def format_phone_for_selection(phone_number):
    if phone_number is None:
        return
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
            msg_id=json_data["quoted"]["id"]
            group_id = json_data["conversation"]
            angel_phone = json_data["user"]["phone"]
            customer_phone = json_data["quoted"]["user"]["phone"]
            if is_angel_ack(message["text"], angel_phone, customer_phone, group_id):
                hdb.insert_message(msg_id, group_id,
                                   format_phone_for_selection(customer_phone),
                                   format_phone_for_selection(angel_phone),
                                   json_data["quoted"]["text"], json_data["timestamp"])
                react_robot(group_id=group_id,msg_id=msg_id)



def react_robot(group_id,msg_id):
    body={
        "to_number": group_id,
        "type": "reaction",
        "message": ROBOT_SIGN,
        "reply_to": msg_id
    }
    send_msg(body)
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
    elif hdb.get_session(formatted_phone_number) is None:
        hdb.insert_session(sys_id)
        send_private_txt_msg("you have new session!", raw_phone_number)

    ses_stage = hdb.get_session(formatted_phone_number)[0][1]
    ses_permission = hdb.get_premission(formatted_phone_number)
    run_conversation(ses_stage, ses_permission, raw_phone_number, json_data['message']['text'], sys_id)


def run_conversation(ses_stage, permission, raw_phone_number, income_msg, sys_id):
    # ---------- triggering QnA from admins phone --------------#
    if sys_id == 1 and income_msg.lower() == "qna":
        start_QnA()
        return
    # -----------------------------------------------------------#
    income_msg = income_msg.lower()
    if ses_stage >= 99:
        if income_msg != 'yes' and income_msg != 'no':
            send_private_txt_msg('please answer only yes or no')
            return
        elif ses_stage == 100:
            if income_msg == 'yes':
                status = 1
            elif income_msg == 'no':
                status = 0
            pop_question(raw_phone_number, ses_stage, status)
        else:
            if ses_stage == 99:
                if income_msg == 'yes':
                    hdb.update_stage(system_id=sys_id, stage=ses_stage + 1)
                elif income_msg == 'no':
                    return
        send_next_QnA(raw_phone_number)


def pop_question(emp_phone, ses_stage, status):
    """
    take question outside Qpoll and insert answer to database
    """
    emp_phone = format_phone_for_selection(emp_phone.split('@')[0])
    global Qpoll
    for d in Qpoll:
        if d['emp'] == emp_phone:
            answerd = d['questions'].pop(0)
            insert_answer(answerd[0], status)
            hdb.insrt_daily_msg(answerd[0], format_phone_for_selection(d['customer']), status)
            return


def insert_answer(q_id, status):
    if status == 0:
        return
    elif status == 1:
        hdb.update_msg_status(q_id)


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
    Qpoll = hdb.get_QnA_dict()
    emps_to_ask = hdb.get_QnA_emps()
    for e in emps_to_ask:
        emp_phone = e[0]
        raw_phone = format_phone_for_sending(emp_phone)
        hdb.update_stage(hdb.get_system_id(emp_phone), 99)
        is_ready_for_QnA(format_phone_for_sending(emp_phone))


def is_ready_for_QnA(emp_phone):
    send_private_txt_msg(
        f"*Hi {hdb.get_employee_name(phone_number=format_phone_for_selection(emp_phone))}!*\nare you ready for day summary questions?"
        , emp_phone)


def send_next_QnA(emp_phone):
    formatted_phone = format_phone_for_selection(emp_phone)
    question = get_next_question(emp_phone)
    if question == None:
        return
    send_private_txt_msg(f"{question['BN']} asked you:\n {question['Q']}", emp_phone)


def get_next_question(raw_emp_phone):
    emp_phone = format_phone_for_selection(raw_emp_phone)
    is_emp_in_poll = False
    emp_phone = emp_phone.split('@')[0]
    for d in Qpoll:
        if d['emp'] == emp_phone and d['questions'] != []:
            is_emp_in_poll = True
            return {'Q': d['questions'][0][1], 'BN': hdb.get_buisness_name(format_phone_for_selection(d['customer']))}
        elif d['questions'] == []:
            Qpoll.remove(d)
    if not is_emp_in_poll:
        finish_QnA(raw_emp_phone, format_phone_for_sending(d['customer']))


def finish_QnA(emp_phone, customer_phone):
    send_private_txt_msg("Thank you! that's all for today", emp_phone)
    hdb.update_stage(hdb.get_system_id(format_phone_for_selection(emp_phone)), 4)
    send_daily_report(customer_phone)


def send_daily_report(raw_customer_phone):
    print("starting daily to number " + raw_customer_phone)
    customer_phone = format_phone_for_selection(raw_customer_phone)
    msgs = hdb.get_daily(customer_phone)
    txt = f"*Hi {hdb.get_buisness_name(raw_customer_phone)}!*\n here is what we did for you today:"
    counter = 1
    for m in msgs:
        txt = txt + f"\n{counter}. {m[1]}"
        counter = counter + 1
    send_private_txt_msg(txt, raw_customer_phone)
    hdb.delete_daily(customer_phone)


# endregion

# region Menus

def send_admin_menu(raw_phone_number):
    pass


# endregion

@app.route("/", methods=["POST"])
def webhook():
    json_data = request.get_json()
    json_data['timestamp'] = datetime.now().strftime(Tstamp_format)
    # -------------- for QA ONLY -----------#
    # invented numbers so bot sends messages to error numbers
    if json_data['type'] == 'error':
        return 'error'
    # ---------------------------------------#
    if json_data['conversation']=='972537750144@c.us':
        print("handle text from voice message")
    elif json_data['message']['type']=='ptt':
        body={
      "to_number": "972537750144",
      "type": "forward",
      "message": json_data['message']['id'],
      "forward_caption": True
    }
        send_msg(body)
    elif json_data['type'] != 'ack':
        conv_type = json_data["conversation"].split('@')[1][0]
        if conv_type == group_chat_type:
            handle_group_msg(json_data)
        elif conv_type == private_chat_type:
            handle_income_private_msg(json_data)
    elif json_data['type'] == 'ack':
        print("message was acked")
    else:
        print("Unknow Message", file=sys.stdout, flush=True)
    return jsonify({"success": True}), 200


if __name__ == '__main__':
    app.run()
    """
    #group1:
    group1='group1:E_lior & C_hagit'
    lior_emp='972584105280'
    hagit_cust='972584103477'

    #group2:
    group2='group2:E_meiran & C_adi'
    meiran_emp='972502760600'
    adi_cust='972584105481'

    admin_gilad='972526263862'
    admin_yona='972528449529'
    hdb.insert_employee('11111111','lior tz','lior@QA.com',format_phone_for_selection(lior_emp))
    hdb.insert_employee('2222222','meiran tz','meiran@QA.com',format_phone_for_selection(meiran_emp))
    hdb.insert_customer('3333','hagit cu','hagit@QA.com',format_phone_for_selection(hagit_cust),'Buisness of Hagit')
    hdb.insert_customer('4444','adi cu','adi@QA.com',format_phone_for_selection(adi_cust),'Buisness of Adi')
    hdb.insert_conversation(create_group(group1,[lior_emp,hagit_cust,admin_yona,admin_gilad]),group1,
                            format_phone_for_selection(hagit_cust),format_phone_for_selection(lior_emp))
    hdb.insert_conversation(create_group(group2,[meiran_emp,adi_cust,admin_yona,admin_gilad]),group2,
                            format_phone_for_selection(adi_cust),format_phone_for_selection(meiran_emp))
                            """
