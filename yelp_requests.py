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

import urllib

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

def yelp_request(host, path, api_key, url_params=None):
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


    # TODO: make first request, then see how many yelp returns then make that many requests
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

      l = yelp_request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)
      businesses.extend(l.get('businesses'))

    if leftovers:
      url_params['limit'] = leftovers
      url_params['offset'] = full_requests * 50 + 1
      businesses.extend(yelp_request(API_HOST, SEARCH_PATH, api_key, url_params=url_params).get('businesses'))

    with open('restaurant_data.txt', 'w') as outfile:
      json.dump(businesses, outfile)




# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True)