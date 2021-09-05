# Maltiverse Feed Redis Connector
Connection script to integrate Maltiverse feeds into a Redis database instance

```
usage: maltiverse-redis.py [-h] --maltiverse_email MALTIVERSE_EMAIL --maltiverse_password MALTIVERSE_PASSWORD --feed MALTIVERSE_FEED
                           [--range MALTIVERSE_RANGE] [--range_field MALTIVERSE_RANGE_FIELD]
                           [--feed-expiration-days MALTIVERSE_FEED_EXPIRATION_DAYS] [--redis_host REDIS_HOST] [--redis_port REDIS_PORT]
                           [--redis_password REDIS_PASSWORD]

optional arguments:
  -h, --help            show this help message and exit
  --maltiverse_email MALTIVERSE_EMAIL
                        Specifies Maltiverse email for login. Required
  --maltiverse_password MALTIVERSE_PASSWORD
                        Specifies Maltiverse password for login. Required
  --feed MALTIVERSE_FEED
                        Specifies Maltiverse Feed ID to retrieve. Required
  --range MALTIVERSE_RANGE
                        Specifies Feed time range. Examples now-1h, now-1w, now-1M
  --range_field MALTIVERSE_RANGE_FIELD
                        Specifies the datetime field to apply filtering range ('creation_time'|'modification_time'). Default 'modification_time'
  --feed-expiration-days MALTIVERSE_FEED_EXPIRATION_DAYS
                        Specifies the default expiration time in days for the indicators of the selected collection. Default 30 days
  --redis_host REDIS_HOST
                        Specifies Redis database destination hostname. Default localhost
  --redis_port REDIS_PORT
                        Specifies Redis database destination hostname port. Default 6379
  --redis_password REDIS_PASSWORD
                        Specifies Redis database destination password.
```

## Example 1 - Retrieve "Malicious IP" feed, full download
maltiverse-redis.py --maltiverse_email EMAIL --maltiverse_password PASSWORD --feed uYxZknEB8jmkCY9eQoUJ 

## Example 2 - Retrieve "Malicious IP" feed, last hour download
maltiverse-redis.py --maltiverse_email EMAIL --maltiverse_password PASSWORD --feed uYxZknEB8jmkCY9eQoUJ --range now-1h

