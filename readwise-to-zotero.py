#!/usr/bin/env python3

import requests
import os
import sys

# Retrieve credentials from environment variables
READWISE_API_TOKEN = os.getenv('READWISE_API_TOKEN')
ZOTERO_API_KEY = os.getenv('ZOTERO_API_KEY')
ZOTERO_USER_ID = os.getenv('ZOTERO_USER_ID')

if not all([READWISE_API_TOKEN, ZOTERO_API_KEY, ZOTERO_USER_ID]):
    print("Please set the READWISE_API_TOKEN, ZOTERO_API_KEY, and ZOTERO_USER_ID environment variables.")
    sys.exit(1)

# API URLs
ZOTERO_API_URL = f"https://api.zotero.org/users/{ZOTERO_USER_ID}/items"
READWISE_API_URL = "https://readwise.io/api/v2/highlights/"
TRANSLATION_SERVER_URL = "http://127.0.0.1:1969/web"

# Headers for Zotero and Readwise API
headers_zotero = {
    'Authorization': f'Bearer {ZOTERO_API_KEY}',
    'Content-Type': 'application/json',
    'Zotero-API-Version': '3',
}

headers_readwise = {
    'Authorization': f'Token {READWISE_API_TOKEN}',
}

# Fetch data from Readwise API
def fetch_readwise_data():
    highlights = []
    next_url = READWISE_API_URL
    while next_url:
        response = requests.get(next_url, headers=headers_readwise)
        if response.status_code == 200:
            data = response.json()
            highlights.extend(data['results'])
            next_url = data['next']
        else:
            print(f"Failed to fetch Readwise data: {response.status_code}")
            return []
    return highlights

# Fetch existing Zotero items to check for duplicates
def fetch_zotero_items():
    items = []
    start = 0
    limit = 100
    while True:
        params = {'start': start, 'limit': limit}
        response = requests.get(ZOTERO_API_URL, headers=headers_zotero, params=params)
        if response.status_code == 200:
            batch = response.json()
            if not batch:
                break
            items.extend(batch)
            start += limit
        else:
            print(f"Failed to fetch Zotero data: {response.status_code}")
            break
    return items

# Check if a Zotero item already exists (by URL)
def item_exists_in_zotero(zotero_items, url):
    for item in zotero_items:
        if 'url' in item['data'] and item['data']['url'] == url:
            return True
    return False

# Use Zotero Translation Server to fetch metadata from URL
def fetch_metadata_from_url(url):
    headers = {'Content-Type': 'text/plain'}
    response = requests.post(TRANSLATION_SERVER_URL, headers=headers, data=url)
    if response.status_code == 200:
        metadata = response.json()
        if metadata:
            return metadata[0]
    return None

# Add item to Zotero library
def add_item_to_zotero(item_data):
    response = requests.post(ZOTERO_API_URL, headers=headers_zotero, json=[item_data])
    if response.status_code in (200, 201):
        print(f"Successfully added item to Zotero: {item_data.get('title', 'No Title')}")
    else:
        print(f"Error adding item to Zotero: {response.content}")

# Main logic to process Readwise highlights and add them to Zotero
def main():
    # Fetch Readwise highlights
    readwise_highlights = fetch_readwise_data()

    # Extract unique URLs from Readwise data
    urls = set()
    for highlight in readwise_highlights:
        source_url = highlight.get('source_url')
        if source_url:
            urls.add(source_url)

    if not urls:
        print("No URLs found in Readwise data.")
        return

    # Fetch existing Zotero items to check for duplicates
    zotero_items = fetch_zotero_items()

    # Process each URL
    for url in urls:
        if not item_exists_in_zotero(zotero_items, url):
            print(f"Fetching metadata for URL: {url}")
            metadata = fetch_metadata_from_url(url)
            if metadata:
                # Add the URL to the item data (in case it's missing)
                metadata['url'] = url
                # Add item to Zotero
                add_item_to_zotero(metadata)
            else:
                print(f"Could not retrieve metadata for URL: {url}")
        else:
            print(f"Item with URL {url} already exists in Zotero.")

if __name__ == "__main__":
    main()

