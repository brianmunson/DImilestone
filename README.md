# Data Incubator Milestone project: Twitter Trends

This project allows the user to enter a location in the world and returns a
bar graph of trends and their tweet volume. In an invalid location is specified,
worldwide trends will be shown instead.

This project is intended to help you tie together some important concepts and
technologies from the 12-day course, including Git, Flask, JSON, Pandas,
Requests, Heroku, and Bokeh for visualization.

## index.html

A page for entering a location. Invalid locations other than the empty location
will return worldwide trends.

## bargraph.html

A plot displaying trends in the user-specified location.

## app.py

The app takes a location, asks Yahoo weather for the WOEID of that location,
asks Twitter for trends from that location, the result of which is read into
pandas to form an appropriate dataframe and then Bokeh is used to create a bar
plot. The location and plot are then fed to bargraph.html and displayed.
The Twitter API keys are kept hidden.
