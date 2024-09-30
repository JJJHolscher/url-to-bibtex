#!/usr/bin/env python3

import requests
import os
import sys
import argparse
import toml

# Default configuration file path
DEFAULT_CONFIG_PATH = os.path.expanduser('~/.config/readwise_to_zotero/config.toml')

def load_config(args):
    # Initialize configuration dictionary
    config = {}

    # Load from environment variables
    config['readwise_api_token'] = os.getenv('READWISE_API_TOKEN')
    config['zotero_api_key'] = os.getenv('ZOTERO_API_KEY')
    config['zotero_user_id'] = os.getenv('ZOTERO_USER_ID')

    # Load from config file if specified or default exists
    config_path = args.config if args.config else DEFAULT_CONFIG_PATH
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = toml.load(f)
                config.update({k: v for k, v in file_config.items() if v})
        except Exception as e:
            print(f"Error reading config file: {e}")
            sys.exit(1)

    # Override with CLI arguments if provided
    if args.readwise_api_token:
        config['readwise_api_token'] = args.readwise_api_token
    if args.zotero_api_key:
        config['zotero_api_key'] = args.zotero_api_key
    if args.zotero_user_id:
        config['zotero_user_id'] = args.zotero_user_id
    if args.translation_server_url:
        config['translation_server_url'] = args.translation_server_url
    else:
        config['translation_server_url'] = 'http://127.0.0.1:1969/web'

    # Validate required configurations
    required_keys = ['readwise_api_token', 'zotero_api_key', 'zotero_user_id']
    missing_keys = [key for key in required_keys if not config.get(key)]
    if missing_keys:
        print(f"Missing required configuration: {', '.join(missing_keys)}")
        print("Provide them via environment variables, config file, or CLI arguments.")
        sys.exit(1)

    return config

def parse_arguments():
    parser = argparse.ArgumentParser(description='Import Readwise data into Zotero.')
    parser.add_argument('--readwise-api-token', help='Readwise API Token')
    parser.add_argument('--zotero-api-key', help='Zotero API Key')
    parser.add_argument('--zotero-user-id', help='Zotero User ID')
    parser.add_argument('--translation-server-url', help='Translation Server URL')
    parser.add_argument('--config', help='Path to configuration TOML file')
    parser.add_argument('--no-ssl-verify', action='store_true', help='Disable SSL certificate verification')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    return parser.parse_args()

def fetch_readwise_data(config, verify_ssl=True):
    headers = {
        'Authorization': f"Token {config['readwise_api_token']}",
    }
    highlights = []
    next_url = "https://readwise.io/api/v2/highlights/"
    while next_url:
        response = requests.get(next_url, headers=headers, verify=verify_ssl)
        if response.status_code == 200:
            data = response.json()
            highlights.extend(data['results'])
            next_url = data['next']
        else:
            print(f"Failed to fetch Readwise data: {response.status_code}")
            return []
    return highlights

def fetch_zotero_items(config, verify_ssl=True):
    headers = {
        'Authorization': f"Bearer {config['zotero_api_key']}",
        'Zotero-API-Version': '3',
    }
    items = []
    start = 0
    limit = 100
    while True:
        params = {'start': start, 'limit': limit}
        response = requests.get(f"https://api.zotero.org/users/{config['zotero_user_id']}/items", headers=headers, params=params, verify=verify_ssl)
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

def item_exists_in_zotero(zotero_items, url):
    for item in zotero_items:
        if 'url' in item['data'] and item['data']['url'] == url:
            return True
    return False

def fetch_metadata_from_url(url, translation_server_url, verify_ssl=True):
    headers = {'Content-Type': 'text/plain'}
    response = requests.post(translation_server_url, headers=headers, data=url, verify=verify_ssl)
    if response.status_code == 200:
        metadata = response.json()
        if metadata:
            return metadata[0]
    return None

def add_item_to_zotero(config, item_data, verify_ssl=True):
    headers = {
        'Authorization': f"Bearer {config['zotero_api_key']}",
        'Content-Type': 'application/json',
        'Zotero-API-Version': '3',
    }
    response = requests.post(f"https://api.zotero.org/users/{config['zotero_user_id']}/items", headers=headers, json=[item_data], verify=verify_ssl)
    if response.status_code in (200, 201):
        print(f"Successfully added item to Zotero: {item_data.get('title', 'No Title')}")
    else:
        print(f"Error adding item to Zotero: {response.content}")

def main():
    args = parse_arguments()
    config = load_config(args)

    # Handle SSL verification
    verify_ssl = not args.no_ssl_verify

    if args.verbose:
        print("Configuration:")
        for key, value in config.items():
            if 'token' in key.lower() or 'key' in key.lower():
                print(f"{key}: {'*' * 8}")
            else:
                print(f"{key}: {value}")

    # Fetch Readwise highlights
    readwise_highlights = fetch_readwise_data(config, verify_ssl=verify_ssl)

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
    zotero_items = fetch_zotero_items(config, verify_ssl=verify_ssl)

    # Process each URL
    for url in urls:
        if not item_exists_in_zotero(zotero_items, url):
            print(f"Fetching metadata for URL: {url}")
            metadata = fetch_metadata_from_url(url, config['translation_server_url'], verify_ssl=verify_ssl)
            if metadata:
                # Add the URL to the item data (in case it's missing)
                metadata['url'] = url
                # Add item to Zotero
                add_item_to_zotero(config, metadata, verify_ssl=verify_ssl)
            else:
                print(f"Could not retrieve metadata for URL: {url}")
        else:
            print(f"Item with URL {url} already exists in Zotero.")

if __name__ == "__main__":
    main()

