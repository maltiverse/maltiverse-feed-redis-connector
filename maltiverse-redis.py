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
                    help='Specifies Feed time range. Examples now-1h, now-1w, now-1M')
parser.add_argument('--range_field', dest='maltiverse_range_field', default="modification_time",
                    help="Specifies the datetime field to apply filtering range ('creation_time'|'modification_time'). Default 'modification_time'")
parser.add_argument('--feed-expiration-days', dest='maltiverse_feed_expiration_days', default=30,
                    help="Specifies the default expiration time in days for the indicators of the selected collection. Default '30'")
parser.add_argument('--redis_host', dest='redis_host', default="localhost",
                    help="Specifies Redis database destination hostname. Default 'localhost'")
parser.add_argument('--redis_port', dest='redis_port', default=6379,
                    help="Specifies Redis database destination hostname port. Default '6379'")
parser.add_argument('--redis_password', dest='redis_password', default=None,
                    help='Specifies Redis database destination password.')
parser.add_argument('--redis_database_ipv4', dest='redis_database_ipv4', default=0,
                    help='Specifies Redis database index for IPv4.')
parser.add_argument('--redis_database_hostname', dest='redis_database_hostname', default=0,
                    help='Specifies Redis database index for Hostnames.')
parser.add_argument('--redis_database_url', dest='redis_database_url', default=0,
                    help='Specifies Redis database index for URL.')
parser.add_argument('--redis_database_sample', dest='redis_database_sample', default=0,
                    help='Specifies Redis database index for Samples.')
parser.add_argument('--verbose', dest='verbose', action="store_true", default=False,
                    help='Shows extra information during ingestion')
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

r_ipv4 = redis.Redis(
    host=arguments.redis_host,
    port=arguments.redis_port, 
    password=arguments.redis_password,
    db=arguments.redis_database_ipv4)

r_hostname = redis.Redis(
    host=arguments.redis_host,
    port=arguments.redis_port, 
    password=arguments.redis_password,
    db=arguments.redis_database_hostname)

r_url = redis.Redis(
    host=arguments.redis_host,
    port=arguments.redis_port, 
    password=arguments.redis_password,
    db=arguments.redis_database_url)

r_sample = redis.Redis(
    host=arguments.redis_host,
    port=arguments.redis_port, 
    password=arguments.redis_password,
    db=arguments.redis_database_sample)

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
            if r_ipv4.set(element['ip_addr'], str(element), ex=int(diff_seconds)):
                COUNT_IP += 1
                if arguments.verbose:
                    print("Inserted: " + element['ip_addr'])

        if element['type'] == 'hostname':
            if r_hostname.set(element['hostname'], str(element), ex=int(diff_seconds)):
                COUNT_URL += 1
                if arguments.verbose:
                    print("Inserted: " + element['hostname'])

        if element['type'] == 'url':
            if r_url.set(element['url'], str(element), ex=int(diff_seconds)):
                COUNT_URL += 1
                if arguments.verbose:
                    print("Inserted: " + element['url'])

        if element['type'] == 'sample':
            if r_sample.set(element['sha256'], str(element), ex=int(diff_seconds)):
                COUNT_SAMPLE += 1
                if arguments.verbose:
                    print("Inserted: " + element['sha256'])

print("IPs Inserted        : " + str(COUNT_IP))
print("Hostnames Inserted  : " + str(COUNT_HOSTNAME))
print("URLs Inserted       : " + str(COUNT_URL))
print("SHA256 Inserted     : " + str(COUNT_SAMPLE))
print("PROCESSED           : " + COLL_OBJ['name'])
print("###########################################")
print("")