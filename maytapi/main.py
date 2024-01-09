# region Imports

from flask import Flask, request, jsonify
import requests
import sys
import json
import os
from dotenv import load_dotenv
from datetime import datetime
"""
sys.path.append(os.path.abspath("C:\\Users\\40gil\\OneDrive\\Desktop\\Helpful"))
from HelpfulAI.Database.PythonDatabase import DBmain as Database
"""
sys.path.append(os.path.abspath("C:\\Users\\40gil\\Desktop\\HelpfulAI"))
from Database.PythonDatabase import DBmain as Database

# endregion

# region Globals and initializations

app = Flask(__name__)
load_dotenv(dotenv_path='Maytapi.env')
PRODUCT_ID = os.getenv("PRODUCT_ID")
PHONE_ID = os.getenv("PHONE_ID")
API_TOKEN = os.getenv("TOKEN")
TRIAL_GROUP_ID = os.getenv("GROUP_ID")
ANGEL_SIGN = os.getenv("ACK_SIGN").split(',')
SESSION_DICT = json.loads(os.getenv("SESSION_DICT"))
INSTANCE_URL = os.getenv('INSTANCE_URL')
CREATE_GROUP_SUFFIX = 'createGroup'

ROBOT_SIGN = '🤖'
timluli = '972537750144'
Tstamp_format = "%d/%m/%Y %H:%M"
private_chat_type = 'c'
group_chat_type = 'g'
hdb = Database.Database()
url = f"{INSTANCE_URL}/{PRODUCT_ID}/{PHONE_ID}"
headers = {"Content-Type": "application/json", "x-maytapi-key": API_TOKEN, }
last_sent_to_timluli = None
Qpoll = None


# endregion

# region Support functions


# -------------------------------------------------- QNA SUPPORTERS --------------------------------------------------#

def pop_question(emp_phone, status):
    """
    take question outside Qpoll and insert answer to database
    """
    emp_phone = format_phone_for_selection(raw_phone_number=emp_phone.split('@')[0])
    global Qpoll
    for d in Qpoll:
        if d['emp'] == emp_phone:
            answerd_id = hdb.get_sent_message(emp_phone=emp_phone)  # get id of last sent question
            index = 0
            for q in d['questions']:
                if answerd_id == q[0]:
                    answerd = d['questions'].pop(index)
                    insert_answer(msg_id=answerd[0], status=status)
                    hdb.insrt_daily_msg(msg_id=answerd[0], customer_phone=format_phone_for_selection(d['customer']),
                                        status=status)
                    hdb.delete_sent_message(msg_id=answerd_id)  # delete last sent question from DB
                    return
                index += 1


def insert_answer(msg_id, status):
    if status == 0:
        return
    elif status == 1:
        hdb.update_msg_status(msg_id=msg_id)


def get_next_question(raw_emp_phone):
    global Qpoll
    emp_phone = format_phone_for_selection(raw_emp_phone)
    is_emp_in_poll = False
    emp_phone = emp_phone.split('@')[0]
    for d in Qpoll:
        if d['emp'] == emp_phone and d['questions'] != []:
            is_emp_in_poll = True
            return {
                'Q': d['questions'][0][1],
                'BN': hdb.get_buisness_name(phone_number=format_phone_for_selection(d['customer'])),
                'id': d['questions'][0][0]
            }
    if not is_emp_in_poll:
        finish_QnA(emp_phone=raw_emp_phone, customer_phone=format_phone_for_sending(d['customer']))


def finish_QnA(emp_phone, customer_phone):
    send_private_txt_msg(msg="תודה! הנה סיכום היום שלך:", to=[emp_phone])
    # hdb.update_stage(system_id=hdb.get_system_id(phone_number=format_phone_for_selection(emp_phone)),stage=SESSION_DICT['SendMenu'])
    send_daily_report(raw_emp_phone=emp_phone, raw_customer_phone=customer_phone)


# --------------------------------------------------------------------------------------------------------------------#
# ----------------------------------------------------- TIMLULI ------------------------------------------------------#

def timluli_is_locked():
    if last_sent_to_timluli is None:
        return False
    return True


def get_headline_from_timluli(text):
    return text.split('*')[1]


