# import the Flask class from the flask module

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
from __future__ import print_function
from flask import Flask, render_template

import argparse
import json
import pprint
import requests
import sys
import urllib
import random
import os
from flask import jsonify

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
API_KEY = os.getenv('YELP_LUNCH_SPINNER_API_KEY')


# API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.


# Defaults for our simple example.
DEFAULT_TERM = 'dinner'
DEFAULT_LOCATION = 'San Francisco, CA'
SEARCH_LIMIT = 50



# create the application object
app = Flask(__name__)

# use decorators to link the function to a url
@app.route('/')
def home():
    if not os.path.isfile('restaurant_data.txt'):
      refresh_business_list(API_KEY)

    businesses = retrieve_businesses_from_file()
    return render_template('welcome.html', choice=chooseRandomRestaurant(businesses), data=businesses)

@app.route('/choice', methods=['GET', 'POST'])
def choose():
  if not os.path.isfile('restaurant_data.txt'):
    refresh_business_list(API_KEY)

  restaurant = chooseRandomRestaurant(retrieve_businesses_from_file())
  ret = {
    'attachments': [{
      'fallback': restaurant.get('name'),
      'color': '#9500c7',
      'author_name': 'Lunch Spinner',
      'title': restaurant.get('name'),
      'title_link': restaurant.get('url'),
      'image_url': restaurant.get('image_url'),
      'fields': [
        {
          'title': 'Categories',
          'value': ', '.join([category.get('title') for category in restaurant.get('categories')]),
          'short': 'true',
        },
        {
          'title': 'Address',
          'value': restaurant.get('location').get('address1'),
          'short': 'true',
        },
        {
          'title': 'Rating',
          'value': restaurant.get('rating'),
          'short': 'true',
        },
        {
          'title': 'Price',
          'value': restaurant.get('price'),
          'short': 'true',
        },
      ],
      'actions': [
        {
          "name": "repeat",
          "text": "Spin again",
          "type": "button",
          "value": "repeat",
        }
      ],
      'callback_id': 'lunch-spinner',
      'replace_original': 'true'
    }]
  }
  return jsonify(ret)

# @app.route('/test', methods=['POST'])
# def test():
#   return jsonify(
#     {
#     "attachments": [
#         {
#             "fallback": "Required plain-text summary of the attachment.",
#             "color": "#36a64f",
#             "pretext": "Optional text that appears above the attachment block",
#             "author_name": "Bobby Tables",
#             "author_link": "http://flickr.com/bobby/",
#             "author_icon": "http://flickr.com/icons/bobby.jpg",
#             "title": "Slack API Documentation",
#             "title_link": "https://api.slack.com/",
#             "text": "Optional text that appears within the attachment",
#             "fields": [
#                 {
#                     "title": "Priority",
#                     "value": "High",
#                     "short": false
#                 }
#             ],
#             "image_url": "http://my-website.com/path/to/image.jpg",
#             "thumb_url": "http://example.com/path/to/thumb.png",
#             "footer": "Slack API",
#             "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
#             "ts": 123456789
#         }
#     ]
# }
#   )

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')  # render a template


def chooseRandomRestaurant(businesses):
  return random.choice(businesses)

def request(host, path, api_key, url_params=None):
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
        'Authorization': 'Bearer %s' % api_key,
    }

    print(u'Querying {0} ...'.format(url))

    response = requests.request('GET', url, headers=headers, params=url_params)
    print (response.status_code)
    return response.json()

def retrieve_close_businesses_from_file():
    json_data=open('close_restaurants.txt').read()
    data = json.loads(json_data)
    return data


def retrieve_businesses_from_file():
    json_data=open('restaurant_data.txt').read()
    data = json.loads(json_data)
    return data


def refresh_business_list(api_key, term='lunch', lat=37.788440, lon=-122.399855, distance=900, price='1,2', num_businesses=200):
# def search(api_key):
# def search(api_key, term, location):
    """Query the Search API by a search term and location.
    Args:
        term (str): The search term passed to the API.
        location (str): The search location passed to the API.
    Returns:
        dict: The JSON response from the request.
    """

    url_params = {
        'term': term.replace(' ', '+'),
        'latitude': lat,
        'longitude': lon,
        'limit': SEARCH_LIMIT,
        'radius': distance,
        'price': price
    }

    businesses = []

    x = divmod(num_businesses, 50)
    full_requests = x[0]
    leftovers = x[1]

    for n in range(0, full_requests):
      if n == 0:
        url_params['offset'] = 0
      else:
        url_params['offset'] = n * 50 + 1

      l = request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)
      businesses.extend(l.get('businesses'))

    if leftovers:
      url_params['limit'] = leftovers
      url_params['offset'] = full_requests * 50 + 1
      businesses.extend(request(API_HOST, SEARCH_PATH, api_key, url_params=url_params).get('businesses'))

    with open('restaurant_data.txt', 'w') as outfile:
      json.dump(businesses, outfile)




# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True)