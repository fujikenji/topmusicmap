### Uncomment line 24/line 85 when you get API keys and put it into lastfm_key.py/mapquest_key.py ###

import urllib.request, urllib.error, urllib.parse, json, lastfm_key, logging, mapquest_key

# Utility functions from previous hw's for testing/safe_get
def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

def safe_get(url):
    try:
        return urllib.request.urlopen(url)
    except urllib.error.HTTPError as e:
        print("The server couldn't fulfill the request." )
        print("Error code: ", e.code)
    except urllib.error.URLError as e:
        print("We failed to reach a server")
        print("Reason: ", e.reason)
    return None

# Repurposing FlickrREST from HW 6 for last.fm/mapquest urls
def geturl(baseurl = 'http://ws.audioscrobbler.com/2.0',
    method = 'geo.gettopartists',
    mapquest = False,
    api_key = lastfm_key.key,
    format = 'json',
    params={},
    ):
    if mapquest == False:
        params['method'] = method
        params['api_key'] = api_key
    else:
        params['key'] = api_key
    params['format'] = format
    url = baseurl + "?" + urllib.parse.urlencode(params)
    return url

def apirequest(url):
    # make a request with the url and necessary headers
    # User-Agent
    headers = {"User-Agent": "fujikenji (fujikenji22@gmail.com)"}
    req = urllib.request.Request(url,headers=headers)
    # pass that request to safe_get
    result = safe_get(req)
    if result is not None:
        return json.load(result)

class Artist():
    def __init__(self, artistinfo):
        self.name = artistinfo['name']
        self.listeners = artistinfo['listeners']
        self.url = artistinfo['url']

class Track():
    def __init__(self, trackinfo):
        self.name = trackinfo['name']
        self.listeners = trackinfo['listeners']
        self.url = trackinfo['url']
        self.artist = trackinfo['artist']['name']
        self.artisturl = trackinfo['artist']['url']

# Makes a dictionary of all the track/artist objects for each user-provided country
def musicobjects(infotype, countrylist, resultsnum):
    infodict = {}

    if 'toptracks' in infotype:
        for country in countrylist:
            tracksinfo = apirequest(geturl(method='geo.gettoptracks', params={'limit': resultsnum, 'country': country.strip()}))
            tracks = [Track(info) for info in tracksinfo['tracks']['track']]
            infodict[country.strip()] = tracks

    elif 'topartists' in infotype:
        for country in countrylist:
            artistinfo = apirequest(geturl(params={'limit': resultsnum, 'country':country.strip()}))
            print(pretty(artistinfo))
            artists = [Artist(info) for info in artistinfo['topartists']['artist']]
            infodict[country.strip()] = artists

    return infodict

# Returns a dictionary with country names as keys and lat/long tuples for values
def getlatlong(countrylist):
    latlongdict = {}
    for country in countrylist:
        url = geturl(baseurl='http://www.mapquestapi.com/geocoding/v1/address',
                     # api_key=mapquest_key.key,
                     mapquest = True,
                     params={'location':country})
        countryjson = apirequest(url)
        latlongdict[country] = (countryjson['results'][0]['locations'][0]['latLng']['lat'], countryjson['results'][0]['locations'][0]['latLng']['lng'])
    return latlongdict

from flask import Flask, render_template, request
app = Flask(__name__)

@app.route("/")
def main_handler():
    app.logger.info("In MainHandler")
    getlatlong(['Japan', 'Nigeria'])
    return render_template('topmusictemplate.html')

@app.route("/locationget")
def locationget_handler():
    resultvalues = {'tracks':True, 'artists':True}

    # Getting country name(s) from the form
    country = request.args.get('country')
    if "," not in country:
        resultvalues['country'] = [country]
    else:
        countries = country.split(',')
        resultvalues['country'] = [country.strip() for country in countries]

    resultvalues['coordinates'] = getlatlong(resultvalues['country'])

    # If user chose artists/tracks/both
    infotype = request.args.getlist('infotype')

    if country != "" and infotype != []:
        resultsnum = request.args.get('results', 5)
        resultvalues['resultsnum'] = resultsnum

        if len(infotype) > 1:
            resultvalues['tracksorartists'] = "Tracks/Artists"
            resultvalues['tracksinfo'] = musicobjects(infotype, resultvalues['country'], resultsnum)
            resultvalues['artistsinfo'] = musicobjects(infotype, resultvalues['country'], resultsnum)

        elif 'toptracks' in infotype:
            resultvalues['tracksorartists'] = "Tracks"
            resultvalues['artists'] = False
            resultvalues['tracksinfo'] = musicobjects(infotype, resultvalues['country'], resultsnum)

        elif 'topartists' in infotype:
            resultvalues['tracksorartists'] = 'Artists'
            resultvalues['tracks'] = False
            resultvalues['artistsinfo'] = musicobjects(infotype, resultvalues['country'], resultsnum)

    print(resultvalues)
    return render_template('topmusicresults.html', results=resultvalues)

if __name__ == '__main__':
    app.run(host="localhost", port=8080, debug=True)