import os
import pyrebase

FIREBASE_CONFIG = {
  "apiKey": os.getenv('FIREBASE_LUNCH_API_KEY'),
  "authDomain": "lunch-spinner.firebaseapp.com",
  "databaseURL": "https://lunch-spinner.firebaseio.com/",
  "storageBucket": "lunch-spinner.appspot.com"
}

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
db = firebase.database()


def get_preferences(channel_id):
  return db.child('channels').child(channel_id).child('preferences').get().val()

def set_preferences(channel_id, preferences):
  db.child("channels").child(channel_id).child('preferences').set(preferences)

def add_channel(channel_id, team_id):
  db.child('channels').child(channel_id).set({'team_id': team_id})

def get_channel(channel_id):
  return db.child('channels').child(channel_id).get().val()

def get_restaurants(channel_id):
  return db.child('channels').child(channel_id).child('restaurants').get().val();

def set_restaurants(channel_id, restaurants):
  return db.child('channels').child(channel_id).child('restaurants').set(restaurants);


# TODO name this better
def add_settings(channel_id, settings):
  prev_preferences = get_preferences(channel_id)

  # merge old and new preferences
  # new takes precedence
  new_preferences = {}
  new_preferences.update(prev_preferences)
  new_preferences.update(settings)

  set_preferences(channel_id, new_preferences)
  return new_preferences


