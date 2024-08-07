import os
import json
import datetime
import requests
import pytz
from dotenv import load_dotenv
import boto3
from requests.exceptions import HTTPError

load_dotenv()

API_ENDPOINT = 'https://apiappv2.arboxapp.com'
USER_EMAIL = os.getenv('USER_EMAIL')
USER_PASSWORD = os.getenv('USER_PASSWORD')
SNS_REGION = os.getenv('SNS_REGION')
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN')
TARGET_HOUR = int(os.getenv('TARGET_HOUR', 18))  # 6 p.m
SCHEDULE_CONFIG = json.loads(os.getenv('SCHEDULE_CONFIG', '{"6": "GAIN", "1": "WOD", "3": "WOD"}'))

# Hardcoded class ID mapping
CLASS_ID_MAPPING = {
    'WOD': [40066, 40067],
    'Weightlifting': [40069],
    'GAIN': [50223, 40072],
    'Endurance': [40068],
    'MOBILITY': [50226],
    'Gymnastics': [40070]
}

# Common headers
HEADERS = {
    "content-type": "application/json",
    "accept": "application/json, text/plain, */*",
    "version": "11",
    "referername": "app",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    "user-agent": "HYPRtraining/4000531 CFNetwork/1492.0.1 Darwin/23.3.0",
    "whitelabel": "HYPR-training",
    "refreshtoken": "undefined",
}

def log(message):
    print(message)  # This will output to CloudWatch in AWS Lambda

def perform_login():
    login_url = f"{API_ENDPOINT}/api/v2/user/login"
    login_payload = {"email": USER_EMAIL, "password": USER_PASSWORD}

    try:
        response = requests.post(login_url, json=login_payload, headers=HEADERS, verify=False)
        response.raise_for_status()
        data = response.json()['data']
        log(f"Logged in successfully. User ID: {data['id']}")
        return data['token'], data['id']
    except HTTPError as http_err:
        log(f"HTTP error occurred: {http_err}")
        raise Exception(f"HTTP error occurred: {http_err}")
    except Exception as err:
        log(f"An error occurred during login: {err}")
        raise Exception(f"An error occurred: {err}")

def israel_is_dst():
    tz = pytz.timezone('Asia/Jerusalem')
    now = datetime.datetime.now(tz)
    return now.dst() != datetime.timedelta(0)

def get_target_datetime(current_datetime):
    target_hour = TARGET_HOUR
    days_to_add = {6: 2, 1: 2, 3: 3}  # Sunday -> Tuesday, Tuesday -> Thursday, Thursday -> Sunday
    days_ahead = days_to_add.get(current_datetime.weekday(), 2)
    target_date = current_datetime + datetime.timedelta(days=days_ahead)
    log(f"Calculated target date: {target_date}")
    return target_date.replace(hour=target_hour, minute=0, second=0, microsecond=0)

def get_schedule_id_for_class(auth_token, target_datetime, class_ids):
    date_str = target_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
    target_time_str = target_datetime.strftime("%H:%M")
    schedules_url = f"{API_ENDPOINT}/api/v2/schedule/betweenDates"

    params = {
        "from": date_str,
        "to": date_str,
        "locations_box_id": 48,
        "boxes_id": 59
    }

    headers_with_auth_token = HEADERS.copy()
    headers_with_auth_token["accessToken"] = auth_token

    try:
        response = requests.post(schedules_url, headers=headers_with_auth_token, params=params, verify=False)
        response.raise_for_status()
        schedules = response.json().get('data', [])
        for schedule_item in schedules:
            log(f"Checking schedule item: {schedule_item}")
            if schedule_item['box_category_fk'] in class_ids and schedule_item['time'] == target_time_str:
                log(f"Found matching schedule: {schedule_item['id']} for class ID: {schedule_item['box_category_fk']}")
                return schedule_item['id'], schedule_item['time'], schedule_item['box_categories']['name']
    except Exception as e:
        log(f"Failed to get schedule id: {e}")
    return None, None, None

def get_membership_id(auth_token):
    membership_url = f"{API_ENDPOINT}/api/v2/boxes/59/memberships/1?XDEBUG_SESSION_START=PHPSTORM"

    headers_with_auth_token = HEADERS.copy()
    headers_with_auth_token["accessToken"] = auth_token

    try:
        response = requests.get(membership_url, headers=headers_with_auth_token, verify=False)
        response.raise_for_status()
        data = response.json().get('data', [{}])
        membership_id = data[0].get('id') if data else None
        log(f"Retrieved membership ID: {membership_id}")
        return membership_id
    except Exception as e:
        log(f"Failed to get membership id: {e}")
    return None

def register_for_class(auth_token, membership_user_id, schedule_id, class_time, class_name):
    register_url = f"{API_ENDPOINT}/api/v2/scheduleUser/insert"
    payload = {
        'schedule_id': schedule_id,
        'membership_user_id': membership_user_id,
        'extras': None
    }

    headers_with_token = HEADERS.copy()
    headers_with_token["accessToken"] = auth_token

    try:
        response = requests.post(register_url, headers=headers_with_token, json=payload, verify=False)
        response.raise_for_status()
        send_sns_notification("Registration Successful",
                              f"Successfully registered for class with schedule ID: {schedule_id}\n"
                              f"Details: {class_time}\tat\t{class_name}")
        log(f"Registered successfully for class with schedule ID: {schedule_id}")
    except Exception as e:
        send_sns_notification("Registration Failed",
                              f"Failed to register to class: {class_name} at time: {class_time}\n{e}")
        log(f"Failed to register for class: {e}")

def send_sns_notification(subject, message):
    # enable in local test
    # aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    # aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    sns_client = boto3.client('sns', region_name=SNS_REGION)
    # enable in local test
    # aws_access_key_id=aws_access_key_id,
    # aws_secret_access_key=aws_secret_access_key
    try:
        sns_client.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject=subject)
        log(f"SNS notification sent: {subject}")
    except Exception as e:
        log(f"Failed to send SNS notification: {e}")

def lambda_handler(event, context):
    try:
        auth_token, _ = perform_login()
        utc_now = datetime.datetime.utcnow()

        if israel_is_dst():
            israel_now = utc_now + datetime.timedelta(hours=3)
        else:
            israel_now = utc_now + datetime.timedelta(hours=2)

        log(f"Current Israel time: {israel_now}")

        target_datetime = get_target_datetime(israel_now)
        class_name = SCHEDULE_CONFIG.get(str(israel_now.weekday()))
        class_ids = CLASS_ID_MAPPING.get(class_name, [])

        log(f"Class name for today: {class_name}")
        log(f"Class IDs: {class_ids}")

        if not class_ids:
            raise Exception(f"No class IDs found for the specified class: {class_name}")

        schedule_id, class_time, class_name = get_schedule_id_for_class(auth_token, target_datetime, class_ids)

        if schedule_id:
            membership_user_id = get_membership_id(auth_token)
            if membership_user_id:
                register_for_class(auth_token, membership_user_id, schedule_id, class_time, class_name)
                return {
                    'statusCode': 200,
                    'body': json.dumps("Successfully registered for the class.")
                }
            else:
                raise Exception("No membership ID found for registration.")
        else:
            raise Exception("No schedule ID found for registration.")
    except Exception as e:
        log(f"Registration process failed: {e}")
        send_sns_notification("Registration Failed", f"Failed to register for class: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Failed to register for the class: {e}")
        }

# Uncomment for local testing only, not for production
# if __name__ == "__main__":
#     lambda_handler({}, {})
