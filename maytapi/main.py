from flask import Flask, request, jsonify
import requests
import sys
import base64
import os
from dotenv import load_dotenv
import DBSessionManeger as dbs
sys.path.append(os.path.abspath("C:\\Users\\40gil\\OneDrive\\Desktop\\Helpful"))
from HelpfulAI.Database.PythonDatabase import DBmain as Database


#region Globals and initializations

app = Flask(__name__)
load_dotenv(dotenv_path='Maytapi.env')
INSTANCE_URL = "https://api.maytapi.com/api"
PRODUCT_ID =os.getenv("PRODUCT_ID")
PHONE_ID = os.getenv("PHONE_ID")
API_TOKEN = os.getenv("TOKEN")
TRIAL_GROUP_ID=os.getenv("GROUP_ID")
ANGEL_SIGN=os.getenv("ACK_SIGN").split(',')
private_chat_type='c'
group_chat_type='g'
hdb = Database.Database()
sessions=dbs.get_session()

url = f"{INSTANCE_URL}/{PRODUCT_ID}/{PHONE_ID}/sendMessage"
headers = {
    "Content-Type": "application/json",
    "x-maytapi-key": API_TOKEN,
}

#endregion

#region Support functions

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
    print("okkk?")


def format_phone_for_selection(phone_number):
    # Remove leading '+' if present
    phone_number = phone_number.lstrip('+')

    # Check if the number starts with '972' and remove it
    if phone_number.startswith('972'):
        phone_number = phone_number[3:]

    # Check if the number starts with '0', if not, add '0' at the beginning
    if not phone_number.startswith('0'):
        phone_number = '0' + phone_number

    if phone_number.endswith('@c.us'):
        phone_number=phone_number[:10]

    return phone_number


def is_angel(phone_number,group_id=None):
    if group_id is None:
        return False
    formatted_phone=format_phone_for_selection(phone_number)
    sys_id=hdb.get_system_id(formatted_phone)
    if hdb.get_premission(formatted_phone)>=1 \
            and sys_id in hdb.get_employees_from_conv(group_id): # employee in group with premission
        return True
    return False


def is_customer(phone_number,group_id=None):
    if group_id is None:
        return False
    formatted_phone=format_phone_for_selection(phone_number)
    sys_id=hdb.get_system_id(formatted_phone)
    if sys_id == hdb.get_customer_from_conv(group_id): # customer is in conversation
        return True
    return False


def send_response(body):
    print("Request Body", body, file=sys.stdout, flush=True)
    url = INSTANCE_URL + "/" + PRODUCT_ID + "/" + PHONE_ID + "/sendMessage"
    headers = {
        "Content-Type": "application/json",
        "x-maytapi-key": API_TOKEN,
    }
    response = requests.post(url, json=body, headers=headers)
    print("Response", response.json(), file=sys.stdout, flush=True)
    return

def is_angel_ack(txt,e_phone,c_phone,group_id):
    """
    if msg is ack sign
    AND quoter is angel from the relevant group with premission
    AND quoted is customer of the relevant group

    """
    if txt in ANGEL_SIGN and \
            is_angel(e_phone, group_id) and \
            is_customer(c_phone, group_id):
        return True

#endregion

#region Group chat handlers

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
            if is_angel_ack(message["text"],angel_phone,customer_phone,group_id):
                    hdb.insert_message(json_data["quoted"]["id"], group_id, customer_phone, angel_phone,
                                           json_data["quoted"]["text"])

#endregion

#region Private chat handles

def send_private_msg(type,msg,to):
    if type == "text":
        body = {
            "type": "text",
            "message": msg,
            "to_number": to
        }
    send_msg(body)

def handle_private_msg(json_data):
    raw_phone_number = json_data['user']['id']
    sys_id = hdb.get_system_id(format_phone_for_selection(raw_phone_number))
    if sys_id == -1:
        sys_id = None
    if sys_id is None:
        send_private_msg("text","You are not in the system",raw_phone_number)
        return
    elif sys_id in sessions:
        send_private_msg("text", f"Your session stage is {sessions[sys_id]}", raw_phone_number)
    else:
        #need to create session
        print ('create session')
#endregion

@app.route("/", methods=["POST"])
def webhook():
    json_data = request.get_json()
    if json_data['type'] != 'ack':
        conv_type=json_data["conversation"].split('@')[1][0]
        if conv_type == group_chat_type:
            handle_group_msg(json_data)
        elif conv_type == private_chat_type:
            handle_private_msg(json_data)

    else:
        print("Unknow Message",  file=sys.stdout, flush=True)
    return jsonify({"success": True}), 200



if __name__=='__main__':
        app.run()


        """
        

        """