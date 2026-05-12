import re
import datetime
from lxml import etree


def slugify(name: str) -> str:
    s = name.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')


def format_xmltv_time(iso_str: str) -> str:
    dt = datetime.datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    return dt.strftime('%Y%m%d%H%M%S +0000')


def ms_to_xmltv_time(epoch_ms: int) -> str:
    dt = datetime.datetime.fromtimestamp(epoch_ms / 1000, tz=datetime.timezone.utc)
    return dt.strftime('%Y%m%d%H%M%S +0000')


def write_xmltv(tv_element, path: str) -> None:
    with open(path, 'wb') as f:
        f.write(etree.tostring(tv_element, pretty_print=True, xml_declaration=True, encoding='UTF-8'))
