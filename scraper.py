from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.firefox import GeckoDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import sqlite3

# List of URLs to scrape
urls = [
    "https://curaleaf.com/shop/arizona/curaleaf-dispensary-camelback",
    "https://curaleaf.com/shop/arizona/curaleaf-dispensary-midtown",
    "https://curaleaf.com/shop/arizona/curaleaf-dispensary-central",
    # Add more URLs here
]

# Set up Selenium WebDriver with GeckoDriver
driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
actions = ActionChains(driver)

# Connect to the database
conn = sqlite3.connect('scraped_data.db')
cursor = conn.cursor()

# Clear the database
cursor.execute('DELETE FROM data')
conn.commit()
print("All data has been cleared from the database.")

# Check if the necessary columns exist and add them if not
cursor.execute("PRAGMA table_info(data)")
columns = cursor.fetchall()
existing_columns = [column[1] for column in columns]

required_columns = ['date', 'old_price', 'new_price', 'current_price', 'category', 'deal']
for col in required_columns:
    if col not in existing_columns:
        cursor.execute(f'ALTER TABLE data ADD COLUMN {col} TEXT')
        conn.commit()
        print(f"{col.capitalize()} column has been added to the database.")

first_url = True
date_today = datetime.now().strftime('%Y-%m-%d')

for url in urls:
    try:
        print(f"Scraping URL: {url}")
        driver.get(url)

        if first_url:
            # Wait for the dropdown trigger to be clickable and click it
            try:
                dropdown_trigger = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'p-dropdown-trigger'))
                )
                dropdown_trigger.click()
            except Exception as e:
                print(f"Dropdown trigger not found or not clickable on {url}: {e}")
                first_url = False
                continue

            # Wait for the dropdown options to be visible
            try:
                dropdown_options = WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, 'p-dropdown-item'))
                )
            except Exception as e:
                print(f"Dropdown options not found or not visible on {url}: {e}")
                first_url = False
                continue

            # Select the state option by visible text
            try:
                state_option = driver.find_element(By.XPATH, "//li[text()='Arizona']")
                state_option.click()
            except Exception as e:
                print(f"State option 'Arizona' not found on {url}: {e}")
                first_url = False
                continue

            # Wait for the age verification button to be clickable and click it
            try:
                age_verification_button = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='submit']"))
                )
                age_verification_button.click()
            except Exception as e:
                print(f"Age verification button not found or not clickable on {url}: {e}")
                first_url = False
                continue

            # Handle additional pop-up if it appears
            try:
                popup_close_button = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'mailingOptIn_close__VO7xF'))
                )
                popup_close_button.click()
            except Exception as e:
                print(f"No additional pop-up found or clickable on {url}: {e}")

            first_url = False

        # Increase wait time to ensure the page loads completely
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        # Get the page source and parse with BeautifulSoup
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Scrape specific elements
        products = []
        product_names = soup.find_all('h2', class_='product-name text-color-primary margin-0 tbody16-bold')
        for product in product_names:
            product_data = {}
            product_data['name'] = product.text.strip()
            product_container = product.find_parent()

            old_price = product_container.find('span', class_='old-price strikethrough margin-left-5 tbody16-bold text-color-grey')
            new_price = product_container.find('span', class_='new-price tbody16-bold text-color-error')
            current_price = product_container.find('span', class_='current-price tbody16-bold text-color-primary')

            category_section = soup.find('h2', class_='title text-primary margin-0')
            category = category_section.find_next('h2', class_='title text-primary margin-0') if category_section else None

            product_data['old_price'] = old_price.text.strip() if old_price else '0'
            product_data['new_price'] = new_price.text.strip() if new_price else '0'
            product_data['current_price'] = current_price.text.strip() if current_price else '0'
            product_data['category'] = category.text.strip() if category else 'Unknown'

            # Determine if it's a deal
            product_data['deal'] = 'True' if float(product_data['current_price'].replace('$', '').replace(',', '')) == 0 else 'False'

            products.append(product_data)

        for product in products:
            print(f"Scraped Product: {product}")

            # Construct the content for database insertion
            content = f"Name: {product.get('name', '')}, Old Price: {product.get('old_price', '')}, New Price: {product.get('new_price', '')}, Current Price: {product.get('current_price', '')}, Category: {product.get('category', '')}, Deal: {product.get('deal', '')}"

            if content:  # Only insert if content is not empty
                query = '''
                    INSERT INTO data (url, content, date, old_price, new_price, current_price, category, deal) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                '''
                # Log the query and data
                print(f"Executing SQL: {query}")
                print(f"Data: URL={url}, Content={content}, Date={date_today}, Old Price={product.get('old_price', '')}, New Price={product.get('new_price', '')}, Current Price={product.get('current_price', '')}, Category={product.get('category', '')}, Deal={product.get('deal', '')}")

                try:
                    # Log data separately to isolate the issue
                    print(f"Data to be inserted: {url}, {content}, {date_today}, {product.get('old_price', '')}, {product.get('new_price', '')}, {product.get('current_price', '')}, {product.get('category', '')}, {product.get('deal', '')}")
                    cursor.execute(query, (url, content, date_today, product.get('old_price', ''), product.get('new_price', ''), product.get('current_price', ''), product.get('category', ''), product.get('deal', '')))
                    print(f"Data inserted for URL: {url}")
                except sqlite3.Error as sql_err:
                    print(f"SQLite error occurred while executing query: {sql_err}")
            else:
                print(f"Scraped content is empty for URL: {url}")

    except Exception as e:
        print(f"General error occurred while scraping {url}: {e}")

# Commit the changes and close the connection
conn.commit()
conn.close()
print("Scraping and database operations completed.")

# Quit the WebDriver
driver.quit()