def send_to_timluli(json_data):
    global last_sent_to_timluli
    keys = last_sent_to_timluli_keys = ['msg_id', 'conv_id', 'quoted_phone', 'quoter_phone', 'timestamp']
    while timluli_is_locked():
        continue
    last_sent_to_timluli = dict.fromkeys(keys)
    last_sent_to_timluli.update({
        'msg_id': json_data['id'],
        'conv_id': json_data['conv_id'],
        'quoted_phone': json_data['user']['phone'],
        'quoter_phone': json_data['quoter'],
        'timestamp': json_data['timestamp']
    })
    forward_msg(msg=json_data['id'], to=timluli)


# --------------------------------------------------------------------------------------------------------------------#
# -------------------------------------------------- WA SUPPORTERS ---------------------------------------------------#

def create_group(name, numbers):
    """
    name=String
    numbers=[]

    """

    if not isinstance(numbers, list):
        raise TypeError("Numbers must be a list of strings")
    body = {
        "name": name,
        "numbers": numbers
    }
    execute_post(body=body, url_suffix=CREATE_GROUP_SUFFIX)


def send_msg(body):
    print(f"Request Body {body}")
    execute_post(body=body, url_suffix='sendMessage')


def react_robot(group_id, msg_id):
    body = {
        "to_number": group_id,
        "type": "reaction",
        "message": ROBOT_SIGN,
        "reply_to": msg_id
    }
    send_msg(body)


def forward_msg(msg, to):
    body = {
        "to_number": to,
        "type": "forward",
        "message": msg,
        "forward_caption": True
    }
    send_msg(body=body)


# --------------------------------------------------------------------------------------------------------------------#
# ----------------------------------------------------- GENERALS -----------------------------------------------------#

