from flask import Flask, request, jsonify
import requests
import sys
import base64
import os
from dotenv import load_dotenv
sys.path.append(os.path.abspath("C:\\Users\\40gil\\OneDrive\\Desktop\\Helpful"))
from HelpfulAI.Database.PythonDatabase import DBmain as Database

app = Flask(__name__)

load_dotenv(dotenv_path='Maytapi.env')
INSTANCE_URL = "https://api.maytapi.com/api"
PRODUCT_ID =os.getenv("PRODUCT_ID")
PHONE_ID = os.getenv("PHONE_ID")
API_TOKEN = os.getenv("TOKEN")
TRIAL_GROUP_ID=os.getenv("GROUP_ID")
ANGEL_SIGN=os.getenv("ACK_SIGN").split(',')
hdb = Database.Database()



def getCatalog():
    url = INSTANCE_URL + "/" + PRODUCT_ID + "/" + PHONE_ID + "/catalog"
    payload = {}
    headers = {
        "Content-Type": "application/json",
        "x-maytapi-key": API_TOKEN,
    }
    r = requests.request('GET', url, headers=headers, data=payload)
    tjson = r.json()
    pData = tjson["data"]
    pSuccess = tjson["success"]
    if pSuccess == True and len(pData) > 0:
        pId = tjson["data"][0]["productId"]
        return pId
    else:
        return 0


def format_phone_for_selection(phone_number):
    # Remove leading '+' if present
    phone_number = phone_number.lstrip('+')

    # Check if the number starts with '972' and remove it
    if phone_number.startswith('972'):
        phone_number = phone_number[3:]

    # Check if the number starts with '0', if not, add '0' at the beginning
    if not phone_number.startswith('0'):
        phone_number = '0' + phone_number

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


@app.route("/", methods=["POST"])
def webhook():
    json_data = request.get_json()

    wttype = json_data["type"]
    if wttype == "message":
        message = json_data["message"]
        _type = message["type"]
        if message["fromMe"]:
            return
        if _type == "text" and 'quoted' in json_data:
            group_id=json_data["conversation"]
            angel_phone=json_data["user"]["phone"]
            customer_phone=json_data["quoted"]["user"]["phone"]
            if message['text'] in ANGEL_SIGN: # if msg is ack sign
                if is_angel(angel_phone,group_id): #quoter is angel from the relevant group with premission
                    if is_customer(customer_phone,group_id): #quoted is customer of the relevant group
                        hdb.insert_message(json_data["quoted"]["id"],group_id,customer_phone,angel_phone,json_data["quoted"]["text"])

    else:
        print("Unknow Type:", wttype,  file=sys.stdout, flush=True)
    return jsonify({"success": True}), 200



if __name__=='__main__':
        app.run()


        """
        
        body = {
            "type": "reaction",
            "message": "😀",
            "to_number": '',
            "reply_to":""
        }
        print("Request Body", body, file=sys.stdout, flush=True)

        url = f"{INSTANCE_URL}/{PRODUCT_ID}/{PHONE_ID}/sendMessage"
        headers = {
            "Content-Type": "application/json",
            "x-maytapi-key": API_TOKEN,
        }

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
        """