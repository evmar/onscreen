#!/usr/bin/python

import gtk

screen = gtk.gdk.screen_get_default()
root_win = screen.get_root_window()

x1 = y1 = x2 = y2 = None

def screenshot():
    w = abs(x2 - x1)
    h = abs(y2 - y1)
    if w > 0 and h > 0:
        pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, w, h)
        pixbuf.get_from_drawable(root_win, root_win.get_colormap(),
                                 min(x1, x2), min(y1, y2),
                                 0, 0, w, h)
        pixbuf.save('test.png', 'png')


# Window that holds the grab.  Not visible, positioned at 0,0 so our
# events are all relative to 0,0.
grab_win = gtk.Window(gtk.WINDOW_POPUP)
grab_win.move(0, 0)
grab_win.set_default_size(0, 0)
grab_win.show()

sel_win = gtk.gdk.Window(root_win, 0, 0, gtk.gdk.WINDOW_TEMP, 0,
                         gtk.gdk.INPUT_OUTPUT, override_redirect=True)
sel_win.show()

def motion(widget, event):
    global x1, y1, x2, y2

    if x1 is None:
        x1, y1 = int(event.x), int(event.y)
        return

    x2, y2 = int(event.x), int(event.y)

    sel_win.move(min(x1, x2), min(y1, y2))
    w = max(abs(x2 - x1), 1)
    h = max(abs(y2 - y1), 1)
    sel_win.resize(w, h)
    shape = gtk.gdk.region_rectangle((0, 0, w, h))
    shape.subtract(gtk.gdk.region_rectangle((1, 1, w - 2, h - 2)))
    sel_win.shape_combine_region(shape, 0, 0)

def button_release(widget, event):
    gtk.gdk.pointer_ungrab(time=event.time)
    gtk.main_quit()
    if event.button == 1:  # allow cancelling with other mouse buttons
        screenshot()
    return True

grab_win.connect('motion-notify-event', motion)
grab_win.connect('button-release-event', button_release)

mask = gtk.gdk.BUTTON1_MOTION_MASK | gtk.gdk.BUTTON_RELEASE_MASK
gtk.gdk.pointer_grab(grab_win.window, event_mask=mask,
                     cursor=gtk.gdk.Cursor(gtk.gdk.CROSSHAIR))
gtk.main()
