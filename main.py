#!/usr/bin/env python3
# 
# Venmo-OSINT Tool
# Created by sc1341
# Modified for verbose logging

import argparse
import random
import requests
import os
import json
import logging

from banner import banner
from bs4 import BeautifulSoup
from useragents import user_agents

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class VenmoOSINT:

    def __init__(self, username):
        self.username = username
        self.profile_data = {}
        logging.info(f"Initialized VenmoOSINT with username: {self.username}")

    def scan_profile(self):
        """Scans the target profile and returns the data"""
        logging.info(f"Starting scan for profile: {self.username}")
        try:
            url = f"https://venmo.com/{self.username}"
            headers = {"User-Agent": random.choice(user_agents)}
            logging.debug(f"Sending GET request to {url}")
            logging.debug(f"Using User-Agent: {headers['User-Agent']}")
            r = requests.get(url, headers=headers)
            logging.debug(f"Received response with status code: {r.status_code}")
        except requests.exceptions.ConnectionError:
            logging.error("Connection error occurred. Check your network connection.")
            return 1

        logging.info("Parsing response with BeautifulSoup")
        soup = BeautifulSoup(r.text, "html.parser")
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
            # assign values in dictionary for output
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

def parse_args():
    parser = argparse.ArgumentParser(description="Venmo-OSINT Tool, created by sc1341")
    parser.add_argument("--username", help="Username", required=True, nargs=1)
    parser.add_argument("--filename", help="Output file name", required=True, nargs=1)
    args = parser.parse_args()
    logging.info(f"Parsed arguments: username={args.username[0]}, filename={args.filename[0]}")
    return args

def main():
    args = parse_args()
    print(banner)
    logging.info("Starting Venmo-OSINT Tool")
    a = VenmoOSINT(args.username[0])
    a.scan_profile()
    a.save_data(args.filename[0])
    logging.info("Venmo-OSINT Tool execution completed")

if __name__ == "__main__":
    main()
