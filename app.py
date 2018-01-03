from __future__ import print_function
from flask import Flask, render_template, jsonify, request

import json
import random
import os
from yelp_requests import refresh_business_list, yelp_request
from lunch_settings import parse_valid_settings
import db

app = Flask(__name__)

FAVORITE_ACTION_NAME = 'favorite'
DISLIKE_ACTION_NAME = 'blacklist'

@app.route('/choice', methods=['GET', 'POST'])
def choose():
  form_data = request.form
  channel_id = form_data.get('channel_id') or json.loads(form_data.get('payload'))['channel']['id']
  channel = db.get_channel(channel_id)


  if not channel:
    return add_channel(channel_id, form_data.get('team_id'))

  args = form_data.get('text')
  if args:
    return parse_args(channel_id, args)

  if is_favorite_action(form_data):
    restaurant_id = get_restaurant_id_from_payload(form_data)
    db.set_favorite(channel_id, restaurant_id)
    return "Ok, %s will come up more often in the future" % (restaurant_id)
  elif is_dislike_action(form_data):
    restaurant_id = get_restaurant_id_from_payload(form_data)
    db.set_dislike(channel_id, restaurant_id)
    return "Ok, %s will not come up again" % (restaurant_id)


  # TODO: load restaurants in a way that user doesn't get timeout for first query
  if not db.get_restaurants(channel_id):
    get_restaurants(channel_id)

  businesses = db.get_restaurants(channel_id)
  filtered_restaurant_ids = filter_and_enrich_business_list(channel_id, businesses)
  restaurant_id = choose_random_restaurant_id(filtered_restaurant_ids)
  restaurant = businesses.get(restaurant_id)

  return jsonify(build_slack_response(restaurant))


def filter_and_enrich_business_list(channel_id, businesses):
  restaurant_preferences = db.get_restaurant_preferences(channel_id) or {}
  enriched_restaurant_ids = []
  for k,v in restaurant_preferences.items():
    if v == -1:
      businesses.pop(k, None)
    elif v == 1:
      enriched_restaurant_ids.extend([k] * 5)

  # import pdb;pdb.set_trace()
  enriched_restaurant_ids.extend(list(dict(businesses).keys()))

  return enriched_restaurant_ids


def get_restaurant_id_from_payload(form_data):
  return json.loads(form_data.get('payload'))['actions'][0]['value']

def add_favorite(channel_id, restaurant_id):
  restaurant_id = get_restaurant_id_from_payload(form_data)
  db.set_favorite(channel_id, restaurant_id)

def add_dislike(channel_id, restaurant_id):
  restaurant_id = get_restaurant_id_from_payload(form_data)
  db.set_dislike(channel_id, restaurant_id)


def is_favorite_action(form_data):
  return (
    form_data.get('payload') and
    json.loads(form_data.get('payload'))['actions'][0]['name'] == FAVORITE_ACTION_NAME
  )

def is_dislike_action(form_data):
  return (
    form_data.get('payload') and
    json.loads(form_data.get('payload'))['actions'][0]['name'] == DISLIKE_ACTION_NAME
  )

def parse_args(channel_id, args):
  args = args.split(' ')

  if args[0] == 'preferences':
    # TODO: format this in a nice way (get ordered dict out)
    return 'Your lunch-spinner preferences are %s' % (str(db.get_preferences(channel_id).items()))

  elif args[0] == 'setup':
    new_valid_settings = parse_valid_settings(args)
    all_settings = db.set_preferences(channel_id, new_valid_settings)

    # TODO: reload restaurants upon settings change
    # get_restaurants(channel_id)

    return "We've set your preference to %s \n Your settings are now: %s" % (new_valid_settings, db.get_preferences(channel_id))


def add_channel(channel_id, team_id):
  db.add_channel(channel_id, team_id)
  return (
    "It looks like you haven't used lunch-spinner before in this channel.\n" +
    "Type `/lunch setup lat=23432 lon=20394 radius=500` ... etc to set up this channel" +
    "These preferences will be used for any lunch request in this channel.\n"
    "Preference options are: \n *Lat* (requrired) \n *Lon* (required) \n *Radius from location* (Optional: default is 900m) \n "
  )

def get_restaurants(channel_id):
  businesses = refresh_business_list(db.get_preferences(channel_id))
  db.set_restaurants(channel_id, businesses)

def choose_random_restaurant_id(business_ids):
  return random.choice(business_ids)


def build_slack_response(restaurant):
  return {
    "response_type": "in_channel",
    'attachments': [{
      'fallback': restaurant.get('name'),
      'color': '#9500c7',
      'author_name': 'Lunch Spinner',
      'title': restaurant.get('name'),
      'title_link': restaurant.get('url'),
      'image_url': restaurant.get('image_url'),
      'restaurant_id': restaurant.get('id'),
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
        },
        {
          "name": FAVORITE_ACTION_NAME,
          "text": "LOVE!!!",
          "type": "button",
          "value": restaurant.get('id')
        },
        {
          "name": DISLIKE_ACTION_NAME,
          "text": "hate :( :( ",
          "type": "button",
          "value": restaurant.get('id')
        },
      ],
      'callback_id': 'lunch-spinner',
      'replace_original': 'true'
    }]
  }



if __name__ == '__main__':
    app.run(debug=True)