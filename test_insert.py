import sqlite3

# Connect to the database
conn = sqlite3.connect('scraped_data.db')
cursor = conn.cursor()

# Example data to be inserted
test_url = "https://curaleaf.com/shop/arizona/curaleaf-dispensary-camelback"
test_content = "Example Content"

try:
    query = '''
        INSERT INTO data (url, content) VALUES (?, ?)
    '''
    print(f"Executing SQL: {query}")
    print(f"Data: URL={test_url}, Content={test_content}")
    
    cursor.execute(query, (test_url, test_content))
    print("Data inserted successfully")
except sqlite3.Error as sql_err:
    print(f"SQLite error occurred while executing query: {sql_err}")

# Commit the changes and close the connection
conn.commit()
conn.close()
