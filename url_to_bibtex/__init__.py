#!/usr/bin/env python3

import sys
import argparse
from pathlib import Path
import re
import requests
from time import sleep

def is_valid_url(s):
    url_regex = re.compile(
        r'^(https?://)'  # http:// or https://
        r'(\w+(\-\w+)*\.)+'  # Domain name
        r'[a-zA-Z]{2,}'  # Top-level domain
        r'(/[^\s]*)?$'  # Optional path
    )
    return re.match(url_regex, s) is not None

def process_file(file):
    items = []
    for line in file:
        line = line.strip()

        # Ignore empty lines or comments
        if not line or line.startswith('#'): continue
        
        # Alternatively, ignore inline comments after a space before '#'
        if ' #' in line:
            line = line.split(' #')[0].strip()

        items += [line]
    return items

def process_arguments(args):
    items = []
    for arg in args:
        if Path(arg).is_file():
            print(f"Processing file: {arg}", file=sys.stderr)
            with open(arg, 'r') as file:
                items += process_file(file)
        else:
            items += [arg]
    return items

def request_metadata(item, item_type):
    # Get metadata from the translation server.
    response = requests.post(
        'http://127.0.0.1:1969/' + item_type,
        data=item.encode('utf-8'),
        headers={'Content-Type': 'text/plain'}
    )
    response.raise_for_status()
    return response.text

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process URLs, DOIs, other identifiers, and file paths.')
    parser.add_argument('inputs', nargs='*', help='URLs, DOIs, other identifiers, or file paths')
    parser.add_argument('-o', '--output', help='Output file to write the results')
    parser.add_argument('-f', '--format', default="bibtex", help='Format to store the results in, defaults to bibtex.')
    parser.add_argument('--hide-failures', action="store_true", help="Don't comment failed items.")

    # This flag is actually handled by the parent shell script.
    parser.add_argument('-v', '--verbose', action="store_true", help="Don't suppress error messages to the stderr.")
    return parser.parse_args()

def main():
    args = parse_arguments()
    if args.inputs:
        items = process_arguments(args.inputs)
    else:
        print("No arguments provided. Reading from standard input...", file=sys.stderr)
        items = process_file(sys.stdin)
    
    if not len(items):
        print("No urls or identifiers found.\nUsage: url-to-bibtex [URLs or IDs]", file=sys.stderr)
        exit(1)

    out = open(args.output, "w") if args.output else sys.stdout
    for item in items:
        sleep(1)
        # Request metadata from the translation server.
        try:
            # Treat the item as a webpage.
            metadata = request_metadata(item, "web")
        except requests.exceptions.RequestException:
            try:
                sleep(1)
                # Try other ways of getting metadata from the item.
                metadata = request_metadata(item, "search")
            except requests.exceptions.RequestException as e:
                print(
                    "translation server could not get metadata for", item,
                    "error:\n", e,
                    file=sys.stderr
                )
                if not args.hide_failures:
                    print(item)
                continue

        # Convert metadata to the supplied format.
        response = requests.post(
            'http://127.0.0.1:1969/export?format=' + args.format,
            data=metadata,
            headers={'Content-Type': 'application/json'}
        )
        print(response.text, file=out)

    if args.output: out.close()

if __name__ == '__main__':
    main()

