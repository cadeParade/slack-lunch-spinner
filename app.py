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
from flask import jsonify, request
from yelp_requests import refresh_business_list, yelp_request
import pyrebase

config = {
  "apiKey": os.getenv('FIREBASE_LUNCH_API_KEY'),
  "authDomain": "lunch-spinner.firebaseapp.com",
  "databaseURL": "https://lunch-spinner.firebaseio.com/",
  "storageBucket": "lunch-spinner.appspot.com"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()
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


# user sends request
# if so, check if channel exists AND has preferences
# if no, add channel to db and prompt them to set preferences
# if yes, do the choice with channel's preferences


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
  form_data = request.form
  channel_id = form_data.get('channel_id')
  team_id = form_data.get('team_id')
  channel = db.child('channels').child(channel_id).get()

  if not channel.val():
    addChannel(channel_id, team_id)
    print("IN IF", channel_id)
    return jsonify('It looks like you haven\'t used lunch-spinner before in this channel.' +
      'Do some things to set up lunch-spinner for this channel')
    # go to prompt to set preferences


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

def addChannel(channel_id, team_id):
  db.child("channels").child(channel_id).set({'team_id': team_id})


def chooseRandomRestaurant(businesses):
  return random.choice(businesses)


def retrieve_close_businesses_from_file():
    json_data=open('close_restaurants.txt').read()
    data = json.loads(json_data)
    return data


def retrieve_businesses_from_file():
    json_data=open('restaurant_data.txt').read()
    data = json.loads(json_data)
    return data



# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True)