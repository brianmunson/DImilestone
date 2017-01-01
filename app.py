from flask import Flask, render_template, request, redirect
import requests
import os
import tweepy as ty
import yweather
import pandas as pd
import datetime
import bokeh
from bokeh.charts import Bar, output_file, show
from bokeh.embed import components
import geocoder
# import dotenv # for getting environmental variables from .environmental

# following code seems to work for using environmental variables to get API Keys:
# from dotenv import load_dotenv, find_dotenv
# load_dotenv(find_dotenv())
# os.environ.get("TWITTER_CONSUMER") will return the twitter consumer key in the
# .env file. This really doesn't seem any better than my openAPI_Key function:
# the .env still must go in .gitignore.

###### for loading secret API key
# old version for file with single line containing key
# def openAPI_Key(key_file):
#     f = open(key_file, 'r')
#     api_key = f.read().rstrip()
#     f.close()
#     return(api_key)
# another version with one file for all keys
# unused in favor of environmental variables. See settings.py
def openAPI_Key(key_file, name):
    key_file_df = pd.DataFrame.from_csv(key_file, index_col = None, sep = ', ')
    # will give a warning that it will use python engine instead of c engine
    # but i imagine this can be safely ignored. according to warning it can be
    # avoided with enginer='python', but this call does not work in the .from_csv
    # method used above.
    if key_file_df[key_file_df['Name'] == name].empty:
        print("Name not found.")
    else:
        return(key_file_df[ key_file_df['Name'] == name ]['Key'].reset_index(drop = True)[0])
        # returns the key as a string. need to reset index of resulting series
        # to zero otherwise will return an error because subsetting preserves
        # the given index.

###### credentials and such
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())
consumer_key = os.environ.get("TW_CONSUMER")
consumer_secret = os.environ.get("TW_CONSUMER_SECRET")
access_token = os.environ.get("TW_ACCESS")
access_token_secret = os.environ.get("TW_ACCESS_SECRET")

###### yweather get WOEID function. No API keys required.

def get_WOEID(location):
    client = yweather.Client()
    return(client.fetch_woeid(location))

###### Twitter trends based on location
# basic request we're after:
# GET https://api.twitter.com/1.1/trends/place.json?id=XXXX
# where XXXX = output of woeid fetch call above as an integer.

def get_Twitter_trends(location, api_key_dict = None):
    # for use with openAPI_Key function and dictionary of keys; old
    # consumer_key = api_key_dict["Twitter Consumer"]
    # consumer_secret = api_key_dict["Twitter Consumer Secret"]
    # access_token = api_key_dict["Twitter Access Token"]
    # access_token_secret = api_key_dict["Twitter Access Token Secret"]
    auth = ty.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = ty.API(auth)
    available = api.trends_available()
    if get_WOEID(location):
        if get_WOEID(location) in [item['woeid'] for item in available]:
            return(api.trends_place(int(get_WOEID(location))), location)
        else:
            g = geocoder.google(location)
            if g.latlng:
                closest_trends = api.trends_closest(g.latlng[0], g.latlng[1])
                return(api.trends_place(closest_trends[0]['woeid']), closest_trends[0]['name'])
            else:
                return(api.trends_place(1), "worldwide (invalid location entered)")
    else:
        return(api.trends_place(1), "worldwide (invalid location entered)")

    # if get_WOEID(location):
    #     return(api.trends_place(int(get_WOEID(location))), location)
    # else:
    #     return(api.trends_place(1), "worldwide (invalid location entered)")

    #
    # if get_WOEID(location) in [dict['woeid'] for dict in available]:
    #     return(api.trends_place(int(get_WOEID(location))), location)
    # elif get_WOEID(location):
    #     g = geocoder.google(location)
    #     closest_trends = api.trends_closest(g.latlng[0], g.latlng[1])
    #     return(api.trends_place(closest_trends[0]['woeid'], closest_trends[0]['name']))
    #     # get nearest trends. not crazy about two api calls to get it.
    #     # would be nice if easy way to convert woeid to lat/long
    # else:
    #     return(api.trends_place(1), "location invalid, showing Worldwide")

###### Process Twitter trends output. argument is [0] of output of get_Twitter_trends
# function defined above
# it is possible to have a valid WOEID but for the trends not to exist (maybe
# Twitter consider the location too small or something. A better way to go might
# be to do a "closest" trends instead.

def trends_to_df(trends):
    when_trends = trends[0]['as_of']
    when_datetime = datetime.datetime.strptime(when_trends, "%Y-%m-%dT%H:%M:%SZ")
    when = when_datetime.ctime() + " UTC"
    where = trends[0]['locations'][0]['name']
    # returns date in nice format as string
    trends_name_vol_df = pd.DataFrame(trends[0]['trends'],
    columns = ['name', 'tweet_volume' ])
    # only take the name of the trend and its tweet volume
    return( { "when" : when, "where" : where, "trends" : trends_name_vol_df.dropna() } )
    # drops NaN values for volume; only going to graph those with volume counts


###### Bokeh bar plot from pandas trends dataframe
# trending is data frame output of trends_to_df function above
# need to have returns above also give the place and the when.

def bar_plot_trends(trending):
    p = Bar(trending['trends'], 'name', values = 'tweet_volume',
    title = 'Tweet volume of trends for ' + trending['where'] + ' as of ' + trending['when'],
    xlabel = 'Topic', ylabel = 'Volume')
    script, div = components(p)
    return(script, div)
    # output_file("bargraph.html") # debugging in interpreter
    # show(p) # debugging in interpreter

app = Flask(__name__)

# app.vars = {}
# old, for use with openAPI_Key function above:
# keys_list = ["Twitter Consumer", "Twitter Consumer Secret",
# "Twitter Access Token", "Twitter Access Token Secret"]
# for name in keys_list:
#     app.vars[name] = openAPI_Key("API_Key", name)

@app.route('/')
def main():
  return(redirect('/index'))

@app.route('/index', methods = ['GET', 'POST'])
def index():
  return(render_template('index.html'))

@app.route('/bargraph', methods = ['GET', 'POST'])
def bargraph():
    if request.method == "POST":
        location = request.form['location']
        trends, location = get_Twitter_trends(location)
        df = trends_to_df(trends)
        script, div = bar_plot_trends(df)
        return(render_template('bargraph.html', location = location,
        script = script, div = div))
    else:
        return(render_template('index.html'))


if __name__ == '__main__':
    port=int(os.environ.get("PORT", 5000)) # local
    app.run(port=port, host='0.0.0.0') # local
    # app.run(port=33507) # Heroku
