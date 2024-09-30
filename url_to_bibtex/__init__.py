import requests
import sys

def main():
    if len(sys.argv) != 2:
        print("Usage: python urls_to_bibtex.py input_urls.txt")
        sys.exit(1)

    input_file = sys.argv[1]

    # Read URLs from the input file
    with open(input_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    bibtex_entries = []

    for url in urls:
        # Send POST request to the translation server
        try:
            response = requests.post(
                'http://127.0.0.1:1969/web',
                data=url.encode('utf-8'),
                headers={'Content-Type': 'text/plain', 'Accept': 'application/x-bibtex'}
            )
            response.raise_for_status()  # Check for HTTP errors
            bibtex_entries.append(response.text)
        except requests.exceptions.RequestException as e:
            print(f"Error processing URL {url}: {e}", file=sys.stderr)

    # Output the BibTeX entries
    print('\n\n'.join(bibtex_entries))

if __name__ == '__main__':
    main()

