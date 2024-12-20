import time
import json
import csv
import ssl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Ensure SSL is enabled
ssl._create_default_https_context = ssl._create_unverified_context

# Setup Selenium WebDriver
options = Options()
options.add_argument("--headless")  # Run in headless mode
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920x1080")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")  # Prevent shared memory issues

try:
    service = Service('path_to_chromedriver')  # Replace with the path to your ChromeDriver
except OSError as e:
    raise RuntimeError(f"Failed to initialize ChromeDriver: {e}")

# Function to initialize the driver
def initialize_driver():
    try:
        return webdriver.Chrome(service=service, options=options)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize WebDriver: {e}")

def authenticate_amazon(driver, email, password):
    """Authenticate to Amazon using the provided credentials."""
    driver.get("https://www.amazon.in/ap/signin")
    
    try:
        # Enter email
        email_input = driver.find_element(By.ID, "ap_email")
        email_input.send_keys(email)
        driver.find_element(By.ID, "continue").click()
        
        # Enter password
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ap_password")))
        password_input = driver.find_element(By.ID, "ap_password")
        password_input.send_keys(password)
        
        driver.find_element(By.ID, "signInSubmit").click()
        
        # Wait for redirection after login
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "nav-logo")))
        print("Login successful.")
    except Exception as e:
        print("Authentication failed:", e)
        driver.quit()
        raise

def scrape_category(driver, category_url):
    """Scrape the best-selling products in a given category."""
    driver.get(category_url)
    
    products = []
    try:
        for page in range(1, 4):  # Adjust the range as needed to scrape up to 1500 products
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "zg-item")))
            product_elements = driver.find_elements(By.CLASS_NAME, "zg-item-immersion")
            
            for product in product_elements:
                try:
                    name = product.find_element(By.CLASS_NAME, "p13n-sc-truncate").text.strip()
                    price = product.find_element(By.CLASS_NAME, "p13n-sc-price").text.strip()
                    discount = product.find_element(By.CLASS_NAME, "a-size-small.a-color-secondary").text.strip()
                    rating = product.find_element(By.CLASS_NAME, "a-icon-alt").text.strip()
                    ship_from = "Amazon"  # Placeholder if not available
                    sold_by = "Amazon"  # Placeholder if not available
                    description = product.find_element(By.CLASS_NAME, "a-size-small.p13n-sc-truncated").text.strip()
                    num_bought = "Not available"  # Placeholder if not available
                    images = [img.get_attribute("src") for img in product.find_elements(By.TAG_NAME, "img")]
                    
                    products.append({
                        "Product Name": name,
                        "Product Price": price,
                        "Sale Discount": discount,
                        "Best Seller Rating": rating,
                        "Ship From": ship_from,
                        "Sold By": sold_by,
                        "Product Description": description,
                        "Number Bought in the Past Month": num_bought,
                        "Category Name": category_url.split('/')[-1],
                        "All Available Images": images
                    })
                except NoSuchElementException:
                    continue
            
            # Navigate to the next page
            try:
                next_button = driver.find_element(By.CLASS_NAME, "a-last")
                next_button.click()
                time.sleep(3)  # Wait for the page to load
            except NoSuchElementException:
                break
    except Exception as e:
        print("Error while scraping category:", e)
    
    return products

def save_to_file(data, file_format="json"):
    """Save the scraped data to a file."""
    if file_format == "json":
        with open("amazon_best_sellers.json", "w") as json_file:
            json.dump(data, json_file, indent=4)
    elif file_format == "csv":
        with open("amazon_best_sellers.csv", "w", newline='', encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    print(f"Data saved to amazon_best_sellers.{file_format}")

def main():
    # Replace with your Amazon credentials
    email = "your_email@example.com"
    password = "your_password"

    try:
        driver = initialize_driver()
        authenticate_amazon(driver, email, password)

        category_urls = [
            "https://www.amazon.in/gp/bestsellers/kitchen/ref=zg_bs_nav_kitchen_0",
            "https://www.amazon.in/gp/bestsellers/shoes/ref=zg_bs_nav_shoes_0",
            "https://www.amazon.in/gp/bestsellers/computers/ref=zg_bs_nav_computers_0",
            "https://www.amazon.in/gp/bestsellers/electronics/ref=zg_bs_nav_electronics_0",
            # Add more categories as needed
        ]

        all_products = []
        for url in category_urls:
            print(f"Scraping category: {url}")
            category_products = scrape_category(driver, url)
            all_products.extend(category_products)

        save_to_file(all_products, file_format="json")  # Change to "csv" if needed

    except Exception as e:
        print(f"An error occurred during execution: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

if _name_ == "_main_":
    main()