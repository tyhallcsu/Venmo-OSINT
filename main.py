#!/usr/bin/env python3
# 
# Venmo-OSINT Tool
# Created by sc1341
# Modified for authentication, verbose logging, and browser automation

import argparse
import random
import os
import json
import logging
from getpass import getpass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from banner import banner
from bs4 import BeautifulSoup
from useragents import user_agents

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class VenmoOSINT:

    def __init__(self, username):
        self.username = username
        self.profile_data = {}
        self.driver = webdriver.Chrome()  # You'll need to have ChromeDriver installed and in your PATH
        self.driver.implicitly_wait(10)
        logging.info(f"Initialized VenmoOSINT with username: {self.username}")

    def login(self, email, password):
        """Log in to Venmo using Selenium"""
        logging.info("Attempting to log in to Venmo")
        login_url = "https://account.venmo.com/login"
        
        self.driver.get(login_url)
        
        try:
            # Wait for email field and enter email
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.send_keys(email)

            # Enter password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(password)

            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Sign In')]")
            login_button.click()

            # Wait for successful login or 2FA prompt
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Welcome to Venmo')]"))
                )
                logging.info("Successfully logged in to Venmo")
                return True
            except TimeoutException:
                logging.warning("2FA or additional verification may be required. Please check the browser window.")
                input("Press Enter after completing 2FA or additional verification...")
                return True

        except Exception as e:
            logging.error(f"An error occurred during login: {str(e)}")
            return False

    def scan_profile(self):
        """Scans the target profile and returns the data"""
        logging.info(f"Starting scan for profile: {self.username}")
        url = f"https://venmo.com/{self.username}"
        self.driver.get(url)

        # Wait for transactions to load
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "single-payment"))
            )
        except TimeoutException:
            logging.warning("No transactions found or page took too long to load.")

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        transactions = soup.find_all("div", attrs={"class":"single-payment content-wrap"})
        logging.info(f"Found {len(transactions)} public transactions")

        if not transactions:
            logging.warning("No transactions found. The profile might be private or the page structure has changed.")

        for i, transaction in enumerate(transactions):
            logging.debug(f"Processing transaction {i+1}")
            send, recv = transaction.find_all("a")
            send, recv = send.getText(), recv.getText()
            message = transaction.find_all("div", attrs={"class":"paymentpage-text m_five_t"})[0].getText()
            date = transaction.find_all("div", attrs={"class":"date"})[0].getText()
            export_message = f"{send} paid {recv}{date} for {message}"
            logging.info(export_message)
            self.profile_data[str(i)] = {"sender": send,
                                         "recipient": recv,
                                         "date": date,
                                         "exportMessage": export_message
                                        }

    def save_data(self, filename: str):
        """Saves the data from the scan into a file"""
        logging.info(f"Attempting to save data to file with base name: {filename}")
        i = 0
        while True:
            file_path = f"{filename}{i}.txt"
            if not os.path.exists(file_path):
                logging.debug(f"Found available filename: {file_path}")
                with open(file_path, "w") as f:
                    json.dump(self.profile_data, f, indent=2)
                logging.info(f"Data saved successfully to {file_path}")
                break
            else:
                logging.debug(f"File {file_path} already exists, trying next index")
                i += 1

    def cleanup(self):
        """Close the browser"""
        self.driver.quit()

def parse_args():
    parser = argparse.ArgumentParser(description="Venmo-OSINT Tool, created by sc1341")
    parser.add_argument("--username", help="Username to scan", required=True)
    parser.add_argument("--filename", help="Output file name", required=True)
    parser.add_argument("--email", help="Your Venmo account email", required=True)
    args = parser.parse_args()
    logging.info(f"Parsed arguments: username={args.username}, filename={args.filename}, email={args.email}")
    return args

def main():
    args = parse_args()
    print(banner)
    logging.info("Starting Venmo-OSINT Tool")
    
    password = getpass("Enter your Venmo password: ")
    
    venmo = VenmoOSINT(args.username)
    try:
        if venmo.login(args.email, password):
            venmo.scan_profile()
            venmo.save_data(args.filename)
            logging.info("Venmo-OSINT Tool execution completed")
        else:
            logging.error("Login failed. Unable to proceed with scanning.")
    finally:
        venmo.cleanup()

if __name__ == "__main__":
    main()
