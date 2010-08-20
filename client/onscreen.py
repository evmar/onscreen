#!/usr/bin/python

import gtk

# Window that holds the grab.  Not visible, positioned at 0,0 so our
# events are all relative to 0,0.
grab_win = gtk.Window(gtk.WINDOW_POPUP)
grab_win.move(0, 0)
grab_win.set_default_size(0, 0)
grab_win.show()

screen = gtk.gdk.screen_get_default()
root_win = screen.get_root_window()

sel_win = gtk.Window(gtk.WINDOW_POPUP)
sel_win.set_default_size(0, 0)
sel_win.show()

x1 = y1 = x2 = y2 = None

def motion(widget, event):
    global x1, y1

    if x1 is None:
        x1, y1 = int(event.x), int(event.y)
        return

    x, y = int(event.x), int(event.y)

    sel_win.move(min(x1, x), min(y1, y))
    w = max(abs(x - x1), 1)
    h = max(abs(y - y1), 1)
    sel_win.resize(w, h)
    shape = gtk.gdk.region_rectangle((1, 1, w - 2, h - 2))
    sel_win.window.shape_combine_region(shape, 0, 0)

def stop_drag(widget, event):
    gtk.gdk.pointer_ungrab(time=event.time)
    gtk.main_quit()
    return True

grab_win.connect('motion-notify-event', motion)
grab_win.connect('button-release-event', stop_drag)


def screengrab():
    pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 400, 300)
    pixbuf.get_from_drawable(win, win.get_colormap(), 100, 100, 0, 0, 400, 300)
    pixbuf.save('test.png', 'png')

mask = gtk.gdk.BUTTON1_MOTION_MASK | gtk.gdk.BUTTON_RELEASE_MASK
gtk.gdk.pointer_grab(grab_win.window, event_mask=mask,
                     cursor=gtk.gdk.Cursor(gtk.gdk.CROSSHAIR))
gtk.main()
