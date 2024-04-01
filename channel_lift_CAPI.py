import requests
import json
import configparser
import csv
from hashlib import sha256
import logging

config = configparser.ConfigParser()
config.read('config.ini')

# SET VARIABLES TO MAKE CAPI CALL
ACCESS_TOKEN = config['dataset']['access_token']
DATASET_ID = config['dataset']['dataset_id']
API_VERSION = config['dataset']['api_version']
API_ENDPOINT = "https://graph.facebook.com/{0}/{1}/events?access_token={2}".format(API_VERSION, DATASET_ID, ACCESS_TOKEN)
CHANNEL_ATTRIBUTION_DATA_FILE = config['channel_attribution_data_file']['path']
USER_DATA_SECTION = config.items('user_data')
OPTIONAL_CUSTOM_DATA_SECTION = config.items('optional_custom_data')
REQUIRED_CAPI_PARAMETERS_KEYS= ['event_time', 'event_name']
REQUIRED_CUSTOM_PARAM_KEYS = ['currency', 'value']
USER_DATA_COLUMN_NAME = []
OPTIONAL_CUSTOM_DATA_COLUMN_NAME = []
API_LOG_FILE_PATH = config['log_file']['path']
API_LOG_FILE_NAME = config['log_file']['filemame']
ACTION_SOURCE = "website"

CAPI_USER_DATA_COLUMN_NAME_MAPPING_TO_PAYLOAD_KEY = {
    "email" : "em",
    "phone_number" : "ph",
    "first_name" : "fn",
    "last_name" : "ln",
    "gender" : "ge",
    "data_of_birth" : "db",
    "city " : "ct",
    "state" : "st",
    "zip_code" : "zp",
    "country" : "country"
}

CAPI_CUSTOM_DATA_COLUMN_NAME_MAPPING_TO_PAYLOAD_KEY = {
"content_type" : "content_type",
"contents" : "contents",
"custom_data" : "custom_data",
"order_id" : "order_id",
"item_number" : "item_number"
}

# Set up logging
logging.basicConfig(filename=API_LOG_FILE_PATH + API_LOG_FILE_NAME,
                    filemode='a',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

USER_DATA_COLUMN_ENTRY = []
CUSTOM_DATA_COLUMN_ENTRY = []

# user data that is available in the csv file
for key in USER_DATA_SECTION:
    if key[1] != 'absent':
      USER_DATA_COLUMN_ENTRY.append(key)
      USER_DATA_COLUMN_NAME.append(key[1])

# custom data that is available in the csv file
for key in OPTIONAL_CUSTOM_DATA_SECTION:
  if key[1] != 'absent':
    CUSTOM_DATA_COLUMN_ENTRY.append(key)
    OPTIONAL_CUSTOM_DATA_COLUMN_NAME.append(key[1])

# opening the CSV file
with open(CHANNEL_ATTRIBUTION_DATA_FILE, mode='r')as file:
  # reading the CSV file
  capi_events_csv_file = csv.DictReader(file)

  #read all column names/header
  capi_events_csv_file_headers = capi_events_csv_file.fieldnames

  # # Check if all required custom fields are present
  if(all(header in capi_events_csv_file_headers for header in REQUIRED_CUSTOM_PARAM_KEYS)):
    logging.info("REQUIRED CUSTOM KEYS ARE PRESENT, GOING TO NEXT STEP")
  else:
    logging.error("REQUIRED CUSTOM KEYS ARE ABSENT, ABORTING")
    exit()

  # # Check if all required fields are present
  if(all(header in capi_events_csv_file_headers for header in REQUIRED_CAPI_PARAMETERS_KEYS)):
    logging.info("REQUIRED KEYS ARE PRESENT, GOING TO NEXT STEP")
  else:
    logging.error("REQUIRED KEYS ARE ABSENT, ABORTING")
    exit()

  # Check if all user_data specified in the config file is present in the CSV File
  if(all(header in capi_events_csv_file_headers for header in USER_DATA_COLUMN_NAME)):
    logging.info("USER DATA IS PRESENT, GOING TO NEXT STEP")
  else:
    logging.error("USER DATA IS ABSENT, ABORTING")
    exit()

# Check if all custom_data specified in the config file is present in the CSV File
  if(all(header in capi_events_csv_file_headers for header in OPTIONAL_CUSTOM_DATA_COLUMN_NAME)):
    logging.info("OPTIONAL DATA SPECFIED IN CONFIG IS PRESENT, GOING TO NEXT STEP")
  else:
    logging.error("OPTIONAL DATA SPECFIED IN CONFIG IS ABSENT, ABORTING")
    exit()

  # displaying the contents of the CSV file
  for lines in capi_events_csv_file:
        capi_web_data = {}
        user_data = {}
        custom_data = {}
        # Setting Action Source
        capi_web_data["action_source"] = ACTION_SOURCE

        # Get all custom data required fields
        for key in REQUIRED_CUSTOM_PARAM_KEYS:
          custom_data[key] = lines[key]

        # Get all required fields
        for key in REQUIRED_CAPI_PARAMETERS_KEYS:
          capi_web_data[key] = lines[key]

        # Get all user fields
        for key in USER_DATA_COLUMN_ENTRY:
          user_data[CAPI_USER_DATA_COLUMN_NAME_MAPPING_TO_PAYLOAD_KEY[key[0]]] = sha256(lines[key[1]].encode('utf-8')).hexdigest()

        # Get all optional fields
        for key in CUSTOM_DATA_COLUMN_ENTRY:
          custom_data[CAPI_CUSTOM_DATA_COLUMN_NAME_MAPPING_TO_PAYLOAD_KEY[key[0]]] = lines[key[1]]

        # Construct the payload
        capi_web_data["user_data"] = user_data
        capi_web_data["custom_data"] = custom_data

        capi_web_payload = {"data": [capi_web_data]}
        # Make the CAPI for Web API Call
        payload = json.dumps(capi_web_payload)
        logging.info(payload)
        headers = {
            'Content-Type': 'application/json',
            'Cookie': 'cm_j=none'
        }
        response = requests.request("POST", API_ENDPOINT, headers = headers, data = payload)
        if(response.status_code == 200):
          logging.info(response.text)
        else:
          logging.error(response.text)
