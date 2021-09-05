#!/usr/bin/python
# -----------------------------------------------------------
# Python client that retrieves a feed from Maltiverse.com
# Stores results in Redis database
#
# (C) 2021 Maltiverse
# Released under GNU Public License (GPL)
# -----------------------------------------------------------

import argparse
import json
from datetime import datetime, timedelta
import redis
import requests

parser = argparse.ArgumentParser()

parser.add_argument('--maltiverse_email', dest='maltiverse_email', required=True,
                    help='Specifies Maltiverse email for login. Required')
parser.add_argument('--maltiverse_password', dest='maltiverse_password', required=True,
                    help='Specifies Maltiverse password for login. Required')
parser.add_argument('--feed', dest='maltiverse_feed', required=True,
                    help='Specifies Maltiverse Feed ID to retrieve. Required')
parser.add_argument('--range', dest='maltiverse_range', default=None,
                    help='Specifies Feed time range. Examples now-1h, now-1W, now-1m')
parser.add_argument('--range_field', dest='maltiverse_range_field', default="modification_time",
                    help='Specifies the datetime field to apply filtering range. Available options are creation_time and modification_time')
parser.add_argument('--feed-expiration-days', dest='maltiverse_feed_expiration_days', default=30,
                    help='Specifies Maltiverse Feed ID to retrieve. Required')
parser.add_argument('--redis_host', dest='redis_host', default="localhost",
                    help='Specifies Redis database destination hostname. Default localhost')
parser.add_argument('--redis_port', dest='redis_port', default=6379,
                    help='Specifies Redis database destination hostname port. Default 6379')
parser.add_argument('--redis_password', dest='redis_password', default=None,
                    help='Specifies Redis database destination password.')

arguments = parser.parse_args()

# Script options
script_path = "."
login_obj = {
    'email': arguments.maltiverse_email,
    'password': arguments.maltiverse_password
    }

session = requests.Session()
session.headers = {
    'content-type': 'application/json',
    'accept': 'application/json',
}

HEADERS = None

r = redis.Redis(
    host=arguments.redis_host,
    port=arguments.redis_port, 
    password=arguments.redis_password)

COUNT_IP = 0
COUNT_HOSTNAME = 0
COUNT_URL = 0
COUNT_SAMPLE = 0

# Authentication in Maltiverse service
try:
    data_login = requests.post('https://api.maltiverse.com/auth/login', json=login_obj)
    R_JSON = json.loads(data_login.text)
    if 'status' in R_JSON and R_JSON['status'] == 'success':
        if R_JSON['auth_token']:
            HEADERS = {'Authorization': 'Bearer ' + R_JSON['auth_token'] }
        else:
            print('Authentication failed')
            raise SystemExit()
    else:
        print('Authentication failed')
        raise SystemExit()

except requests.exceptions.RequestException as e: 
    raise SystemExit(e)

# Retrieving feed information
COLLECTION_URL = "https://api.maltiverse.com/collection/" + arguments.maltiverse_feed
COLL_RESP = requests.get(COLLECTION_URL, headers=HEADERS)
if COLL_RESP.status_code != 200:
    print('Feed does not exist')
    raise SystemExit()
else:
    COLL_OBJ = json.loads(COLL_RESP.text)

# Apply ranges if specified
if arguments.maltiverse_range and arguments.maltiverse_range_field:
    FEED_URL = COLLECTION_URL + "/download?range=" + arguments.maltiverse_range + "&range_field=" + arguments.maltiverse_range_field
else:
    FEED_URL = COLLECTION_URL + "/download"

# Download feed
print("Retrieving feed: " + COLL_OBJ['name'])
DATA = requests.get(FEED_URL, headers=HEADERS)

# Iterate elements in feed
for element in json.loads(DATA.text):
    # Generating description field
    first_description = True
    description_string = ""
        
    expiration_date = datetime.utcnow() - timedelta(days=arguments.maltiverse_feed_expiration_days)
    last_seen_obj = datetime.strptime(element['modification_time'], "%Y-%m-%d %H:%M:%S")
    diff = last_seen_obj - expiration_date
    diff_seconds = diff.total_seconds()

    if diff_seconds > 0:
        if element['type'] == 'ip':
            if r.set(element['ip_addr'], str(element), ex=int(diff_seconds)):
                print("Inserted: " + element['ip_addr'])
                COUNT_IP += 1
        if element['type'] == 'hostname':
            if r.set(element['hostname'], str(element), ex=int(diff_seconds)):
                print("Inserted: " + element['hostname'])
                COUNT_HOSTNAME += 1
        if element['type'] == 'url':
            if r.set(element['url'], str(element), ex=int(diff_seconds)):
                print("Inserted: " + element['url'])
                COUNT_URL += 1
        if element['type'] == 'sample':
            if r.set(element['sha256'], str(element), ex=int(diff_seconds)):
                print("Inserted: " + element['sha256'])
                COUNT_SAMPLE += 1

print("IPs Added: " + str(COUNT_IP))
print("Hostnames Added: " + str(COUNT_HOSTNAME))
print("URLs Added: " + str(COUNT_URL))
print("SHA256 Added: " + str(COUNT_SAMPLE))
print("Feed successfully processed: " + COLL_OBJ['name'])