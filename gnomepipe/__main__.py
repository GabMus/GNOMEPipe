# __main__.py
#
# Copyright (C) 2017 GabMus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import pathlib
import json

import argparse
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf

from . import threading_helper as ThreadingHelper
from . import listbox_helper as ListboxHelper
from . import videofeed_flowbox_item as VideofeedFlowboxItem
from . import channel_listbox_item as ChannelListboxItem
from . import pipe_channel
from . import pipe_video

from urllib import request, parse


HOME = os.environ.get('HOME')
G_CONFIG_FILE_PATH = '{0}/.config/gnomepipe.json'.format(HOME)
G_CACHE_PATH = '{0}/.cache/gnomepipe/'.format(HOME)

# check if inside flatpak sandbox. if so change some variables
if 'XDG_RUNTIME_DIR' in os.environ.keys():
    if os.path.isfile('{0}/flatpak-info'.format(os.environ['XDG_RUNTIME_DIR'])):
        G_CONFIG_FILE_PATH = '{0}/gnomepipe.json'.format(os.environ.get('XDG_CONFIG_HOME'))
        G_CACHE_PATH = '{0}/gnomepipe/'.format(os.environ.get('XDG_CACHE_HOME'))

if not os.path.isdir(G_CACHE_PATH):
    os.makedirs(G_CACHE_PATH)

