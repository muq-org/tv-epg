import requests
from lxml import etree
import datetime
from zoneinfo import ZoneInfo
from xmltv_utils import slugify, ms_to_xmltv_time, write_xmltv

CHANNEL_LIST_URL = "https://www.sky.de/sgtvg/service/getChannelList"
BROADCASTS_URL = "https://www.sky.de/sgtvg/service/getBroadcastsForGrid"
IMAGE_BASE = "https://www.sky.de"
BATCH_SIZE = 50

HEADERS = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'content-type': 'application/json',
    'origin': 'https://www.sky.de',
    'referer': 'https://www.sky.de/tvguide-7599',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

# The API checks for the presence of JSESSIONID but does not validate its value.
COOKIES = {'JSESSIONID': 'tvepg'}


def fetch_channels() -> list:
    payload = {"dom": "de", "s": 2, "cat": "", "cpck": False, "fav": False, "feed": True, "pck": ""}
    resp = requests.post(CHANNEL_LIST_URL, json=payload, headers=HEADERS, cookies=COOKIES)
    resp.raise_for_status()
    return resp.json()['cl']


def fetch_broadcasts(channel_ids: list, date_ms: int) -> dict:
    episodes_by_ci = {}
    for i in range(0, len(channel_ids), BATCH_SIZE):
        batch = channel_ids[i:i + BATCH_SIZE]
        payload = {"d": date_ms, "cil": batch}
        resp = requests.post(BROADCASTS_URL, json=payload, headers=HEADERS, cookies=COOKIES)
        resp.raise_for_status()
        for ch in resp.json()['cl']:
            ci = ch['ci']
            if ci not in episodes_by_ci:
                episodes_by_ci[ci] = []
            episodes_by_ci[ci].extend(ch.get('el', []))
    return episodes_by_ci


def to_xmltv(channels: list, broadcasts_by_ci: dict):
    epg_id_map = {ch['ci']: f"{slugify(ch['cn'])}.de" for ch in channels}

    tv = etree.Element('tv')

    for ch in channels:
        ci = ch['ci']
        chan_elem = etree.SubElement(tv, 'channel', id=epg_id_map[ci], **{'api-id': str(ci)})
        etree.SubElement(chan_elem, 'display-name').text = ch['cn']
        if ch.get('clu'):
            etree.SubElement(chan_elem, 'icon', src=f"{IMAGE_BASE}{ch['clu']}")

    seen_ei = set()
    for ch in channels:
        ci = ch['ci']
        epg_id = epg_id_map[ci]
        for ep in broadcasts_by_ci.get(ci, []):
            ei = ep['ei']
            if ei in seen_ei or not ep.get('et'):
                continue
            seen_ei.add(ei)
            prog_elem = etree.SubElement(tv, 'programme', {
                'start': ms_to_xmltv_time(ep['bsdt']),
                'stop': ms_to_xmltv_time(ep['bedt']),
                'channel': epg_id,
                'api-channel-id': str(ci),
            })
            etree.SubElement(prog_elem, 'title').text = ep['et']
            epit = ep.get('epit', '')
            if epit and epit != ep['et']:
                etree.SubElement(prog_elem, 'sub-title').text = epit
            sn, en = ep.get('sn'), ep.get('en')
            if sn and en:
                try:
                    ep_num = etree.SubElement(prog_elem, 'episode-num', system='xmltv_ns')
                    ep_num.text = f'{int(sn) - 1}.{int(en) - 1}.'
                except ValueError:
                    pass
            if ep.get('ec'):
                etree.SubElement(prog_elem, 'category').text = ep['ec']
            if ep.get('pu'):
                etree.SubElement(prog_elem, 'icon', src=f"{IMAGE_BASE}{ep['pu']}")

    return tv


def main():
    berlin = ZoneInfo('Europe/Berlin')
    now = datetime.datetime.now(tz=berlin)
    today = datetime.datetime(now.year, now.month, now.day, tzinfo=berlin)

    print("Fetching Sky.de channel list...")
    channels = fetch_channels()
    channel_ids = [ch['ci'] for ch in channels]
    print(f"Found {len(channel_ids)} channels")

    broadcasts_by_ci: dict = {}
    for day_offset in range(2):
        day = today + datetime.timedelta(days=day_offset)
        date_ms = int(day.timestamp() * 1000)
        print(f"Fetching broadcasts for {day.date()}...")
        day_data = fetch_broadcasts(channel_ids, date_ms)
        for ci, episodes in day_data.items():
            if ci not in broadcasts_by_ci:
                broadcasts_by_ci[ci] = []
            broadcasts_by_ci[ci].extend(episodes)

    tv = to_xmltv(channels, broadcasts_by_ci)
    write_xmltv(tv, 'epg_sky.xml')
    print("Sky EPG XMLTV data written to epg_sky.xml")


if __name__ == "__main__":
    main()
