from __future__ import print_function
from flask import Flask, render_template, jsonify, request

import json
import random
import os
from yelp_requests import refresh_business_list, yelp_request
from lunch_settings import parse_valid_settings
import db

# user sends request
# if so, check if channel exists AND has preferences
# if no, add channel to db and prompt them to set preferences
# if yes, do the choice with channel's preferences


# create the application object
app = Flask(__name__)

@app.route('/choice', methods=['GET', 'POST'])
def choose():
  form_data = request.form
  # # TODO take out this string literal
  # channel_id = 'C8KRF1KAB'
  channel_id = form_data.get('channel_id') or json.loads(form_data.get('payload'))['channel']['id']
  channel = db.get_channel(channel_id)

  if not channel:
    return add_channel(channel_id, form_data.get('team_id'))

  args = form_data.get('text')
  if args:
    return parse_args(channel_id, args)

  if not db.get_restaurants(channel_id):
    get_restaurants(channel_id)

  restaurant = choose_random_restaurant(db.get_restaurants(channel_id))

  return jsonify(build_slack_response(restaurant))


def parse_args(channel_id, args):
  args = args.split(' ')

  if args[0] == 'preferences':
    # TODO: format this in a nice way (get ordered dict out)
    return 'Your lunch-spinner preferences are %s' % (str(db.get_preferences(channel_id).items()))

  elif args[0] == 'setup':
    new_valid_settings = parse_valid_settings(args)
    all_settings = db.add_settings(channel_id, new_valid_settings)

    return "We've set your preference to %s \n Your settings are now: %s" % (new_valid_settings, all_settings)


def add_channel(channel_id, team_id):
  db.add_channel(channel_id, team_id)
  return ("It looks like you haven't used lunch-spinner before in this channel.\n" +
      "We need to set up some preferences. These preferences will be used for any lunch request in this channel.\n"
      "Preference options are: \n *Lat* (requrired) \n *Lon* (required) \n *Radius from location* (Optional: default is 900m) \n " +
      "To enter preferences, type `/lunch setup lat=23432 lon=20394 radius=500` ... etc")

def get_restaurants(channel_id):
  businesses = refresh_business_list(db.get_preferences(channel_id))
  db.set_restaurants(channel_id, businesses)

def choose_random_restaurant(businesses):
  restaurant_id = random.choice(list(dict(businesses).keys()))
  return businesses[restaurant_id]


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



if __name__ == '__main__':
    app.run(debug=True)