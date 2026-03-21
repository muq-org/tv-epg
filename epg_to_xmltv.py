import requests
from lxml import etree
import datetime
import json
import os

# --- CONFIGURATION ---
API_URL_TEMPLATE = "https://services.sg101.prd.sctv.ch/catalog/tv/channels/list/(end={end};ids={ids};level=minimal;start={start})"
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,de-CH;q=0.7,de;q=0.6',
    'Authorization': 'Bearer 6ba3e826-7840-4c43-843d-24433b526e26',
    'Content-Type': 'application/json; charset=utf-8',
    'From': 'fd93f6e8-852b-4d77-a381-1f105a735055@services.sg101.prd.sctv.ch',
    'Loading-Disabled': 'true',
    'Origin': 'https://tv.blue.ch',
    'Referer': 'https://tv.blue.ch/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
    'X-Request-ID': '2630df32-7ecc-c0ad-c8a2-c7abb6ea923e_1774084900934',
    'sec-ch-ua': '"Not-A.Brand";v="24", "Chromium";v="146"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
}

# --- FETCH DATA ---
def fetch_epg_data(channel_ids, start, end):
    ids_str = ','.join(channel_ids)
    url = API_URL_TEMPLATE.format(start=start, end=end, ids=ids_str)
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

# --- CONVERT TO XMLTV ---
def to_xmltv(epg_data):
    tv = etree.Element('tv')
    nodes = epg_data.get('Nodes', {}).get('Items', [])
    for channel in nodes:
        if channel.get('Kind') != 'Channel':
            continue
        chan_id = channel.get('Identifier')
        chan_title = channel.get('Content', {}).get('Description', {}).get('Title', f"Channel {chan_id}")
        chan_elem = etree.SubElement(tv, 'channel', id=str(chan_id))
        etree.SubElement(chan_elem, 'display-name').text = chan_title
        # Programs/Broadcasts
        broadcasts = channel.get('Content', {}).get('Nodes', {}).get('Items', [])
        for prog in broadcasts:
            if prog.get('Kind') != 'Broadcast':
                continue
            prog_content = prog.get('Content', {})
            desc = prog_content.get('Description', {})
            title = desc.get('Title', 'No Title')
            subtitle = desc.get('Subtitle', '')
            # Find start/stop times from Availabilities
            avails = prog.get('Availabilities', [])
            if not avails:
                continue
            start = avails[0].get('AvailabilityStart')
            stop = avails[0].get('AvailabilityEnd')
            if not start or not stop:
                continue
            prog_elem = etree.SubElement(tv, 'programme', {
                'start': format_xmltv_time(start),
                'stop': format_xmltv_time(stop),
                'channel': str(chan_id)
            })
            etree.SubElement(prog_elem, 'title').text = title
            if subtitle:
                etree.SubElement(prog_elem, 'sub-title').text = subtitle
            # Optionally add more fields (desc, etc.)
    return etree.tostring(tv, pretty_print=True, xml_declaration=True, encoding='UTF-8')

def format_xmltv_time(dt_str):
    # expects ISO8601, returns XMLTV format: YYYYMMDDHHMMSS + 00 offset
    dt = datetime.datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    return dt.strftime('%Y%m%d%H%M%S +0000')

# --- MAIN ---
def main():
    # Load selected channel IDs
    if not os.path.exists('selected_channel_ids.json'):
        raise RuntimeError("selected_channel_ids.json not found. Run extract_selected_channel_ids.py first.")
    with open('selected_channel_ids.json') as f:
        channel_ids = json.load(f)
    # Set time window (example: next 24h from now)
    import datetime as dt
    now = dt.datetime.utcnow()
    start = now.strftime('%Y%m%d%H%M')
    end = (now + dt.timedelta(days=1)).strftime('%Y%m%d%H%M')
    print(f"Requesting EPG for {len(channel_ids)} channels from {start} to {end}")
    epg_data = fetch_epg_data(channel_ids, start, end)
    xmltv = to_xmltv(epg_data)
    with open('epg.xml', 'wb') as f:
        f.write(xmltv)
    print("EPG XMLTV data written to epg.xml")

if __name__ == "__main__":
    main()
