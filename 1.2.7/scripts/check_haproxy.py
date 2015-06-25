#!/usr/bin/env python
import urlparse # Allows you to verify the validity of a URL
import requests # Require the requests API
import argparse # Required to parse the first arguement

argparser = argparse.ArgumentParser(description='Given a URL, determine if that URL is returning a static code 200')
argparser.add_argument('url',
                       action='store',
                       nargs=1,
                       help='The provided URL to test against')

args = argparser.parse_args()


# Check if the URL looks valid
parsed = urlparse.urlparse(args.url[0],'http') # Parse URL with default of http

# Try the request
try:
    request = requests.get(urlparse.urlunparse(parsed))
except:
    exit(1) # The request failed, this could mean the provided URL is invalid
    
if not request.status_code == 200:
    exit(1) # The request failed as the request did not return a 200

exit(0) # The request succeeded