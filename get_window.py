"""python-xlib example which reacts to changing the active window/title.

Requires:
- Python
- python-xlib

Tested with Python 2.x because my Kubuntu 14.04 doesn't come with python-xlib
for Python 3.x.

Design:
-------

Any modern window manager that isn't horrendously broken maintains an X11
property on the root window named _NET_ACTIVE_WINDOW.

Any modern application toolkit presents the window title via a property
named _NET_WM_NAME.

This listens for changes to both of them and then hides duplicate events
so it only reacts to title changes once.

Known Bugs:
-----------

- Under some circumstances, I observed that the first window creation and last
  window deletion on on an empty desktop (ie. not even a taskbar/panel) would
  go ignored when using this test setup:

      Xephyr :3 &
      DISPLAY=:3 openbox &
      DISPLAY=:3 python3 x11_watch_active_window.py

      # ...and then launch one or more of these in other terminals
      DISPLAY=:3 leafpad
"""

# pylint: disable=unused-import
from contextlib import contextmanager
from typing import Any, Dict, Optional, Tuple, Union  # noqa

from Xlib import X
from Xlib.display import Display
from Xlib.error import XError
from Xlib.xobject.drawable import Window
from Xlib.protocol.rq import Event

class GetWindow():
# Connect to the X server and get the root window
    disp = Display()
    root = disp.screen().root

# Prepare the property names we use so they can be fed into X11 APIs
    NET_ACTIVE_WINDOW = disp.intern_atom('_NET_ACTIVE_WINDOW')
    NET_WM_NAME = disp.intern_atom('_NET_WM_NAME')  # UTF-8
    WM_NAME = disp.intern_atom('WM_NAME')           # Legacy encoding

    last_seen = {'xid': None, 'title': None}  # type: Dict[str, Any]


    @contextmanager
    def window_obj(self, win_id: Optional[int]) -> Window:
        """Simplify dealing with BadWindow (make it either valid or None)"""
        window_obj = None
        if win_id:
            try:
                window_obj = self.disp.create_resource_object('window', win_id)
            except XError:
                pass
        yield window_obj


    def get_active_window(self) -> Tuple[Optional[int], bool]:
        """Return a (window_obj, focus_has_changed) tuple for the active window."""
        response = self.root.get_full_property(self.NET_ACTIVE_WINDOW,
                                          X.AnyPropertyType)
        if not response:
            return None, False
        win_id = response.value[0]

        focus_changed = (win_id != self.last_seen['xid'])
        if focus_changed:
            with self.window_obj(self.last_seen['xid']) as old_win:
                if old_win:
                    old_win.change_attributes(event_mask=X.NoEventMask)

            self.last_seen['xid'] = win_id
            with self.window_obj(win_id) as new_win:
                if new_win:
                    new_win.change_attributes(event_mask=X.PropertyChangeMask)

        return win_id, focus_changed


    def _get_window_name_inner(self, win_obj: Window) -> str:
        """Simplify dealing with _NET_WM_NAME (UTF-8) vs. WM_NAME (legacy)"""
        for atom in (self.NET_WM_NAME, self.WM_NAME):
            try:
                window_name = win_obj.get_full_property(atom, 0)
            except UnicodeDecodeError:  # Apparently a Debian distro package bug
                title = "<could not decode characters>"
            else:
                if window_name:
                    win_name = window_name.value  # type: Union[str, bytes]
                    if isinstance(win_name, bytes):
                        # Apparently COMPOUND_TEXT is so arcane that this is how
                        # tools like xprop deal with receiving it these days
                        win_name = win_name.decode('latin1', 'replace')
                    return win_name
                else:
                    title = "<unnamed window>"

        return "{} (XID: {})".format(title, win_obj.id)


    def get_window_name(self, win_id: Optional[int]) -> Tuple[Optional[str], bool]:
        """Look up the window name for a given X11 window ID"""
        if not win_id:
            self.last_seen['title'] = None
            return self.last_seen['title'], True

        title_changed = False
        with self.window_obj(win_id) as wobj:
            if wobj:
                try:
                    win_title = self._get_window_name_inner(wobj)
                except XError:
                    pass
                else:
                    title_changed = (win_title != self.last_seen['title'])
                    self.last_seen['title'] = win_title

        return self.last_seen['title'], title_changed


    def handle_xevent(self, event: Event):
        """Handler for X events which ignores anything but focus/title change"""
        if event.type != X.PropertyNotify:
            return

        changed = False
        if event.atom == self.NET_ACTIVE_WINDOW:
            if self.get_active_window()[1]:
                self.get_window_name(self.last_seen['xid'])  # Rely on the side-effects
                changed = True
        elif event.atom in (self.NET_WM_NAME, self.WM_NAME):
            changed = changed or self.get_window_name(self.last_seen['xid'])[1]

        if changed:
            self.handle_change(self.last_seen)
            return True
        return False


    def handle_change(self, new_state: dict):
        """Replace this with whatever you want to actually do"""
        print(new_state)

if __name__ == '__main__':

    get_window = GetWindow()
    # Listen for _NET_ACTIVE_WINDOW changes
    get_window.root.change_attributes(event_mask=X.PropertyChangeMask)

    # Prime last_seen with whatever window was active when we started this
    get_window.get_window_name(get_window.get_active_window()[0])
    get_window.handle_change(get_window.last_seen)

    while True:  # next_event() sleeps until we get an event
        get_window.handle_xevent(get_window.disp.next_event())
