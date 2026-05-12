import pytest
from lxml import etree
from epg_sky_to_xmltv import fetch_channels, fetch_broadcasts, to_xmltv
import datetime


# --- Fixtures ---

SAMPLE_CHANNELS = [
    {'ci': 1, 'cn': 'Sky Atlantic HD', 'clu': '/static/img/logo1.png', 'cu': '/tvguide/sky-atlantic'},
    {'ci': 2, 'cn': 'Sky One HD', 'clu': '/static/img/logo2.png', 'cu': '/tvguide/sky-one'},
]

SAMPLE_BROADCASTS = {
    1: [
        {
            'ei': 100, 'bsdt': 1778538300000, 'bedt': 1778540700000,
            'et': 'Succession', 'epit': 'Rehearsal', 'sn': '3', 'en': '1',
            'ec': 'Drama', 'pu': '/static/img/prog100.jpg',
        },
        {
            'ei': 101, 'bsdt': 1778540700000, 'bedt': 1778543700000,
            'et': 'The Wire', 'epit': 'The Wire', 'sn': '1', 'en': '1',
            'ec': 'Crime', 'pu': '/static/img/prog101.jpg',
        },
    ],
    2: [
        {
            'ei': 200, 'bsdt': 1778538300000, 'bedt': 1778541900000,
            'et': 'Movie Night', 'epit': '', 'sn': '', 'en': '',
            'ec': 'Film', 'pu': '',
        },
    ],
}


# --- Unit tests ---

class TestToXmltvStructure:
    def setup_method(self):
        self.tv = to_xmltv(SAMPLE_CHANNELS, SAMPLE_BROADCASTS)

    def test_returns_element(self):
        assert self.tv.tag == 'tv'

    def test_channel_count(self):
        channels = self.tv.findall('channel')
        assert len(channels) == 2

    def test_channel_epg_ids(self):
        ids = [ch.get('id') for ch in self.tv.findall('channel')]
        assert 'sky-atlantic-hd.de' in ids
        assert 'sky-one-hd.de' in ids

    def test_channel_has_display_name(self):
        ch = self.tv.find("channel[@id='sky-atlantic-hd.de']")
        assert ch.find('display-name').text == 'Sky Atlantic HD'

    def test_channel_has_icon(self):
        ch = self.tv.find("channel[@id='sky-atlantic-hd.de']")
        icon = ch.find('icon')
        assert icon is not None
        assert icon.get('src') == 'https://www.sky.de/static/img/logo1.png'

    def test_programme_count(self):
        programmes = self.tv.findall('programme')
        assert len(programmes) == 3

    def test_programme_times(self):
        prog = self.tv.find("programme[@channel='sky-atlantic-hd.de']")
        assert prog.get('start') == '20260511222500 +0000'
        assert prog.get('stop') == '20260511230500 +0000'

    def test_programme_title(self):
        prog = self.tv.find("programme[@channel='sky-atlantic-hd.de']")
        assert prog.find('title').text == 'Succession'

    def test_sub_title_emitted_when_different(self):
        prog = self.tv.find("programme[@channel='sky-atlantic-hd.de']")
        assert prog.find('sub-title').text == 'Rehearsal'

    def test_sub_title_omitted_when_same_as_title(self):
        # The Wire episode has epit == et
        progs = self.tv.findall("programme[@channel='sky-atlantic-hd.de']")
        the_wire = next(p for p in progs if p.find('title').text == 'The Wire')
        assert the_wire.find('sub-title') is None

    def test_episode_num_0_indexed(self):
        prog = self.tv.find("programme[@channel='sky-atlantic-hd.de']")
        ep_num = prog.find("episode-num[@system='xmltv_ns']")
        assert ep_num.text == '2.0.'  # season 3 → 2, episode 1 → 0

    def test_category(self):
        prog = self.tv.find("programme[@channel='sky-atlantic-hd.de']")
        assert prog.find('category').text == 'Drama'

    def test_programme_icon(self):
        prog = self.tv.find("programme[@channel='sky-atlantic-hd.de']")
        icon = prog.find('icon')
        assert icon.get('src') == 'https://www.sky.de/static/img/prog100.jpg'

    def test_icon_omitted_when_no_pu(self):
        prog = self.tv.find("programme[@channel='sky-one-hd.de']")
        assert prog.find('icon') is None

    def test_episode_num_omitted_when_no_sn_en(self):
        prog = self.tv.find("programme[@channel='sky-one-hd.de']")
        assert prog.find("episode-num") is None


class TestToXmltvDeduplication:
    def test_duplicate_ei_dropped(self):
        broadcasts = {
            1: [
                {'ei': 999, 'bsdt': 1778538300000, 'bedt': 1778540700000,
                 'et': 'Show', 'epit': 'Ep1', 'sn': '1', 'en': '1', 'ec': 'Drama', 'pu': ''},
                {'ei': 999, 'bsdt': 1778538300000, 'bedt': 1778540700000,
                 'et': 'Show', 'epit': 'Ep1', 'sn': '1', 'en': '1', 'ec': 'Drama', 'pu': ''},
            ],
        }
        tv = to_xmltv([{'ci': 1, 'cn': 'Sky Atlantic HD', 'clu': '', 'cu': ''}], broadcasts)
        assert len(tv.findall('programme')) == 1


# --- Integration tests ---

@pytest.mark.integration
class TestSkyApiClient:
    def test_fetch_channels_returns_channels(self):
        channels = fetch_channels()
        assert len(channels) >= 10
        for ch in channels:
            assert isinstance(ch['ci'], int)
            assert isinstance(ch['cn'], str) and ch['cn']

    def test_fetch_broadcasts_returns_data(self):
        from zoneinfo import ZoneInfo
        berlin = ZoneInfo('Europe/Berlin')
        now = datetime.datetime.now(tz=berlin)
        today = datetime.datetime(now.year, now.month, now.day, tzinfo=berlin)
        date_ms = int(today.timestamp() * 1000)

        # Use a small subset of known channel IDs
        result = fetch_broadcasts([1019, 535, 2], date_ms)

        assert isinstance(result, dict)
        assert len(result) > 0
        for ci, episodes in result.items():
            assert isinstance(ci, int)
            assert len(episodes) > 0
            for ep in episodes:
                assert 'bsdt' in ep
                assert 'bedt' in ep
                assert 'et' in ep
