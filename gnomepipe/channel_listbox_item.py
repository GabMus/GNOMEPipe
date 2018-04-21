import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf
from . import threading_helper as ThreadingHelper
import os
from urllib import request

class ChannelBox(Gtk.ListBoxRow):
    def __init__(self, channel, *args, **kwds):
        super().__init__(*args, **kwds)

        self.channel = channel

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)

        self.container_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.channel_picture = Gtk.Image.new_from_icon_name('image-x-generic', Gtk.IconSize.DIALOG)
        self.container_box.pack_start(self.channel_picture, False, False, 3)

        self.channelname_label = Gtk.Label()
        self.channelname_label.set_text(self.channel.name)
        self.channelname_label.set_ellipsize(3)
        self.channelname_label.set_halign(Gtk.Align.START)

        self.container_box.pack_start(self.channelname_label, False, False, 3)
        self.container_box.set_margin_left(12)
        self.container_box.set_margin_right(12)
        self.container_box.set_margin_top(12)
        self.container_box.set_margin_bottom(12)
        self.add(self.container_box)
        self.set_tooltip_text(self.channel.name)

        self.set_size_request(380, -1)

    def set_channel_picture(self):
        pixbuf_fake_list=[]
        pixbuf_thread = ThreadingHelper.do_async(
            self.make_channel_picture_pixbuf,
            (self.channel.picture, pixbuf_fake_list)
        )
        ThreadingHelper.wait_for_thread(pixbuf_thread)
        self.channel_picture.set_from_pixbuf(pixbuf_fake_list[0])
        self.channel_picture.show()

    def make_channel_picture_pixbuf(self, picurl, return_pixbuf_pointer=-1):
        # TODO: explore gdk_pixbuf_new_from_stream_async
        url = self.channel.picture
        extension = url[-4:]
        fullpath = self.channel.cachedir+self.channel.channelhash+extension
        if not os.path.isfile(fullpath):
            print('Downloading picture of channel {0}'.format(self.channel.name))
            request.urlretrieve(url, fullpath)
        else:
            print('Cache hit for picture of channel {0}'.format(self.channel.name))
        #res = request.urlopen(url)
        #input_stream = Gio.MemoryInputStream.new_from_data(res.read(), None)
        picture_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(fullpath, 50, 50, True)
        if type(return_pixbuf_pointer) == list:
            return_pixbuf_pointer.append(picture_pixbuf)
        return picture_pixbuf
