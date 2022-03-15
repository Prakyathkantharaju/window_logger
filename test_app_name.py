import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck as wnck

screen = wnck.screen_get_default()
window = screen.get_active_window()
pid = window.get_pid()
