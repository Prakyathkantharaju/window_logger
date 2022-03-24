

import gi
import time

gi.require_version("Wnck", "3.0")
from gi.repository import Wnck

scr = Wnck.Screen.get_default()

while True:
    time.sleep(1)
    scr.force_update()
    print(scr.get_active_window())
    print(scr.get_active_window().get_name())
