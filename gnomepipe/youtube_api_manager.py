
from . import secret
from urllib import request, parse
import json

YT_API_PREFIX='https://www.googleapis.com/youtube/v3/'

def get_channel_id(username):
    res = request.urlopen('{0}channels?key={1}&forUsername={2}&part=id'.format(
        YT_API_PREFIX,
        secret.YT_API_KEY,
        username
    )).read()
    return json.loads(res)

def search_channel(keywords):
    res = request.urlopen('{0}search?key={1}&maxResults=25&q={2}&type=channel&part=snippet'.format(
        YT_API_PREFIX,
        secret.YT_API_KEY,
        parse.quote(keywords)
    )).read()
    return json.loads(res)

def search_video(keywords):
    res = request.urlopen('{0}search?key={1}&maxResults=25&q={2}&type=video&part=snippet'.format(
        YT_API_PREFIX,
        secret.YT_API_KEY,
        parse.quote(keywords)
    )).read()
    return json.loads(res)

def get_channel_info(channelid):
    res = request.urlopen('{0}channels?key={1}&id={2}&part=snippet'.format(
        YT_API_PREFIX,
        secret.YT_API_KEY,
        channelid
    )).read()
    return json.loads(res)
