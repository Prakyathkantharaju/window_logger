

# file to verify the data in the table

import sqlite3
import datetime

con = sqlite3.connect('window.db')
c = con.cursor()
date = datetime.datetime.now().strftime("%Y%m%d")
date = 'day' + date
with con:
    c.execute(f"SELECT * FROM {date}")
    rows = c.fetchall()
    for i in rows:
        print(i)
        print('\n')
