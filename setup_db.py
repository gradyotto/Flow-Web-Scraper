import sqlite3

# Connect to the database (or create it if it doesn't exist)
conn = sqlite3.connect('scraped_data.db')

# Create a cursos object to interact with the database
cursor = conn.cursor()

# Create a table to store the scraped data
cursor.execute('''
    CREATE TABLE IF NOT EXISTS data (
               id INTEGER PRIMARY KEY,
               url TEXT,
               content TEXT
               )
''')

# Commit the changes and close the connection
conn.commit()
conn.close()
