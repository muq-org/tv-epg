import requests
import json

CHANNELS_URL = "https://services.sg101.prd.sctv.ch/portfolio/tv/channels"
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,de-CH;q=0.7,de;q=0.6',
    'Authorization': 'Bearer 96473175-6e7e-4849-ab3e-f8876461909d',
    'Cache-Control': 'no-cache, no-store',
    'Content-Type': 'application/json; charset=utf-8',
    'From': '348d50d0-a83a-4921-aa7a-4af7681ee617@services.sg101.prd.sctv.ch',
    'Origin': 'https://tv.blue.ch',
    'Referer': 'https://tv.blue.ch/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'X-Request-ID': '664775e4-0df6-86ea-3780-1058981cbd15_1774085531147',
    'sec-ch-ua': '"Not-A.Brand";v="24", "Chromium";v="146"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
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
    with open('all_channels.json', 'w') as f:
        json.dump(channels, f, indent=2, ensure_ascii=False)
    print("Channel overview saved to all_channels.json")

if __name__ == "__main__":
    main()
