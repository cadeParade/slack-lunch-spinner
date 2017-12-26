from __future__ import print_function
from flask import Flask, render_template, jsonify, request

import json
import requests
import random
import os
from yelp_requests import refresh_business_list, yelp_request
from lunch_settings import get_valid_settings
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
  channel_id = form_data.get('channel_id')
  team_id = form_data.get('team_id')

  form_text = form_data.get('text')
  if form_text:
    form_text = form_text.split(' ')

    if form_text[0] == 'preferences':
      # TODO: format this in a nice way (get ordered dict out)
      return 'Your lunch-spinner preferences are %s' % (str(db.get_preferences(channel_id).items()))

    elif form_text[0] == 'setup':
      new_valid_settings = get_valid_settings(form_text)
      all_settings = db.add_settings(channel_id, new_valid_settings)

      return "We've set your preference to %s \n Your settings are now: %s" % (new_valid_settings, all_settings)

  # TODO: make this work with "spin again" -- channel id does not come through the same way in second response :/
  channel = db.get_channel(channel_id)

  if not channel:
    db.add_channel(channel_id, team_id)
    return ("It looks like you haven't used lunch-spinner before in this channel.\n" +
        "We need to set up some preferences. These preferences will be used for any lunch request in this channel.\n"
        "Preference options are: \n *Lat* (requrired) \n *Lon* (required) \n *Radius from location* (Optional: default is 900m) \n " +
        "To enter preferences, type `/lunch setup lat=23432 lon=20394 radius=500` .. etc")

  if not os.path.isfile('restaurant_data.txt'):
    refresh_business_list()

  restaurant = chooseRandomRestaurant(retrieve_businesses_from_file())

  return jsonify(build_slack_response(restaurant))



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