import requests
from lxml import etree
import datetime
import json
import os

# --- CONFIGURATION ---
API_URL_TEMPLATE = "https://services.sg101.prd.sctv.ch/catalog/tv/channels/list/(end={end};ids={ids};level=minimal;start={start})"
HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Origin': 'https://tv.blue.ch',
    'Referer': 'https://tv.blue.ch/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
}

# --- FETCH DATA ---
def fetch_epg_data(channel_ids, start, end):
    ids_str = ','.join(channel_ids)
    url = API_URL_TEMPLATE.format(start=start, end=end, ids=ids_str)
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

# --- CONVERT TO XMLTV ---
def to_xmltv(epg_data, epg_id_map):
    tv = etree.Element('tv')
    nodes = epg_data.get('Nodes', {}).get('Items', [])
    for channel in nodes:
        if channel.get('Kind') != 'Channel':
            continue
        chan_id = channel.get('Identifier')
        chan_title = channel.get('Content', {}).get('Description', {}).get('Title', f"Channel {chan_id}")
        epg_id = epg_id_map.get(str(chan_id), f"{chan_title}.ch")
        chan_elem = etree.SubElement(tv, 'channel', id=epg_id, **{'api-id': str(chan_id)})
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
                'channel': epg_id,
                'api-channel-id': str(chan_id)
            })
            etree.SubElement(prog_elem, 'title').text = title
            if subtitle:
                etree.SubElement(prog_elem, 'sub-title').text = subtitle
            # Add <icon> for programme image if available
            images = prog_content.get('Nodes', {}).get('Items', [])
            image_url = None
            # Prefer 'Lane' image, else first image
            for img in images:
                if img.get('Kind') == 'Image' and img.get('Role') == 'Lane' and img.get('ContentPath'):
                    image_url = f"https://services.sg101.prd.sctv.ch/content/images/{img['ContentPath']}_w1920.webp"
                    break
            if not image_url:
                for img in images:
                    if img.get('Kind') == 'Image' and img.get('ContentPath'):
                        image_url = f"https://services.sg101.prd.sctv.ch/content/images/{img['ContentPath']}_w1920.webp"
                        break
            if image_url:
                etree.SubElement(prog_elem, 'icon', {'src': image_url})
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
        channel_data = json.load(f)
        channel_ids = [c['api-id'] for c in channel_data]
        epg_id_map = {c['api-id']: c['epg-id'] for c in channel_data}
    # Set time window (example: next 24h from now)
    import datetime as dt
    now = dt.datetime.utcnow()
    start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = start_dt + dt.timedelta(days=2)
    # Split into 1-day intervals
    all_epg_nodes = []
    interval = dt.timedelta(days=1)
    interval_start = start_dt
    while interval_start < end_dt:
        interval_end = min(interval_start + interval, end_dt)
        start_str = interval_start.strftime('%Y%m%d%H%M')
        end_str = interval_end.strftime('%Y%m%d%H%M')
        print(f"Requesting EPG for {len(channel_ids)} channels from {start_str} to {end_str}")
        epg_data = fetch_epg_data(channel_ids, start_str, end_str)
        # Extract channel nodes and append
        nodes = epg_data.get('Nodes', {}).get('Items', [])
        all_epg_nodes.extend(nodes)
        interval_start = interval_end
    # Merge all nodes into a single epg_data structure
    merged_epg_data = {'Nodes': {'Items': all_epg_nodes}}
    xmltv = to_xmltv(merged_epg_data, epg_id_map)
    with open('epg.xml', 'wb') as f:
        f.write(xmltv)
    print("EPG XMLTV data written to epg.xml")

if __name__ == "__main__":
    main()
