from sys import modules

import niquests
import requests
from niquests.packages import urllib3

# the mock utility 'response' only works with 'requests'
modules["requests"] = niquests
modules["requests.adapters"] = niquests.adapters
modules["requests.exceptions"] = niquests.exceptions
modules["requests.compat"] = requests.compat
modules["requests.packages.urllib3"] = urllib3