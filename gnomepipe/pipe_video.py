import os
from subprocess import Popen

mpv_devnull = open(os.devnull , 'wb')

class Video:

    def __init__(self, channel, title, videolink, thumbnail, description, datetime):
        self.channel = channel
        self.title = title
        self.videolink = videolink
        self.thumbnail = thumbnail
        self.description = description
        self.datetime = datetime
        self.mpv_process = None

    def play(self):
        if not self.mpv_process is None:
            print('Process open already')
        else:
            self.mpv_process = Popen(
                ['mpv', self.videolink],
                stdout=mpv_devnull, stderr=mpv_devnull
            )
            return self.mpv_process


    def stop(self):
        if self.mpv_process is None:
            print('Process is None')
            return
        else:
            self.mpv_process.terminate()
            self.mpv_process = None
