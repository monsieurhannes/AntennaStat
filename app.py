import os
import sqlite3
import pandas as pd

from jupyter_dash import JupyterDash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
import plotly.express as px

from tkinter import filedialog
from tkinter import *

root = Tk()
root.filename =  filedialog.askopenfilename(title = "Select file",filetypes = (("database files","*.db"),("all files","*.*")))
print (root.filename)


con = sqlite3.connect(os.path.join(root.filename))

# Read tables
FeedMedia = pd.read_sql_query("SELECT * from FeedMedia", con)
FeedItems = pd.read_sql_query("SELECT * from FeedItems", con)
Feeds = pd.read_sql_query("SELECT * from Feeds", con)

# convert timestamp in ms to datetime objects (why are they in milliseconds?!)
FeedMedia.last_played_time = pd.to_datetime(FeedMedia.last_played_time, unit='ms')
FeedMedia.playback_completion_date = pd.to_datetime(FeedMedia.playback_completion_date, unit='ms')
FeedItems.pubDate = pd.to_datetime(FeedItems.pubDate, unit='ms')

# Do some magic
FeedMedia['percentage_played']= FeedMedia['position']/FeedMedia['duration']

df = pd.merge(FeedMedia, FeedItems, left_on='feeditem', right_on='id', suffixes=('_media', '_item'))
df = pd.merge(df, Feeds, left_on='feed', right_on='id', suffixes=('', '_feed'))

df.percentage_played.fillna(0,inplace=True)

df["pub_year"] = df["pubDate"].dt.year

app = JupyterDash(__name__)

app.layout = html.Div(children = [
    dcc.Dropdown(
        id="podcasts", 
        placeholder="Select some podcasts", 
        clearable=False, 
        options=[{"label": y, "value": y} for y in df["title_feed"].unique()],
        multi=True
    ),
    dcc.RangeSlider(
        id='year_slider',
        min=1990,
        max=2030,
        step=1,
        value=[2018, 2022],
        tooltip={"placement": "bottom", "always_visible": True}
    ),
    dcc.Graph(id="release", figure={}),
              
    dcc.Graph(id="bar-plot", figure={}),
    ])
    
    
@app.callback(Output("release", "figure"),
              Input("year_slider", "value"),
              Input("podcasts", "value"))
def year_range(year_slider,podcasts):
    # Scatter plot with weekday and duration in minutes
    df1 = df[df.playback_completion_date.dt.year.isin(range(year_slider[0],year_slider[1]))]
    if podcasts:
        df2 = df1[df1.title_feed.isin(podcasts)]
        fig = px.scatter(df2[df2["percentage_played"]>0], 
                 template="plotly_dark",
                 color_discrete_sequence=px.colors.qualitative.Bold,
                 y="duration", 
                 x="pubDate", 
                 color="title_feed", 
                 size = "percentage_played", 
                 height=500, 
                 range_x=year_slider,
                 )
    
    else:
        fig = px.scatter(df1[df1["percentage_played"]>0], 
                 template="plotly_dark",
                 color_discrete_sequence=px.colors.qualitative.Bold,
                 y="duration", 
                 x="pubDate", 
                 color="title_feed", 
                 size = "percentage_played", 
                 height=500, 
                 range_x=year_slider,
                 )
        
    return fig.update_layout(font_family="Rockwell",
                             showlegend=False,
                             legend=(dict(orientation="h", 
                                          title="", 
                                         )))

@app.callback(Output("bar-plot", "figure"),
              Input("year_slider", "value"),
              Input("podcasts", "value"))
def party(year_slider,podcasts):
    df1 = df[df.playback_completion_date.dt.year.isin(range(year_slider[0],year_slider[1]))]
    if podcasts:
        df2 = df1[df1.title_feed.isin(podcasts)]
        fig2 = px.bar(df2[df2["played_duration"]>0],
           template="plotly_dark",
           x=df2['playback_completion_date'].dt.dayofweek, 
           y=df2["played_duration"]/1000/60,
           color=df2['playback_completion_date'].dt.year.astype(str),
           color_discrete_sequence=px.colors.qualitative.Bold)
    
    else:
        fig2 = px.bar(df1[df1["played_duration"]>0],
           template="plotly_dark",
           x=df1['playback_completion_date'].dt.dayofweek, 
           y=df1["played_duration"]/1000/60,
           color=df1['playback_completion_date'].dt.year.astype(str),
           color_discrete_sequence=px.colors.qualitative.Bold)
        
    return fig2.update_layout(font_family="Rockwell",
                             showlegend=False,
                             legend=(dict(orientation="h", 
                                          title="", 
                                         )))
    
app.run_server()#mode="jupyterlab")

url = "http://localhost:8050"
webbrowser.open(url, new = 0, autoraise = true)