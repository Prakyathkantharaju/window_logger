from Xlib import X
# pylint: disable=unused-import
from typing import Any, Dict, Optional, Tuple, Union  # noqa
import sqlite3
import datetime

from get_window import GetWindow

con = sqlite3.connect('window.db')
c = con.cursor()


def get_table_name(cursor: sqlite3.Cursor, database: sqlite3.Connection) -> str:
    """
    Get the name of the table in the database.
    """
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_name = cursor.fetchall()[0][0]
    except IndexError:
        table_name = []
    return table_name

def create_table(cursor: sqlite3.Cursor, database: sqlite3.Connection, name: str) -> None:
    """
    Create a table in the database. with todays date as the name.
    """
    cursor.execute("CREATE TABLE %s (time text, Windowname text, TypeWindow text, window int)" % name)


def check_table(cursor: sqlite3.Cursor, database: sqlite3.Connection, name: str) -> None:
    """
    Check if the table exists in the database.
    """
    try:
        cursor.execute(f'SELECT * FROM {name}')
    except sqlite3.OperationalError:
        create_table(cursor, database, name)

def arange_data(data: Dict[str, Any]) -> Tuple[str, str, int]:
    """
    Arrange the data in the correct format.
    """
    time = datetime.datetime.now().strftime("%H:%M:%S")
    window_name = data['name']
    window_type = data['type']
    window_id = data['id']
    return time, window_name, window_type, window_id


date = datetime.datetime.now().strftime("%Y%m%d")
date = 'day' + date
check_table(c, con, str(date))
print(get_table_name(c, con))

get_window = GetWindow()
# Listen for _NET_ACTIVE_WINDOW changes
get_window.root.change_attributes(event_mask=X.PropertyChangeMask)

# Prime last_seen with whatever window was active when we started this
get_window.get_window_name(get_window.get_active_window()[0])
get_window.handle_change(get_window.last_seen)

while True:  # next_event() sleeps until we get an event
    get_window.handle_xevent(get_window.disp.next_event())
