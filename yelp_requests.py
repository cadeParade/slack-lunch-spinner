"""
Yelp Fusion API code sample.
This program demonstrates the capability of the Yelp Fusion API
by using the Search API to query for businesses by a search term and location,
and the Business API to query additional information about the top result
from the search query.
Please refer to http://www.yelp.com/developers/v3/documentation for the API
documentation.
This program requires the Python requests library, which you can install via:
`pip install -r requirements.txt`.
Sample usage of the program:
`python sample.py --term="bars" --location="San Francisco, CA"`
"""

import os
import urllib
import requests
import json

# This client code can run on Python 2.x or 3.x.  Your imports can be
# simpler if you only need one of those.
try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode


# Yelp Fusion no longer uses OAuth as of December 7, 2017.
# You no longer need to provide Client ID to fetch Data
# It now uses private keys to authenticate requests (API Key)
# You can find it on
# https://www.yelp.com/developers/v3/manage_app
YELP_API_KEY = os.getenv('YELP_LUNCH_SPINNER_API_KEY')


# API constants, you shouldn't have to change these.
YELP_API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.


# Defaults for our simple example.
DEFAULT_TERM = 'dinner'
DEFAULT_LOCATION = 'San Francisco, CA'
SEARCH_LIMIT = 50



def yelp_request(host, path, url_params=None):
    """Given your API_KEY, send a GET request to the API.
    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        API_KEY (str): Your API Key.
        url_params (dict): An optional set of query parameters in the request.
    Returns:
        dict: The JSON response from the request.
    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % YELP_API_KEY,
    }

    print(u'Querying {0} ...'.format(url))

    response = requests.request('GET', url, headers=headers, params=url_params)
    print (response.status_code)
    return response.json()


def refresh_business_list(preferences):
    """Query the Search API by a search term and location.
    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.
    Returns:
        dict: The JSON response from the request.
    """


    # TODO: make first request, then see how many yelp returns then make that many requests
    url_params = {
      'term': 'lunch',
      'price': '1,2',
      'limit': 1,
      'latitude': preferences['lat'],
      'longitude': preferences['lon'],
      'radius': preferences.get('radius') or 800,
    }

    businesses = []

    initial_query = yelp_request(YELP_API_HOST, SEARCH_PATH, url_params=url_params)

    # don't ask for more than 1000 businesses, even if there are more than 1000
    num_businesses = 1000 if initial_query['total'] < 1000 else initial_query['total']


    x = divmod(num_businesses, SEARCH_LIMIT)
    full_requests = x[0]
    leftovers = x[1]


    url_params['limit'] = SEARCH_LIMIT
    for n in range(0, full_requests):
      if n == 0:
        url_params['offset'] = 0
      else:
        url_params['offset'] = n * SEARCH_LIMIT

      l = yelp_request(YELP_API_HOST, SEARCH_PATH, url_params=url_params)
      businesses.extend(l.get('businesses'))

    if leftovers:
      url_params['offset'] = full_requests * SEARCH_LIMIT
      businesses.extend(yelp_request(YELP_API_HOST, SEARCH_PATH, url_params=url_params).get('businesses'))


    business_dict = {}
    for business in businesses:
      business_dict[business['id']] = business

    return business_dict
