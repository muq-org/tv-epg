import uuid
import requests
from lxml import etree
from xmltv_utils import slugify, format_xmltv_time, write_xmltv

API_URL = "https://rail-router.discovery.indazn.com/eu/v10/Rail?platform=web&id=Livetvschedule&country=de&brand=dazn&languageCode=de"
IMAGE_BASE = "https://image.discovery.indazn.com/eu/v3"
LOGO_SUFFIX = "contain/center/center/none/80/136/112/png/image?brand=dazn"
PROG_SUFFIX = "fill/center/center/none/80/2160/1000/webp/image?brand=dazn"


def logo_url(image_id: str) -> str:
    return f"{IMAGE_BASE}/linear-channel/none/{image_id}/{LOGO_SUFFIX}"


def prog_url(image_id: str) -> str:
    return f"{IMAGE_BASE}/linear-channel/none/{image_id}/{PROG_SUFFIX}"


def fetch_tiles() -> list:
    headers = {
        'sec-ch-ua-platform': '"macOS"',
        'Referer': 'https://www.dazn.com/',
        'sec-ch-ua': '"Not/A)Brand";v="99", "Chromium";v="148"',
        'sec-ch-ua-mobile': '?0',
        'X-BRAND': 'dazn',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
        'x-session-id': str(uuid.uuid4()),
    }
    resp = requests.get(API_URL, headers=headers)
    resp.raise_for_status()
    return resp.json().get('Tiles', [])


def to_xmltv(tiles: list):
    tv = etree.Element('tv')

    for tile in tiles:
        schedule = tile.get('LinearSchedule')
        if not schedule:
            continue

        title = tile.get('Title', '')
        asset_id = tile.get('AssetId', '')
        epg_id = f"{slugify(title)}.de"

        chan_elem = etree.SubElement(tv, 'channel', id=epg_id, **{'api-id': asset_id})
        etree.SubElement(chan_elem, 'display-name').text = title
        logo = tile.get('LogoImage') or {}
        if logo.get('Id'):
            etree.SubElement(chan_elem, 'icon', src=logo_url(logo['Id']))

        programmes = []
        if schedule.get('Now'):
            programmes.append(schedule['Now'])
        if schedule.get('Next'):
            programmes.append(schedule['Next'])
        programmes.extend(schedule.get('Later') or [])

        for prog in programmes:
            start = prog.get('Start')
            end = prog.get('End')
            if not start or not end:
                continue
            prog_elem = etree.SubElement(tv, 'programme', {
                'start': format_xmltv_time(start),
                'stop': format_xmltv_time(end),
                'channel': epg_id,
                'api-channel-id': asset_id,
            })
            etree.SubElement(prog_elem, 'title').text = prog.get('Title', '')
            episode_title = prog.get('EpisodeTitle', '')
            if episode_title and episode_title != prog.get('Title'):
                etree.SubElement(prog_elem, 'sub-title').text = episode_title
            genres = prog.get('Genre') or []
            if genres and genres[0].get('name'):
                etree.SubElement(prog_elem, 'category').text = genres[0]['name']
            image = prog.get('BackgroundImage') or {}
            if image.get('Id'):
                etree.SubElement(prog_elem, 'icon', src=prog_url(image['Id']))

    return tv


def main():
    print("Fetching DAZN channel schedule...")
    tiles = fetch_tiles()
    print(f"Found {len(tiles)} tiles")
    tv = to_xmltv(tiles)
    channels = len(tv.findall('channel'))
    programmes = len(tv.findall('programme'))
    print(f"Writing {channels} channels, {programmes} programmes")
    write_xmltv(tv, 'epg_dazn.xml')
    print("DAZN EPG XMLTV data written to epg_dazn.xml")


if __name__ == "__main__":
    main()
