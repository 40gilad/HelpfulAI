# region Imports
import time
import random
from flask import Flask, request, jsonify
import requests
import sys
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import threading

sys.path.append(r'/home/ubuntu/HelpfulAI/Database/PythonDatabase')
import queue
import DBmain as Database


# endregion

# region Singletons

class SingletonBase:
    _instances = {}
    _locks = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._get_lock():
                if cls not in cls._instances:
                    cls._instances[cls] = super(SingletonBase, cls).__new__(cls, *args, **kwargs)
        return cls._instances[cls]

    @classmethod
    def _get_lock(cls):
        if cls not in cls._locks:
            cls._locks[cls] = threading.Lock()
        return cls._locks[cls]


class Globals(SingletonBase):
    TIMLULI_Q_SIZE = 30
    app = Flask(__name__)
    load_dotenv(dotenv_path='Maytapi.env')
    Tstamp_format = "%d/%m/%Y %H:%M"  # globals
    IS_QA = False  # globals

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True


class DatabaseHelper(SingletonBase):
    DB_ENV_PATH = r'/home/ubuntu/HelpfulAI/Database/PythonDatabase/DBhelpful.env'  # DB

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.hdb = Database.Database(env_path=self.DB_ENV_PATH)


class GepetoHelper(SingletonBase):
    OPENAI_KEY = os.getenv('OPENAI_KEY')
    GPT3 = "gpt-3.5-turbo"  # globals
    GPT4 = "gpt-4-0125-preview"  # globals
    TO_USE_GPT = False
    TO_SUMMERIZE = False

    def __init__(self, to_use_gpt=True, to_summerize=False):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.TO_SUMMERIZE = to_summerize
            self.TO_USE_GPT = to_use_gpt

    def __ask_gepeto__(self, prompt, model=GPT4):
        # ChatGPT API endpoint
        endpoint = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.OPENAI_KEY}"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        try:
            response = requests.post(endpoint, json=data, headers=headers)
            # Check if the request was successful
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"Error: {str(e)}"

    def is_task(self, message):
        json = {'is_task': False, "task": ""}

        if message is not None or message != "":
            answer = self.__ask_gepeto__(
                prompt=f'the following message:\n{message}\nis a message my boss sent me on whasapp.\n'
                       f'i want to know if it contains a task or an action i should do for him.\n'
                       f'please reply only with yes or no.')

            if 'yes' in answer.lower() and self.TO_SUMMERIZE:
                json['is_task'] = True
                answer = self.__ask_gepeto__(prompt=f'the following message:\n{message}\n'
                                                    f'is a task i need to do.\n'
                                                    f'please summerize the task for me in hebrew')
                json['task'] = answer
            return json


class MaytapiHelper(SingletonBase):
    PRODUCT_ID = os.getenv("PRODUCT_ID")  # maytapi
    PHONE_ID = os.getenv("PHONE_ID")  # maytapi
    API_TOKEN = os.getenv("TOKEN")  # maytapi
    INSTANCE_URL = os.getenv('INSTANCE_URL')
    CREATE_GROUP_SUFFIX = 'createGroup'

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.url = f"{self.INSTANCE_URL}/{self.PRODUCT_ID}/{self.PHONE_ID}"
            self.headers = {"Content-Type": "application/json", "x-maytapi-key": self.API_TOKEN}


class SessionManager(SingletonBase):
    SESSION_DICT = json.loads(os.getenv("SESSION_DICT"))

    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True

    def get_dict_val(self, key):
        # returns value of the key from session dict
        return self.SESSION_DICT[key]


class TimluliHelper(SingletonBase):
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.timluli_queue = queue.Queue(maxsize=Globals().TIMLULI_Q_SIZE)
            self.last_sent_to_timluli = None


class ConversationHelper(SingletonBase):
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.ROBOT_SIGN = ['🤖', '🦿', '🦾']  # conversation
            self.private_chat_type = 'c'  # conversation
            self.group_chat_type = 'g'  # conversation


