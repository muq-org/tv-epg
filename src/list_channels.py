import requests
import json

CHANNELS_URL = "https://services.sg101.prd.sctv.ch/portfolio/tv/channels"
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Origin': 'https://tv.blue.ch',
    'Referer': 'https://tv.blue.ch/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
}

def fetch_channels():
    resp = requests.get(CHANNELS_URL, headers=HEADERS)
    resp.raise_for_status()
    channels = resp.json()  # This is a list
    overview = []
    for ch in channels:
        ch_id = ch.get('Identifier')
        ch_name = ch.get('Title', '')
        overview.append({'id': ch_id, 'name': ch_name})
    return overview

def main():
    channels = fetch_channels()
    print(f"Found {len(channels)} channels:")
    for ch in channels:
        print(f"{ch['id']}: {ch['name']}")
    with open('config/all_channels.json', 'w') as f:
        json.dump(channels, f, indent=2, ensure_ascii=False)
    print("Channel overview saved to config/all_channels.json")

if __name__ == "__main__":
    main()