def execute_post(body, url_suffix):
    try:
        response = requests.post(f'{url}/{url_suffix}', json=body, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        print("Response:", response.json())
        if url_suffix is CREATE_GROUP_SUFFIX:
            return response.json()['data']['id']
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


def format_phone_for_selection(raw_phone_number):
    if raw_phone_number is None:
        return
    phone_number = raw_phone_number
    # Remove leading '+' if present
    if raw_phone_number.startswith('+'):
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


def is_angel(raw_phone_number, group_id=None):
    if group_id is None:
        return False
    formatted_phone = format_phone_for_selection(raw_phone_number)
    sys_id = hdb.get_system_id(phone_number=formatted_phone)
    if hdb.get_premission(phone_number=formatted_phone) >= 1 \
            and sys_id in hdb.get_employees_from_conv(conv_id=group_id):  # employee in group with permission
        return True
    return False


def is_customer(raw_phone_number, group_id=None):
    if group_id is None:
        return False
    formatted_phone = format_phone_for_selection(raw_phone_number=raw_phone_number)
    sys_id = hdb.get_system_id(formatted_phone)
    if sys_id == hdb.get_customer_from_conv(group_id):  # customer is in conversation
        return True
    return False


def is_angel_ack(txt, emp_phone, customer_phone, group_id):
    """
    if msg is ack sign
    AND quoter is angel from the relevant group with permission
    AND quoted is customer of the relevant group

    """
    if txt in ANGEL_SIGN and \
            is_angel(raw_phone_number=emp_phone, group_id=group_id) and \
            is_customer(raw_phone_number=customer_phone, group_id=group_id):
        return True


# --------------------------------------------------------------------------------------------------------------------#

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
            msg_id = json_data["quoted"]["id"]
            group_id = json_data["conversation"]
            raw_angel_phone = json_data["user"]["phone"]
            raw_customer_phone = json_data["quoted"]["user"]["phone"]
            if is_angel_ack(txt=message["text"], emp_phone=raw_angel_phone, customer_phone=raw_customer_phone,
                            group_id=group_id):
                react_robot(group_id=group_id, msg_id=msg_id)
                if json_data['quoted']['type'] == 'ptt':
                    json_data['quoted']['timestamp'] = json_data['timestamp']
                    json_data['quoted']['quoter'] = raw_angel_phone
                    json_data['quoted']['conv_id'] = group_id
                    send_to_timluli(json_data=json_data['quoted'])
                else:
                    hdb.insert_message(msg_id=msg_id, conv_id=group_id,
                                       quoted_phone=format_phone_for_selection(raw_phone_number=raw_customer_phone),
                                       quoter_phone=format_phone_for_selection(raw_phone_number=raw_angel_phone),
                                       msg=json_data["quoted"]["text"], time_stamp=json_data["timestamp"])


# endregion

# region Private chat handles

def send_private_txt_msg(msg, to):
    if to != []:
        for t in to:
            body = {
                "type": "text",
                "message": msg,
                "to_number": t
            }
            send_msg(body=body)


def handle_income_private_msg(json_data):
    raw_phone_number = json_data['user']['id']
    formatted_phone_number = format_phone_for_selection(raw_phone_number=raw_phone_number)

    sys_id = hdb.get_system_id(phone_number=formatted_phone_number)
    if sys_id is None:
        send_private_txt_msg("מספר טלפון זה אינו במערכת! אנא פנה למנהל המערכת",
                             to=[raw_phone_number])
        return
    elif hdb.get_session(phone_number=formatted_phone_number) is None:
        hdb.insert_session(sys_id=sys_id)
        send_private_txt_msg("you have new session!", to=[raw_phone_number])

    ses_stage = hdb.get_session(phone_number=formatted_phone_number)[0][1]
    ses_permission = hdb.get_premission(phone_number=formatted_phone_number)
    run_conversation(ses_stage=ses_stage, permission=ses_permission, raw_phone_number=raw_phone_number,
                     income_msg=json_data['message']['text'], sys_id=sys_id)


def run_conversation(ses_stage, permission, raw_phone_number, income_msg, sys_id):
    # ---------- triggering QnA from admins phone --------------#
    if sys_id == 1 and income_msg.lower() == "qna":
        start_QnA()
        return
    # -----------------------------------------------------------#
    # income_msg = income_msg.lower()
    if ses_stage >= SESSION_DICT['IsReadyForQnA']:
        if income_msg != 'כן' and income_msg != 'לא':
            send_private_txt_msg(msg='בבקשה לענות רק בכן או לא', to=[raw_phone_number])
            return
        elif ses_stage == SESSION_DICT['ApproveQnA']:
            if income_msg == "כן":
                send_private_txt_msg(msg="תודה! אל תשכחי להעביר את הסיכום ללקוח. אני כבר אשלח לכל השאר :)",
                                     to=[raw_phone_number])
                raw_customer_phone=hdb.get_customer_waiting_for_approve(
                                      emp_phone=format_phone_for_selection(
                                          raw_phone_number=raw_phone_number
                                      ))
                send_daily_report(raw_emp_phone=raw_phone_number,
                                  raw_customer_phone=raw_customer_phone, is_approved=True)
            elif income_msg== "לא":
                send_private_txt_msg(msg="אוקיי. יש לתקן את הדוח ולשלוח אותו לראש הצוות וללקוח ", to=raw_phone_number)

            hdb.delete_waiting_for_approve(customer_phone=raw_customer_phone)
            hdb.update_stage(hdb.get_system_id(format_phone_for_selection(raw_phone_number=raw_phone_number)),
                             stage=SESSION_DICT['SendMenu'])
            return
        elif ses_stage == SESSION_DICT['QnA']:
            status = 0
            if income_msg == 'כן':
                status = 1
            pop_question(emp_phone=raw_phone_number, status=status)
        elif ses_stage == SESSION_DICT['IsReadyForQnA']:
            if income_msg == 'כן':
                hdb.update_stage(system_id=sys_id, stage=SESSION_DICT['QnA'])
        send_next_QnA(raw_emp_phone=raw_phone_number)


def handle_admin(ses_stage, raw_phone_number):
    if ses_stage == SESSION_DICT['SendMenu']:
        send_admin_menu(raw_phone_number=raw_phone_number)
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


def handle_timluli(json_data):
    global last_sent_to_timluli
    hdb.insert_message(msg_id=last_sent_to_timluli['msg_id'], conv_id=last_sent_to_timluli['conv_id'],
                       quoted_phone=format_phone_for_selection(last_sent_to_timluli['quoted_phone']),
                       quoter_phone=format_phone_for_selection(last_sent_to_timluli['quoter_phone']),
                       msg=get_headline_from_timluli(json_data['message']['text']),
                       time_stamp=last_sent_to_timluli['timestamp'])
    last_sent_to_timluli = None


def start_QnA():
    global Qpoll
    Qpoll = hdb.get_QnA_dict()
    emps_to_ask = hdb.get_QnA_emps()
    for e in emps_to_ask:
        emp_phone = e[0]
        hdb.update_stage(hdb.get_system_id(phone_number=emp_phone), stage=SESSION_DICT['IsReadyForQnA'])
        is_ready_for_QnA(format_phone_for_sending(phone_number=emp_phone))


def is_ready_for_QnA(emp_phone):
    send_private_txt_msg(f" היי *{hdb.get_employee_name(phone_number=format_phone_for_selection(emp_phone))}* \n"
                         f" מוכנה לסיכום היום שלנו? ", to=[emp_phone])


def send_next_QnA(raw_emp_phone):
    question = get_next_question(raw_emp_phone=raw_emp_phone)
    if question == None:
        return
    hdb.insert_sent_message(question['id'], format_phone_for_selection(raw_emp_phone))
    send_private_txt_msg(f"{question['BN']} ביקש ממך:\n {question['Q']}", [raw_emp_phone])
    # send_private_txt_msg(f"{question['BN']} asked you:\n {question['Q']}", raw_emp_phone)


def send_daily_report(raw_emp_phone, raw_customer_phone, is_approved=False):
    print(f"starting daily to number {raw_emp_phone}.is approved= {is_approved}")
    formatted_customer_phone = format_phone_for_selection(raw_phone_number=raw_customer_phone)
    formatted_emp_phone = format_phone_for_selection(raw_phone_number=raw_emp_phone)
    for status in range(1, -1, -1):
        msgs = hdb.get_daily(customer_phone=formatted_customer_phone, status=status)
        if status == 0:
            txt = f"*זה ישאר למחר:*\n"
        elif status == 1:
            if is_approved:
                txt= f" * סיכום היום של {hdb.get_employee_name(phone_number=formatted_emp_phone)} * \n"
                txt =txt+ f"עבור העסק {hdb.get_buisness_name(phone_number=formatted_customer_phone)} ביצענו היום : \n"
            elif not is_approved:
                txt = f" * היי {hdb.get_buisness_name(phone_number=formatted_customer_phone)} *\n "
                txt = txt + f"הנה מה שעשיתי בשבילך היום: \n"
                # txt = f"\n. זה מה שעשיתי בשבילך היום: {hdb.get_buisness_name(formatted_customer_phone)}* היי"
            # txt = f"*Hi {hdb.get_buisness_name(raw_emp_phone)}!*\n here is what we did for you today:"
        counter = 1
        for m in msgs:
            txt = txt + f"\n{counter}. {m[1]}"
            counter = counter + 1
        if not is_approved:
            send_private_txt_msg(msg=txt, to=[raw_emp_phone])
        elif is_approved:
            send_private_txt_msg(msg=txt, to=[
                format_phone_for_sending(phone_number=hdb.get_employee_phone(
                    system_id=hdb.get_team_leader_id(
                        customer_id=hdb.get_system_id(
                            phone_number=formatted_customer_phone
                        ))))])
    if not is_approved:
        hdb.update_stage(hdb.get_system_id(formatted_emp_phone),
                         stage=SESSION_DICT['ApproveQnA'])
        hdb.insert_waiting_for_approve(emp_number=formatted_emp_phone, customer_number=formatted_customer_phone)
        send_private_txt_msg(msg="האם את מאשרת את סיכום היום?", to=[raw_emp_phone])
    elif is_approved:
        hdb.delete_daily(customer_phone=formatted_customer_phone)


# endregion

# region Menus

def send_admin_menu(raw_phone_number):
    pass


# endregion


@app.route("/", methods=["POST"])
def webhook():
    json_data = request.get_json()
    json_data['timestamp'] = datetime.now().strftime(Tstamp_format)
    if json_data['type'] == 'error':
        return jsonify({"error": "Received an error message"}), 400
    elif json_data['type'] == 'ack':
        print("message was acked")
    elif 'conversation' in json_data and json_data['conversation'] == '972537750144@c.us':
        handle_timluli(json_data=json_data)
    elif json_data['type'] != 'ack':
        conv_type = json_data["conversation"].split('@')[1][0]
        if conv_type == group_chat_type:
            handle_group_msg(json_data=json_data)
        elif conv_type == private_chat_type:
            handle_income_private_msg(json_data=json_data)
    else:
        return jsonify({"Unknown Message": "Received an Unknown Message"}), 400
    return jsonify({"success": True}), 200


if __name__ == '__main__':
    start_QnA()
    app.run()