class DaySummeryHelper(SingletonBase):
    Qpoll= None
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.db = DatabaseHelper().hdb


    def pop_question(self, emp_phone, status):
        """
        take question outside Qpoll and insert answer to database
        """
        emp_phone = format_phone_for_selection(raw_phone_number=emp_phone.split('@')[0])
        if self.Qpoll is not None:
            for d in self.Qpoll:
                if d['emp'] == emp_phone:
                    answerd_id = self.db.get_sent_message(emp_phone=emp_phone)  # get id of last sent question
                    index = 0
                    for q in d['questions']:
                        if answerd_id == q[0]:
                            answerd = d['questions'].pop(index)
                            self.insert_answer(msg_id=answerd[0], status=status)
                            self.db.insrt_daily_msg(msg_id=answerd[0],
                                               customer_phone=format_phone_for_selection(d['customer']),
                                               status=status)
                            self.db.delete_sent_message(msg_id=answerd_id)  # delete last sent question from DB
                            return
                        index += 1

    def start_QnA(self):
        self.Qpoll = self.db.get_QnA_dict()
        emps_to_ask = self.db.get_QnA_emps()
        for e in emps_to_ask:
            emp_phone = e[0]
            self.db.update_stage(self.db.get_system_id(phone_number=emp_phone),
                            stage=SessionManager().get_dict_val(key="IsReadyForQnA"))
            is_ready_for_QnA(emp_phone=emp_phone)

    def insert_answer(self,msg_id, status):
        if status == 0:
            return
        elif status == 1:
            self.db.update_msg_status(msg_id=msg_id)

    def get_next_question(raw_emp_phone):
        emp_phone = format_phone_for_selection(raw_emp_phone)
        is_emp_in_poll = False
        emp_phone = emp_phone.split('@')[0]
        for d in Qpoll:
            if d['emp'] == emp_phone:
                raw_customer_phone = d['customer']
            if d['questions'] != []:
                is_emp_in_poll = True
                return {
                    'Q': d['questions'][0][1],
                    'BN': hdb.get_buisness_name(phone_number=format_phone_for_selection(d['customer'])),
                    'id': d['questions'][0][0]
                }
            else:
                break
            # for d in Qpoll:
            #     print(f"{d['emp']}-{d['customer']}")
        if not is_emp_in_poll:
            finish_QnA(emp_phone=raw_emp_phone,
                       customer_phone=raw_customer_phone)  # here! customers phone is from d

    def finish_QnA(emp_phone, customer_phone):
        send_private_txt_msg(msg="תודה! הנה סיכום היום שלך:", to=[emp_phone])
        # hdb.update_stage(system_id=hdb.get_system_id(phone_number=format_phone_for_selection(emp_phone)),stage=SESSION_DICT['SendMenu'])
        send_daily_report(raw_emp_phone=emp_phone, raw_customer_phone=customer_phone)


# endregion

# region Support functions


# -------------------------------------------------- QNA SUPPORTERS --------------------------------------------------#

def utc_plus_3():
    return datetime.now() + timedelta(hours=3)





# --------------------------------------------------------------------------------------------------------------------#
# ----------------------------------------------------- TIMLULI ------------------------------------------------------#

def timluli_is_locked():
    if last_sent_to_timluli is None:
        return False
    return True


def get_headline_from_timluli(text):
    return text.split('*')[1]


def send_to_timluli(json_data):
    global timluli_queue
    global last_sent_to_timluli
    global TO_USE_GPT
    if TO_USE_GPT:
        keys = ['msg_id', 'conv_id', 'quoted_phone', 'timestamp']
        timluli_dict = dict.fromkeys(keys)
        timluli_dict.update({
            'msg_id': json_data['message']['id'],
            'conv_id': json_data['conversation'],
            'quoted_phone': json_data['user']['phone'],
            'timestamp': json_data['timestamp']
        })
        while timluli_queue.full():
            forward_to_timluli()
        timluli_queue.put(timluli_dict)
    else:
        send_msg_to_gilad(f"got json data in send_to_timluli func and TO_USE_GPT is {TO_USE_GPT}")
    if IS_QA:
        queue_contents = list(timluli_queue.queue)

        # Now you can iterate over the queue contents and print each item
        for item in queue_contents:
            print(item)
    print(f'last send to timluli AFTER:{last_sent_to_timluli}')


def forward_to_timluli():
    global timluli_queue
    global last_sent_to_timluli
    while timluli_is_locked():
        time.sleep(10)  # wait 10 seconds until next check
        print("in forward_to_timluli: last_sent_to_timluli is not None")
    last_sent_to_timluli = timluli_queue.get()
    print(f"forwarding to timluli: {last_sent_to_timluli}")
    forward_msg(msg=last_sent_to_timluli['msg_id'], to=timluli)


