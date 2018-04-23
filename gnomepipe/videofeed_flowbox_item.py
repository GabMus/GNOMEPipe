import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf
from urllib import request
from . import threading_helper as ThreadingHelper
import os
import html

class VideofeedBox(Gtk.FlowBoxChild):

    def __init__(self, video, *args, **kwds):
        super().__init__(*args, **kwds)

        self.video = video

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)

        self.container_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.video_thumb = Gtk.Image.new_from_icon_name('image-x-generic', Gtk.IconSize.DIALOG)
        self.container_box.add(self.video_thumb)

        self.titlelabel = Gtk.Label()
        self.titlelabel.set_use_markup(True)
        self.titlelabel.set_label('<big>{0}</big>'.format(html.escape(self.video.title)))
        self.titlelabel.set_ellipsize(3) # 3 = ellipsize end
        self.titlelabel.set_halign(Gtk.Align.START)
        self.titlelabel.set_line_wrap(True)
        #self.titlelabel.set_size_request(100, -1)
        self.titlelabel.set_max_width_chars(27)

        self.container_box.pack_end(self.titlelabel, False, False, 3)

        self.container_box.set_margin_left(12)
        self.container_box.set_margin_right(12)

        self.add(self.container_box)
        self.set_tooltip_text('{0} - {1}'.format(self.video.title, self.video.channel.name))
        self.set_size_request(250, -1)

    def set_video_thumb(self):
        pixbuf_fake_list=[]
        pixbuf_thread = ThreadingHelper.do_async(
            self.make_video_thumb_pixbuf,
            (self.video.thumbnail, pixbuf_fake_list)
        )
        ThreadingHelper.wait_for_thread(pixbuf_thread)
        self.video_thumb.set_from_pixbuf(pixbuf_fake_list[0])
        self.video_thumb.show()

    def make_video_thumb_pixbuf(self, thumburl, return_pixbuf_pointer=-1):
        # TODO: explore gdk_pixbuf_new_from_stream_async
        url = self.video.thumbnail
        extension = url[-4:]
        fullpath = self.video.cachedir+self.video.videohash+extension
        if not os.path.isfile(fullpath):
            print('Downloading thumb of video {0}'.format(self.video.title))
            request.urlretrieve(url, fullpath)
        else:
            print('Cache hit for thumb of video {0}'.format(self.video.title))
        #res = request.urlopen(url)
        #input_stream = Gio.MemoryInputStream.new_from_data(res.read(), None)
        thumb_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fullpath, 250, 250, True)
        if type(return_pixbuf_pointer) == list:
            return_pixbuf_pointer.append(thumb_pixbuf)
        return thumb_pixbuf

    def play_video(self):
        return self.video.play()

    def stop_video(self):
        self.video.stop()
