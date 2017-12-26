from __future__ import print_function
from flask import Flask, render_template, jsonify, request

import json
import requests
import random
import os
import pyrebase
from yelp_requests import refresh_business_list, yelp_request

config = {
  "apiKey": os.getenv('FIREBASE_LUNCH_API_KEY'),
  "authDomain": "lunch-spinner.firebaseapp.com",
  "databaseURL": "https://lunch-spinner.firebaseio.com/",
  "storageBucket": "lunch-spinner.appspot.com"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()


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


def is_txt_float(txt):
  try:
    float(txt)
  except Exception as e:
    return False
  else:
    return True

def is_txt_int(txt):
  try:
    int(txt)
  except Exception as e:
    return False
  else:
    return True

def is_valid_value(key, value):
  if key == 'lat' or key == 'lon':
    return is_txt_float(value)
  elif key == 'radius':
    return is_txt_int(value)
  else:
    return False

# valid txt should be in the format ex: lat=20394
def text_is_valid(txt):
  ALLOWED_PARAMS = ['lat', 'lon', 'radius']
  split_txt = txt.split('=')
  if len(split_txt) != 2:
    return False
  if split_txt[0] not in ALLOWED_PARAMS:
    return False
  if not is_valid_value(split_txt[0], split_txt[1]):
    return False

  return True


@app.route('/choice', methods=['GET', 'POST'])
def choose():
  form_data = request.form
  channel_id = form_data.get('channel_id')
  team_id = form_data.get('team_id')
  channel = db.child('channels').child(channel_id).get()

  form_text = form_data.get('text').split(' ')

  if form_text[0] == 'preferences':
    # TODO: format this in a nice way (get ordered dict out)
    return 'Your lunch-spinner preferences are %s' % (str(get_preferences(channel_id).items()))

  elif form_text[0] == 'setup':
    valid_settings = list(filter(text_is_valid, form_text))
    settings = {}
    for setting in valid_settings:
      split_setting = setting.split('=')
      settings[split_setting[0]] = split_setting[1]

    all_settings = addSettings(channel_id, settings)

    return "We've set your preference to %s \n Your settings are now: %s" % (settings, all_settings)


  if not channel.val():
    addChannel(channel_id, team_id)
    return ("It looks like you haven't used lunch-spinner before in this channel.\n" +
        "We need to set up some preferences. These preferences will be used for any lunch request in this channel.\n"
        "Preference options are: \n *Lat* (requrired) \n *Lon* (required) \n *Radius from location* (Optional: default is 900m) \n " +
        "To enter preferences, type `/lunch setup lat=23432 lon=20394 radius=500` .. etc")

  if not os.path.isfile('restaurant_data.txt'):
    refresh_business_list(API_KEY)

  restaurant = chooseRandomRestaurant(retrieve_businesses_from_file())

  return jsonify(build_slack_response(restaurant))


def get_preferences(channel_id):
  return db.child('channels').child(channel_id).child('preferences').get().val()

def set_preferences(channel_id, preferences):
  db.child("channels").child(channel_id).child('preferences').set(preferences)


def addChannel(channel_id, team_id):
  db.child('channels').child(channel_id).set({'team_id': team_id})

def addSettings(channel_id, settings):
  prev_preferences = get_preferences(channel_id)

  # merge old and new preferences
  # new takes precedence
  new_preferences = {}
  new_preferences.update(prev_preferences)
  new_preferences.update(settings)

  set_preferences(channel_id, new_preferences)
  return new_preferences




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

def build_slack_response(restaurant):
  return {
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



# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True)