def pop_timluli():
    global timluli_queue
    while True:
        if timluli_queue.empty():
            print("timluli_queue is empty. will check again in 10 mins")
            time.sleep(5 * 60)  # wait 5 mins
        else:
            forward_to_timluli()


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
    write_log(json_data=body, outcome=True)


def react_robot(group_id, msg_id):
    body = {
        "to_number": group_id,
        "type": "reaction",
        "message": ROBOT_SIGN[random.randint(0, len(ROBOT_SIGN) - 1)],
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

def write_log(json_data, outcome=False, income=False):
    try:
        with open('log.txt', 'a') as log:
            if json_data["type"] == 'text' or json_data["type"] == 'message' or json_data["type"] == 'reaction':
                if income and 'text' in json_data['message']:
                    log.write(
                        '##################################################################################################\n')
                    log.write(
                        f"{json_data['timestamp']}:\t{json_data['user']['phone']}({json_data['user']['name']}) - in {json_data['conversation']}:\n")
                    log.write(f"\tMessage: {json_data['message']['text']}\n")
                elif outcome:
                    log.write(f"{utc_plus_3().strftime(Tstamp_format)}:\tresponse to {json_data['to_number']}:\n")
                    log.write(f"\t Message: {json_data['message']}\n")
                else:
                    log.write(
                        f"\n--------------------------------------------------------------------------------------\n JSON DATA \n\t{json_data}\n --------------------------------------------------------------------------------------\n\n\n")

    except():
        log.write(json_data)


def create_log_file():
    print("Log file doesn't exist. Creating a new one...")
    with open('log.txt', 'w') as new_log:
        new_log.write(
            f"-------------------------     CREATION TIME (UTC): {datetime.now().strftime(Tstamp_format)}     -------------------------\n")


def trigeer_QnA():
    while True:
        current_hour = (time.localtime().tm_hour) + 3  # UTC Time + 3 = israel Summer clock
        if current_hour == 17:  # desired hour to trigger function (will be checked once at 19:00-19:59
            start_QnA()
            print("It's 17:00 ")
            time.sleep(15 * 60 * 60)  # Sleep for 15 hours
        else:
            print(f"It's not 20:00. Waiting for 55 minutes. Current time: {current_hour}")
            time.sleep(55 * 60)  # Sleep for 55 minutes


def check_db_connection():
    while True:
        print("Checking if db is connected...")
        try:
            if hdb.check_database_connection():  # db is connected
                print("Database is connected.")
                time.sleep(10 * 60 * 60)  # Sleep for 10 hours
            else:
                print("Database is not connected. Attempting to reconnect...")
                hdb.reconnect_to_database(env_path=r'/home/ubuntu/HelpfulAI/Database/PythonDatabase/DBhelpful.env')
                if hdb.check_database_connection():  # db is connected after retry
                    print("Database reconnected successfully.")
                    time.sleep(10 * 60 * 60)  # Sleep for 10 hours
                else:
                    print("Database reconnect failed. Retrying in 10 minutes.")
                    send_msg_to_gilad(msg="DB is Inactive!!")
                    time.sleep(10 * 60 * 60)  # Sleep for 10 hours
        except Exception as e:
            print("An error occurred:", e)
            print("Retrying in 10 minutes.")
            send_msg_to_gilad(msg="Erro while trying to reconnect to DB")
            time.sleep(10 * 60 * 60)  # Retry after 10 hours


def check_log_file():
    while True:
        log_file = "log.txt"
        if os.path.exists(log_file):

            creation_time = datetime.fromtimestamp(os.path.getctime(log_file))
            current_date = datetime.now().date()

            # Check if a week has passed since creation
            print(f"Log file exists since {creation_time.date()}. timedelta: {current_date - creation_time.date()}")
            if current_date - creation_time.date() >= timedelta(days=7):
                # Delete the old log file
                os.remove(log_file)
                print("Old log file deleted.")
                create_log_file()

        else:
            print("Log file doesn't exist.")
            create_log_file()

        # Check every 24 hours
        time.sleep(24 * 60 * 60)


def execute_post(body, url_suffix):
    try:
        response = requests.post(f'{url}/{url_suffix}', json=body, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        print(f"{response} \n\t{response.json()}")
        if url_suffix is CREATE_GROUP_SUFFIX:
            if response.json()['success'] == True:
                return response.json()['data']['id']
            else:
                return response.json()
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
    global TO_USE_GPT
    if TO_USE_GPT:
        handle_group_msg_gpt(json_data)
        return

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
                    DatabaseHelper().hdb.insert_message(msg_id=msg_id, conv_id=group_id,
                                       quoted_phone=raw_customer_phone,
                                       quoter_phone=raw_angel_phone,
                                       msg=json_data["quoted"]["text"], time_stamp=json_data["timestamp"])


def handle_group_msg_gpt(json_data):
    print(f"handle group msg gpt:\n{json_data}")
    wttype = json_data["type"]
    if wttype == "message":

        message = json_data["message"]
        group_id = json_data["conversation"]
        msg_id = message["id"]
        _type = message["type"]
        raw_customer_phone = json_data["user"]["id"]
        if not is_customer(raw_phone_number=raw_customer_phone, group_id=json_data['conversation']):
            return
        if message["fromMe"]:
            return
        if _type == "text":
            ret_json = is_task(message=message["text"])
            answer = ret_json["is_task"]
            print(f'ret_json= {ret_json}')
            if answer is False:
                return
            elif answer is True:
                react_robot(group_id=group_id, msg_id=msg_id)
                angel_phone = hdb.get_angle_phone_by_group_id(group_id=group_id)
                hdb.insert_message(msg_id=msg_id, conv_id=group_id,
                                   quoted_phone=format_phone_for_selection(raw_phone_number=raw_customer_phone),
                                   quoter_phone=angel_phone,
                                   msg=ret_json['task'], time_stamp=json_data["timestamp"])
        elif _type == "ptt":
            send_to_timluli(json_data)


# endregion

# region Private chat handles

def send_private_txt_msg(msg, to):
    if to != []:
        for t in to:
            format_phone_for_sending(t)
            body = {
                "type": "text",
                "message": msg,
                "to_number": t
            }
            send_msg(body=body)


def send_msg_to_gilad(msg):
    send_private_txt_msg(msg=msg, to=['972526263862'])


def handle_income_private_msg(json_data):
    write_log(json_data=json_data)
    raw_phone_number = json_data['user']['id']

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
    if sys_id == 1 or sys_id == 2:  #talking to gilad
        if income_msg.lower() == "qna":
            start_QnA()
            return
        elif income_msg.lower() == 'ping':
            send_private_txt_msg(msg='pong', to=[raw_phone_number])
            return
    # -----------------------------------------------------------#
    # income_msg = income_msg.lower()
    if ses_stage >= SESSION_DICT['IsReadyForQnA']:
        if income_msg != 'כן' and income_msg != 'לא':
            send_private_txt_msg(msg='בבקשה לענות רק בכן או לא', to=[raw_phone_number])
            return
        elif ses_stage == SESSION_DICT['ApproveQnA']:
            if income_msg == "כן":
                send_private_txt_msg(msg="תודה! אל תשכחי להעביר את הסיכום ללקוח :)",
                                     to=[raw_phone_number])
                raw_customer_phone = hdb.get_customer_waiting_for_approve(
                    emp_phone=format_phone_for_selection(
                        raw_phone_number=raw_phone_number
                    ))
                # send_daily_report(raw_emp_phone=raw_phone_number,
                #                   raw_customer_phone=raw_customer_phone, is_approved=True)
            elif income_msg == "לא":
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
    global TO_USE_GPT
    curr_timlul = last_sent_to_timluli
    last_sent_to_timluli = None
    if TO_USE_GPT:
        raw_msg = json_data['message']["text"]  # raw_msg.split('\n\n')[1] is the timlul, raw_msg...[0] is the headline
        ret_json = is_task(message=raw_msg.split('\n\n')[1])
        answer = ret_json["is_task"]
        print(f"Accroding to ChatGPT, this message is {answer} task: {json_data['message']['text']}")
        if answer is True:
            react_robot(group_id=curr_timlul['conv_id'], msg_id=curr_timlul['msg_id'])
            angel_phone = hdb.get_angle_phone_by_group_id(group_id=curr_timlul['conv_id'])
            hdb.insert_message(msg_id=curr_timlul['msg_id'], conv_id=curr_timlul['conv_id'],
                               quoted_phone=format_phone_for_selection(curr_timlul['quoted_phone']),
                               quoter_phone=angel_phone,
                               msg=raw_msg.split('\n\n')[1],
                               time_stamp=json_data["timestamp"])


def is_ready_for_QnA(emp_phone):
    send_private_txt_msg(f" היי *{hdb.get_employee_name(phone_number=format_phone_for_selection(emp_phone))}* \n"
                         f" זה הבוט של הלפפול :) \n"
                         f" מוכנה לסיכום היום שלנו? "
                         f"אני אכתוב לך מה ביקשו ממך במהלך היום ואת תגידי לי אם ביצעת את זה או לא"
                         f"(יש לענות רק בכן או לא)", to=[emp_phone])


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
                txt = f" * סיכום היום של {hdb.get_employee_name(phone_number=formatted_emp_phone)} * \n"
                txt = txt + f"עבור העסק {hdb.get_buisness_name(phone_number=formatted_customer_phone)} ביצענו היום : \n"
            elif not is_approved:
                txt = f" * היי {hdb.get_buisness_name(phone_number=formatted_customer_phone)} *\n "
                txt = txt + f"הנה מה שעשיתי בשבילך היום: \n"
        counter = 1
        for m in msgs:
            txt = txt + f"\n{counter}. {m[1]}"
            counter = counter + 1
        if not is_approved:
            send_private_txt_msg(msg=txt, to=[raw_emp_phone])
        # elif is_approved:
        #     send_private_txt_msg(msg=txt, to=[
        #         format_phone_for_sending(phone_number=hdb.get_employee_phone(
        #             system_id=hdb.get_team_leader_id(
        #                 customer_id=hdb.get_system_id(
        #                     phone_number=formatted_customer_phone
        #                 ))))])
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
    write_log(json_data=json_data, income=True)
    json_data['timestamp'] = datetime.now().strftime(Tstamp_format)
    # region QA:
    if IS_QA:
        if 'user' not in json_data:
            return jsonify({"ack": "Received an ack message"}), 200
        if '972526263862@c.us' == json_data["user"]["id"] or '972537750144@c.us' == json_data["user"]["id"]:
            if json_data['type'] == 'error':
                return jsonify({"error": "Received an error message"}), 400

            elif json_data['type'] == 'ack':  # returned acknowledgement from the receiver
                print("message was acked")

            elif ('conversation' in json_data and json_data['conversation']
                  == '972537750144@c.us'):  # returned voice to txt from timluli
                handle_timluli(json_data=json_data)

            elif json_data['type'] != 'ack':  # not ack and not timluli
                conv_type = json_data["conversation"].split('@')[1][0]
                if conv_type == group_chat_type:
                    handle_group_msg_gpt(json_data=json_data)
                elif conv_type == private_chat_type:
                    handle_income_private_msg(json_data=json_data)
            else:
                return jsonify({"Unknown Message": "Received an Unknown Message"}), 400
            return jsonify({"success": True}), 200
        else:
            return jsonify({"Unknown Message ": "Message not from Admin during QA"}), 400
    # endregion
    else:  # not qa
        if 'user' not in json_data:
            print(json_data)
            return jsonify({"non-msg": "Received non message"}), 400
        if json_data['type'] == 'error':
            print(f'Error:{json_data}')
            return jsonify({"error": "Received an error message"}), 400

        elif json_data['type'] == 'ack':  # returned acknowledgement from the receiver
            print("message was acked")

        elif ('conversation' in json_data and json_data['conversation']
              == '972537750144@c.us'):  # returned voice to txt from timluli
            handle_timluli(json_data=json_data)

        elif json_data['type'] != 'ack':  # not ack and not timluli
            conv_type = json_data["conversation"].split('@')[1][0]
            if conv_type == group_chat_type:
                handle_group_msg(json_data=json_data)
            elif conv_type == private_chat_type:
                handle_income_private_msg(json_data=json_data)
        else:
            print(f"unknown{json_data}")
            return jsonify({"Unknown Message": "Received an Unknown Message"}), 400
        return jsonify({"success": True}), 200


if __name__ == '__main__':
    #app.run()
    #start_QnA()
    from waitress import serve

    TO_USE_GPT = True
    IS_QA = False

    #check if its time for day conclusion
    hour_check_thread = threading.Thread(target=trigeer_QnA)
    hour_check_thread.start()

    #check if db is connected
    db_connection_thread = threading.Thread(target=check_db_connection)
    db_connection_thread.start()

    #handle timluli queue
    timluli_queue_thread = threading.Thread(target=pop_timluli)
    timluli_queue_thread.start()

    serve(app)
