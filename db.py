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
  db.child('channels').child(channel_id).child('preferences').update(preferences)

def add_channel(channel_id, team_id):
  db.child('channels').child(channel_id).set({'team_id': team_id})

def get_channel(channel_id):
  return db.child('channels').child(channel_id).get().val()

def get_restaurants(channel_id):
  return db.child('channels').child(channel_id).child('restaurants').get().val();

def set_restaurants(channel_id, restaurants):
  return db.child('channels').child(channel_id).child('restaurants').set(restaurants);

def set_favorite(channel_id, restaurant_id):
  return db.child('channels').child(channel_id).child('restaurant_preferences').update({restaurant_id: 1})

def set_dislike(channel_id, restaurant_id):
  return db.child('channels').child(channel_id).child('restaurant_preferences').update({restaurant_id: -1})

def get_restaurant_preferences(channel_id):
  return db.child('channels').child(channel_id).child('restaurant_preferences').get().val()