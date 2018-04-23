import threading
from gi.repository import Gtk

threads_pool = []

def do_async(function, args): # args must be tuple
    t = threading.Thread(
        group = None,
        target = function,
        name = None,
        args = args
    )
    t.start()
    threads_pool.append(t)
    return t

def wait_for_thread(thread):
    while thread.is_alive():
        while Gtk.events_pending():
            Gtk.main_iteration()
    threads_pool.pop(threads_pool.index(thread))
    return
