from . import youtube_api_manager as yam

FEED_PREFIX="https://www.youtube.com/feeds/videos.xml?channel_id="

class Channel:

    @classmethod
    def from_channelid(cls, channelid):
        info = yam.get_channel_info(channelid)
        return cls(
            channelid,
            info['items'][0]['snippet']['title'],
            info['items'][0]['snippet']['thumbnails']['default']['url'],
            info['items'][0]['snippet']['description']
        )

    def __init__(self, channelid, name, picture, description):
        self.channelid = channelid
        self.name = name
        self.picture = picture
        self.description = description
        self.feed_url = FEED_PREFIX + channelid

    def fetch_videos(self):
