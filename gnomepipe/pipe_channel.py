from . import youtube_api_manager as yam
from . import pipe_video
import feedparser
import datetime

FEED_PREFIX='https://www.youtube.com/feeds/videos.xml?channel_id='
WEBLINK_PREFIX='https://youtube.com/channel/'
ISO_DATETIME_FORMAT='%Y-%m-%dT%H:%M:%S+00:00'

class Channel:

    @classmethod
    def from_channelid(cls, channelid, cachedir):
        info = yam.get_channel_info(channelid)
        return cls(
            channelid,
            info['items'][0]['snippet']['title'],
            info['items'][0]['snippet']['thumbnails']['default']['url'],
            info['items'][0]['snippet']['description'],
            cachedir
        )

    def __init__(self, channelid, name, picture, description, cachedir):
        self.channelid = channelid
        self.weblink = WEBLINK_PREFIX + channelid
        self.name = name
        self.picture = picture
        self.description = description
        self.feed_url = FEED_PREFIX + channelid
        self.feed = feedparser.parse(self.feed_url)
        self.cachedir = cachedir
        self.videos = None

    def fetch_videos(self):
        if self.videos is None:
            self.videos=[]
            for entry in self.feed.entries:
                self.videos.append(
                    pipe_video.Video(
                        self,
                        entry['title'],
                        entry['link'],
                        entry['media_thumbnail'][0]['url'],
                        entry['summary'],
                        datetime.datetime.strptime(
                            entry['published'], ISO_DATETIME_FORMAT
                        ),
                        self.cachedir
                    )
                )
