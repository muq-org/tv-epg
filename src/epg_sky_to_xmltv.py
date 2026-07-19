import requests
from lxml import etree
import datetime
from zoneinfo import ZoneInfo
from xmltv_utils import slugify, ms_to_xmltv_time, write_xmltv

# Sky retired the public sky.de web TV guide in July 2026. This scraper uses
# the Sky Q set-top-box cloud EPG instead, which serves the same data to the
# boxes themselves. Bouquet 4 / subbouquet 0 is the German satellite lineup.
SERVICES_URL = "https://atlantis.epgsky.com/as/services/4/0"
SCHEDULE_URL = "https://awk.epgsky.com/hawk/linear/schedule/{date}/{sids}"
IMAGE_PARAMS = "territory=DE&provider=SKY&proposition=SKYQ"
LOGO_URL = f"https://de.imageservice.sky.com/logo/skychb_{{sid}}{{name}}/600/600?{IMAGE_PARAMS}"
PROGRAMME_IMAGE_URL = f"https://de.imageservice.sky.com/pd-image/{{uuid}}/16-9/1024?{IMAGE_PARAMS}"
BATCH_SIZE = 20

HEADERS = {
    'accept': 'application/json',
    'x-skyott-territory': 'DE',
    'x-skyott-provider': 'SKY',
    'x-skyott-proposition': 'SKYQ',
}


def fetch_channels() -> list:
    resp = requests.get(SERVICES_URL, headers=HEADERS)
    resp.raise_for_status()
    return [s for s in resp.json()['services'] if s.get('schedule')]


def fetch_broadcasts(sids: list, date: datetime.date) -> dict:
    events_by_sid = {}
    for i in range(0, len(sids), BATCH_SIZE):
        batch = sids[i:i + BATCH_SIZE]
        url = SCHEDULE_URL.format(date=date.strftime('%Y%m%d'), sids=','.join(batch))
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        for ch in resp.json()['schedule']:
            events_by_sid.setdefault(ch['sid'], []).extend(ch.get('events', []))
    return events_by_sid


def channel_logo_url(sid: str, name: str) -> str:
    # The image service keys logos on sid + the casefolded alphanumeric name,
    # e.g. skychb_142skyshowcasehd.
    slug = ''.join(c for c in name.casefold() if c.isalnum())
    return LOGO_URL.format(sid=sid, name=slug)


def to_xmltv(channels: list, events_by_sid: dict):
    tv = etree.Element('tv')

    # Slugified names can collide (e.g. SD/HD variants); first occurrence wins,
    # and the services list is ordered by channel number so the main lineup
    # takes priority.
    epg_id_map = {}
    for ch in channels:
        sid = ch['sid']
        epg_id = f"{slugify(ch['t'])}.de"
        if epg_id in epg_id_map.values():
            continue
        epg_id_map[sid] = epg_id
        chan_elem = etree.SubElement(tv, 'channel', id=epg_id, **{'api-id': str(sid)})
        etree.SubElement(chan_elem, 'display-name').text = ch['t']
        etree.SubElement(chan_elem, 'icon', src=channel_logo_url(sid, ch['t']))

    seen = set()
    for ch in channels:
        sid = ch['sid']
        if sid not in epg_id_map:
            continue
        epg_id = epg_id_map[sid]
        for ev in events_by_sid.get(sid, []):
            eid = ev.get('eid')
            if (sid, eid) in seen or not ev.get('t') or 'st' not in ev or 'd' not in ev:
                continue
            seen.add((sid, eid))
            start_ms = ev['st'] * 1000
            stop_ms = (ev['st'] + ev['d']) * 1000
            prog_elem = etree.SubElement(tv, 'programme', {
                'start': ms_to_xmltv_time(start_ms),
                'stop': ms_to_xmltv_time(stop_ms),
                'channel': epg_id,
                'api-channel-id': str(sid),
            })
            etree.SubElement(prog_elem, 'title').text = ev['t']
            if ev.get('sy'):
                etree.SubElement(prog_elem, 'desc').text = ev['sy']
            sn, en = ev.get('seasonnumber'), ev.get('episodenumber')
            if sn and en:
                ep_num = etree.SubElement(prog_elem, 'episode-num', system='xmltv_ns')
                ep_num.text = f'{sn - 1}.{en - 1}.'
            if ev.get('programmeuuid'):
                icon_url = PROGRAMME_IMAGE_URL.format(uuid=ev['programmeuuid'])
                etree.SubElement(prog_elem, 'icon', src=icon_url)

    return tv


def main():
    berlin = ZoneInfo('Europe/Berlin')
    today = datetime.datetime.now(tz=berlin).date()

    print("Fetching Sky Q channel list...")
    channels = fetch_channels()
    sids = [ch['sid'] for ch in channels]
    print(f"Found {len(sids)} channels")

    events_by_sid: dict = {}
    for day_offset in range(3):
        day = today + datetime.timedelta(days=day_offset)
        print(f"Fetching broadcasts for {day}...")
        day_data = fetch_broadcasts(sids, day)
        for sid, events in day_data.items():
            events_by_sid.setdefault(sid, []).extend(events)

    tv = to_xmltv(channels, events_by_sid)
    write_xmltv(tv, 'epg_sky.xml')
    print("Sky EPG XMLTV data written to epg_sky.xml")


if __name__ == "__main__":
    main()
