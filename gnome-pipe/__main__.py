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

import hashlib # for pseudo-random wallpaper name generation


HOME = os.environ.get('HOME')
G_CONFIG_FILE_PATH = '{0}/.config/gnome-pipe.json'.format(HOME)

# check if inside flatpak sandbox. if so change some variables
if 'XDG_RUNTIME_DIR' in os.environ.keys():
    if os.path.isfile('{0}/flatpak-info'.format(os.environ['XDG_RUNTIME_DIR'])):
        G_CONFIG_FILE_PATH = '{0}/gnome-pipe.json'.format(os.environ.get('XDG_CONFIG_HOME'))

class Application(Gtk.Application):
    def __init__(self, **kwargs):
        self.builder = Gtk.Builder.new_from_resource(
            '/org/gabmus/gnome-pipe/ui/ui.glade'
        )
        super().__init__(
            application_id='org.gabmus.gnome-pipe',
            flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            **kwargs
        )
        self.RESOURCE_PATH = '/org/gabmus/gnome-pipe/'

        self.CONFIG_FILE_PATH = G_CONFIG_FILE_PATH  # G stands for Global (variable)

        self.configuration = self.get_config_file()

        self.builder.connect_signals(self)

        settings = Gtk.Settings.get_default()
        # settings.set_property("gtk-application-prefer-dark-theme", True)

        self.window = self.builder.get_object('window')

        self.window.set_icon_name('org.gabmus.gnome-pipe')

        self.window.resize(
            self.configuration['windowsize']['width'],
            self.configuration['windowsize']['height']
        )

        self.mainBox = self.builder.get_object('mainBox')

        self.errorDialog = Gtk.MessageDialog()
        self.errorDialog.add_button('Ok', 0)
        self.errorDialog.set_default_response(0)
        self.errorDialog.set_transient_for(self.window)

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
            }
            self.save_config_file(n_config)
            return n_config
        else:
            do_save = False
            with open(self.CONFIG_FILE_PATH, 'r') as fd:
                if not 'windowsize' in config.keys():
                    config['windowsize'] = {
                        'width': 600,
                        'height': 400
                    }
                    do_save = True
                if do_save:
                    self.save_config_file(config)
                return config

    def do_activate(self):
        self.add_window(self.window)
        self.window.set_wmclass('GNOME-Pipe', 'GNOME-Pipe')

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

    # Handler functions START

    def on_wallpapersFlowbox_child_activated(self, flowbox, selected_item):
        self.set_monitor_wallpaper_preview(
            selected_item.get_child().wallpaper_path
        )

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