class Application(Gtk.Application):
    def __init__(self, **kwargs):
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gnomepipe/ui/ui.glade'
        )
        super().__init__(
            application_id='org.gabmus.gnomepipe',
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
        )
        self.RESOURCE_PATH = '/org/gabmus/gnomepipe/'

        self.CONFIG_FILE_PATH = G_CONFIG_FILE_PATH  # G stands for Global (variable)

        self.configuration = self.get_config_file()
        self.channels = []

        self.builder.connect_signals(self)

        settings = Gtk.Settings.get_default()
        # settings.set_property("gtk-application-prefer-dark-theme", True)

        self.window = self.builder.get_object('window')

        self.window.set_icon_name('org.gabmus.gnomepipe')

        self.window.resize(
            self.configuration['windowsize']['width'],
            self.configuration['windowsize']['height']
        )

        self.feed_videos_flowbox = self.builder.get_object('feedVideosFlowbox')
        self.spinner_or_content_stack = self.builder.get_object('spinnerOrContentStack')
        self.refresh_button = self.builder.get_object('refreshButton')

        self.channels_listbox = self.builder.get_object('channelsListbox')

        self.searchbar = self.builder.get_object('searchbar')
        self.searchbar_entry = self.builder.get_object('searchbarEntry')
        self.search_toggle_button = self.builder.get_object('searchToggleButton')

        self.channels_stack = self.builder.get_object('channelsViewOrSearchStack')
        self.feed_stack = self.builder.get_object('feedViewOrSearchStack')

        self.channels_search_listbox = self.builder.get_object('channelsSearchListbox')
        self.video_search_flowbox = self.builder.get_object('videoSearchFlowbox')

        # Fixing searchbar: it has multiple box children (not explicit in the
        # xml but visible with gtk parasite), and one of them must be set to fill
        # otherwise the searchbar entry will be very small
        self.searchbar.get_child().get_child().get_children()[1].set_halign(Gtk.Align.FILL)
        self.searchbar_entry.set_hexpand(True)

        self.feed_or_detail_stack = self.builder.get_object('videoFeedOrDetailStack')
        self.detail_thumb_overlay = self.builder.get_object('videoDetailThumbnailOverlay')
        self.play_icon = Gtk.Image.new_from_icon_name(
            'media-playback-start',
            Gtk.IconSize.DIALOG
        )
        self.detail_thumb_overlay.add_overlay(self.play_icon)
        self.play_icon.connect(
            'button-press-event', self.on_detail_video_thumb_press
        )
        self.detail_title_label = self.builder.get_object('videoDetailTitleLabel')
        self.detail_video_thumb = self.builder.get_object('videoDetailThumbnail')
        self.detail_description_label = self.builder.get_object('videoDetailDescriptionLabel')
        self.detail_channel_picture = self.builder.get_object('videoDetailChannelPicture')
        self.detail_channel_name_label = self.builder.get_object('videoDetailChannelNameLabel')
        self.detail_thumb_button = self.builder.get_object('videoDetailThumbnailButton')

        self.back_button = self.builder.get_object('backButton')

        self.errorDialog = Gtk.MessageDialog()
        self.errorDialog.add_button('Ok', 0)
        self.errorDialog.set_default_response(0)
        self.errorDialog.set_transient_for(self.window)

        self.mpv_process = None

    def on_window_size_allocate(self, *args):
        alloc = self.window.get_allocation()
        self.configuration['windowsize']['width'] = alloc.width
        self.configuration['windowsize']['height'] = alloc.height

    def do_before_quit(self):
        self.save_config_file()

    def save_config_file(self, n_config=None):
        if not n_config:
            n_config = self.configuration
        with open(self.CONFIG_FILE_PATH, 'w') as fd:
            fd.write(json.dumps(n_config))
            fd.close()

    def get_config_file(self):
        if not os.path.isfile(self.CONFIG_FILE_PATH):
            n_config = {
                'windowsize': {
                    'width': 600,
                    'height': 400
                },
                'subscriptions': [
                    'UCVqlDOUyIjMWqBUhp73a90g'
                ]
            }
            self.save_config_file(n_config)
            return n_config
        else:
            do_save = False
            with open(self.CONFIG_FILE_PATH, 'r') as fd:
                config = json.loads(fd.read())
                fd.close()
                if not 'windowsize' in config.keys():
                    config['windowsize'] = {
                        'width': 600,
                        'height': 400
                    }
                    do_save = True
                if not 'subscriptions' in config.keys():
                    config['subscriptions'] = [
                        'UCVqlDOUyIjMWqBUhp73a90g'
                    ]
                    do_save = True
                if do_save:
                    self.save_config_file(config)
                return config

    def do_activate(self):
        self.add_window(self.window)
        self.window.set_wmclass('GNOMEPipe', 'GNOMEPipe')

        appMenu = Gio.Menu()
        appMenu.append("About", "app.about")
        appMenu.append("Settings", "app.settings")
        appMenu.append("Quit", "app.quit")

        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about_activate)
        self.builder.get_object("aboutdialog").connect(
            "delete-event", lambda *_:
                self.builder.get_object("aboutdialog").hide() or True
        )
        self.add_action(about_action)

        settings_action = Gio.SimpleAction.new("settings", None)
        settings_action.connect("activate", self.on_settings_activate)
        self.builder.get_object("settingsWindow").connect(
            "delete-event", lambda *_:
                self.builder.get_object("settingsWindow").hide() or True
        )
        self.add_action(settings_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit_activate)
        self.add_action(quit_action)
        self.set_app_menu(appMenu)

        self.window.show_all()

        # After components init, do the following
        self.refresh_feed_ui(True)
        self.refresh_channels_ui(False)

    def do_command_line(self, args):
        """
        GTK.Application command line handler
        called if Gio.ApplicationFlags.HANDLES_COMMAND_LINE is set.
        must call the self.do_activate() to get the application up and running.
        """
        Gtk.Application.do_command_line(self, args)  # call the default commandline handler
        # make a command line parser
        parser = argparse.ArgumentParser(prog='gui')
        # add a -c/--color option
        parser.add_argument('-q', '--quit-after-init', dest='quit_after_init', action='store_true', help='initialize application and quit')
        # parse the command line stored in args, but skip the first element (the filename)
        self.args = parser.parse_args(args.get_arguments()[1:])
        # call the main program do_activate() to start up the app
        self.do_activate()
        return 0

    def on_about_activate(self, *args):
        self.builder.get_object("aboutdialog").show()

    def on_settings_activate(self, *args):
        self.builder.get_object("settingsWindow").show()

    def on_quit_activate(self, *args):
        self.do_before_quit()
        self.quit()

    def onDeleteWindow(self, *args):
        self.do_before_quit()
        self.quit()

    def on_aboutdialog_close(self, *args):
        self.builder.get_object("aboutdialog").hide()

    def refresh_channels(self, subscriptions=None):
        if subscriptions is None:
            subscriptions = self.configuration['subscriptions']
        for sub in subscriptions:
            if not sub in [c.channelid for c in self.channels]:
                self.channels.append(pipe_channel.Channel.from_channelid(sub, G_CACHE_PATH))
        for index, channel in enumerate(self.channels):
            if not channel.channelid in subscriptions:
                self.channels.pop(index)
            else:
                channel.fetch_videos()

    def spinner_set_state(self, active):
        if active:
            self.spinner_or_content_stack.set_visible_child_name('spinner')
        else:
            self.spinner_or_content_stack.set_visible_child_name('main')

    def empty_flowbox(self, flowbox):
        while True:
            child = flowbox.get_child_at_index(0)
            if child:
                flowbox.remove(child)
            else:
                break

    def refresh_feed_ui(self, reload=True):
        self.refresh_button.set_sensitive(False)
        self.spinner_set_state(True)
        self.empty_flowbox(self.feed_videos_flowbox)
        if reload:
            refresh_thread = ThreadingHelper.do_async(
                self.refresh_channels,
                (self.configuration['subscriptions'],)
            )
            ThreadingHelper.wait_for_thread(refresh_thread)
        self.spinner_set_state(False)
        # TODO: reimplement mixing all channels together with datetime ordering
        vffilist=[]
        for channel in self.channels:
            if not channel.videos is None:
                for video in channel.videos:
                    vffi = VideofeedFlowboxItem.VideofeedBox(video)
                    self.feed_videos_flowbox.add(vffi)
                    vffilist.append(vffi)
                    vffi.show_all()
                    self.feed_videos_flowbox.show_all()
        for vffi in vffilist:
            vffi.set_video_thumb()
        self.refresh_button.set_sensitive(True)

    def refresh_channels_ui(self, reload=True):
        self.refresh_button.set_sensitive(False)
        self.spinner_set_state(True)
        ListboxHelper.empty_listbox(self.channels_listbox)
        if reload:
            refresh_thread = ThreadingHelper.do_async(
                self.refresh_channels,
                (self.configuration['subscriptions'],)
            )
            ThreadingHelper.wait_for_thread(refresh_thread)
        self.spinner_set_state(False)
        clbilist=[]
        for channel in self.channels:
            clbi = ChannelListboxItem.ChannelBox(channel)
            self.channels_listbox.add(clbi)
            clbilist.append(clbi)
            clbi.show_all()
            self.channels_listbox.show_all()
        for clbi in clbilist:
            clbi.set_channel_picture()
        self.refresh_button.set_sensitive(True)

    def set_search_state(self, active):
        self.searchbar.set_search_mode(active)
        self.channels_stack.set_visible_child_name(
            'search' if active else 'view' # ternary operator THEN IF_CONDITION ELSE
        )
        self.feed_stack.set_visible_child_name(
            'search' if active else 'view' # ternary operator THEN IF_CONDITION ELSE
        )
        self.search_toggle_button.set_active(active)

    def get_channel_search_results(self, keywords, return_list):
        result_dict = pipe_channel.yam.search_channel(keywords)
        return_list.append(result_dict)

    def get_video_search_results(self, keywords, return_list):
        result_dict = pipe_channel.yam.search_video(keywords)
        return_list.append(result_dict)

    def make_channel_from_id(self, channelid, return_list):
        n_channel = pipe_channel.Channel.from_channelid(
            channelid,
            G_CACHE_PATH
        )
        return_list.append(n_channel)

    def make_channel_from_constructor(self, channelid, name, picture, description, return_list):
        n_channel = pipe_channel.Channel(
            channelid, name, picture, description, G_CACHE_PATH
        )
        return_list.append(n_channel)

    def do_all_search(self, keywords):
        return_list_channel = []
        return_list_video = []
        t_channel = ThreadingHelper.do_async(
            self.get_channel_search_results,
            (keywords, return_list_channel)
        )
        t_video = ThreadingHelper.do_async(
            self.get_video_search_results,
            (keywords, return_list_video)
        )
        ThreadingHelper.wait_for_thread(t_video)
        result_dict_video = return_list_video[0]
        result_videos = []
        vffilist = []
        self.empty_flowbox(self.video_search_flowbox)
        for info in result_dict_video['items']:
            n_channel_return_list = []
            n_channel_t = ThreadingHelper.do_async(
                self.make_channel_from_id,
                (info['snippet']['channelId'], n_channel_return_list)
            )
            ThreadingHelper.wait_for_thread(n_channel_t)
            result_pipe_video = pipe_video.Video(
                n_channel_return_list[0],
                info['snippet']['title'],
                'https://www.youtube.com/watch?v={0}'.format(
                    info['id']['videoId']
                ),
                'https://img.youtube.com/vi/{0}/mqdefault.jpg'.format(
                    info['id']['videoId']
                ),
                info['snippet']['description'],
                info['snippet']['publishedAt'],
                G_CACHE_PATH
            )
            result_videos.append(result_pipe_video)
            vffi = VideofeedFlowboxItem.VideofeedBox(result_pipe_video)
            self.video_search_flowbox.add(vffi)
            vffilist.append(vffi)
            vffi.show_all()
            vffi.set_video_thumb()
        # for vffi in vffilist:
        #     vffi.set_video_thumb()
        ThreadingHelper.wait_for_thread(t_channel)
        result_dict_channel = return_list_channel[0]
        result_channels = []
        clbilist = []
        ListboxHelper.empty_listbox(self.channels_search_listbox)
        for info in result_dict_channel['items']:
            n_channel_return_list = []
            channelid = None
            channelpic = None
            if 'id' in info.keys():
                channelid = info['id']['channelId']
            else:
                channelid = info['snippet']['channelId']
            if 'thumbnails' in info['snippet'].keys():
                channelpic = info['snippet']['thumbnails']['default']['url']
            n_channel_t = ThreadingHelper.do_async(
                self.make_channel_from_constructor,
                (
                    channelid,
                    info['snippet']['title'],
                    channelpic,
                    info['snippet']['description'],
                    n_channel_return_list
                )
            )
            ThreadingHelper.wait_for_thread(n_channel_t)
            result_pipe_channel = n_channel_return_list[0]
            result_channels.append(result_pipe_channel)
            clbi = ChannelListboxItem.ChannelBox(result_pipe_channel)
            self.channels_search_listbox.add(clbi)
            clbilist.append(clbi)
            clbi.show_all()
            clbi.set_channel_picture()

    def make_thumb_and_channel_pixbufs(self, video, return_list):
        video_url = video.thumbnail
        video_extension = video_url[-4:]
        video_fullpath = video.cachedir+video.videohash+video_extension
        if not os.path.isfile(video_fullpath):
            print('Downloading thumb of video {0}'.format(video.title))
            request.urlretrieve(video_url, video_fullpath)
        else:
            print('Cache hit for thumb of video {0}'.format(video.title))
        thumb_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(video_fullpath, 250, 250, True)
        chan_url = video.channel.picture
        chan_extension = chan_url[-4:]
        chan_fullpath = video.channel.cachedir+video.channel.channelhash+chan_extension
        if not os.path.isfile(chan_fullpath):
            print('Downloading picture of channel {0}'.format(video.channel.name))
            request.urlretrieve(chan_url, chan_fullpath)
        else:
            print('Cache hit for picture of channel {0}'.format(video.channel.name))
        picture_pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(chan_fullpath, 50, 50, True)
        return_list.append(thumb_pixbuf)
        return_list.append(picture_pixbuf)

    def open_video_detail(self, video):
        self.back_button.set_sensitive(True)
        self.set_search_state(False)
        self.detail_thumb_overlay.video = video
        self.detail_title_label.set_text(video.title)
        self.detail_channel_name_label.set_text(video.channel.name)
        self.detail_description_label.set_text(
            'Published {0}\n\n{1}'.format(video.datetime, video.description)
        )
        self.feed_or_detail_stack.set_visible_child_name('detail')
        return_list = []
        t = ThreadingHelper.do_async(
            self.make_thumb_and_channel_pixbufs,
            (video, return_list)
        )
        ThreadingHelper.wait_for_thread(t)
        self.detail_video_thumb.set_from_pixbuf(return_list[0])
        self.detail_channel_picture.set_from_pixbuf(return_list[1])

    def close_video_detail(self):
        self.back_button.set_sensitive(False)
        self.feed_or_detail_stack.set_visible_child_name('feed')

    # Handler functions START

    def on_feedVideosFlowbox_child_activated(self, flowbox, child):
        self.open_video_detail(child.video)

    def on_refreshButton_clicked(self, btn):
        self.refresh_feed_ui(True)
        self.refresh_channels_ui(False)

    def on_wallpapersFlowbox_child_activated(self, flowbox, selected_item):
        self.set_monitor_wallpaper_preview(
            selected_item.get_child().wallpaper_path
        )

    def on_searchToggleButton_toggled(self, button):
        self.set_search_state(button.get_active())

    def on_searchbarEntry_activate(self, searchentry):
        self.do_all_search(searchentry.get_text())

    def on_detail_video_thumb_press(self, eventbox, eventbutton):
        video = eventbox.get_child().video
        if not self.mpv_process is None:
            if self.mpv_process.poll() is None: # Process is still running
                print('Another process is still running')
                return
        video.stop()
        self.mpv_process = video.play()

    def on_backButton_clicked(self, button):
        self.close_video_detail()

    # Handler functions END

def main():
    application = Application()

    try:
        ret = application.run(sys.argv)
    except SystemExit as e:
        ret = e.code

    sys.exit(ret)


if __name__ == '__main__':
    main()
