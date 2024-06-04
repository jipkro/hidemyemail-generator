from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Define the URL
url = "https://www.icloud.com/settings/"

# Set up the Selenium WebDriver (using Chrome in this example)
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

try:
    # Open the URL
    driver.get(url)

    # Wait for the page to load completely again
    time.sleep(60)  # Adjust this as needed for your network speed

    # Get the cookies
    cookies = driver.get_cookies()
    
    # Format the cookies as semicolon-separated name=value pairs
    cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
    
    # Print the formatted cookies string
    print(cookie_string)

finally:
    # Close the WebDriver
    driver.quit()