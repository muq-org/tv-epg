import pytest
from lxml import etree
from epg_sky_to_xmltv import fetch_channels, fetch_broadcasts, to_xmltv
import datetime


# --- Fixtures ---

SAMPLE_CHANNELS = [
    {'sid': '110', 'c': '105', 't': 'Sky Atlantic HD', 'sf': 'hd', 'schedule': True},
    {'sid': '142', 'c': '100', 't': 'Sky Showcase HD', 'sf': 'hd', 'schedule': True},
]

SAMPLE_EVENTS = {
    '110': [
        {
            'eid': 'E6e-0001', 'st': 1778538300, 'd': 2400,
            't': 'Succession', 'sy': 'Drama um eine Medienfamilie.',
            'seasonnumber': 3, 'episodenumber': 1,
            'programmeuuid': 'aaaa1111-2222-3333-4444-555566667777',
        },
        {
            'eid': 'E6e-0002', 'st': 1778540700, 'd': 3000,
            't': 'The Wire', 'sy': '',
            'seasonnumber': 0, 'episodenumber': 0,
        },
    ],
    '142': [
        {
            'eid': 'E8e-0001', 'st': 1778538300, 'd': 3600,
            't': 'Movie Night',
        },
    ],
}


# --- Unit tests ---

class TestToXmltvStructure:
    def setup_method(self):
        self.tv = to_xmltv(SAMPLE_CHANNELS, SAMPLE_EVENTS)

    def test_returns_element(self):
        assert self.tv.tag == 'tv'

    def test_channel_count(self):
        channels = self.tv.findall('channel')
        assert len(channels) == 2

    def test_channel_epg_ids(self):
        ids = [ch.get('id') for ch in self.tv.findall('channel')]
        assert 'sky-atlantic-hd.de' in ids
        assert 'sky-showcase-hd.de' in ids

    def test_channel_has_display_name(self):
        ch = self.tv.find("channel[@id='sky-atlantic-hd.de']")
        assert ch.find('display-name').text == 'Sky Atlantic HD'

    def test_channel_has_icon(self):
        ch = self.tv.find("channel[@id='sky-atlantic-hd.de']")
        icon = ch.find('icon')
        assert icon is not None
        assert icon.get('src') == (
            'https://de.imageservice.sky.com/logo/skychb_110skyatlantichd/600/600'
            '?territory=DE&provider=SKY&proposition=SKYQ'
        )

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

    def test_programme_desc(self):
        prog = self.tv.find("programme[@channel='sky-atlantic-hd.de']")
        assert prog.find('desc').text == 'Drama um eine Medienfamilie.'

    def test_desc_omitted_when_no_sy(self):
        prog = self.tv.find("programme[@channel='sky-showcase-hd.de']")
        assert prog.find('desc') is None

    def test_episode_num_0_indexed(self):
        prog = self.tv.find("programme[@channel='sky-atlantic-hd.de']")
        ep_num = prog.find("episode-num[@system='xmltv_ns']")
        assert ep_num.text == '2.0.'  # season 3 → 2, episode 1 → 0

    def test_programme_icon(self):
        prog = self.tv.find("programme[@channel='sky-atlantic-hd.de']")
        icon = prog.find('icon')
        assert icon.get('src') == (
            'https://de.imageservice.sky.com/pd-image/aaaa1111-2222-3333-4444-555566667777'
            '/16-9/1024?territory=DE&provider=SKY&proposition=SKYQ'
        )

    def test_icon_omitted_when_no_programmeuuid(self):
        prog = self.tv.find("programme[@channel='sky-showcase-hd.de']")
        assert prog.find('icon') is None

    def test_episode_num_omitted_when_zero(self):
        # The Wire event has seasonnumber/episodenumber 0 (= not set)
        progs = self.tv.findall("programme[@channel='sky-atlantic-hd.de']")
        the_wire = next(p for p in progs if p.find('title').text == 'The Wire')
        assert the_wire.find('episode-num') is None


class TestToXmltvDeduplication:
    def test_duplicate_eid_dropped(self):
        events = {
            '110': [
                {'eid': 'E-dup', 'st': 1778538300, 'd': 2400, 't': 'Show'},
                {'eid': 'E-dup', 'st': 1778538300, 'd': 2400, 't': 'Show'},
            ],
        }
        tv = to_xmltv([SAMPLE_CHANNELS[0]], events)
        assert len(tv.findall('programme')) == 1

    def test_colliding_channel_names_keep_first(self):
        channels = [
            {'sid': '110', 'c': '105', 't': 'Sky Atlantic HD', 'sf': 'hd', 'schedule': True},
            {'sid': '999', 'c': '205', 't': 'Sky Atlantic HD', 'sf': 'sd', 'schedule': True},
        ]
        tv = to_xmltv(channels, {})
        channel_elems = tv.findall('channel')
        assert len(channel_elems) == 1
        assert channel_elems[0].get('api-id') == '110'

    def test_event_without_title_dropped(self):
        events = {'110': [{'eid': 'E-x', 'st': 1778538300, 'd': 2400, 't': ''}]}
        tv = to_xmltv([SAMPLE_CHANNELS[0]], events)
        assert len(tv.findall('programme')) == 0


# --- Integration tests ---

@pytest.mark.integration
class TestSkyApiClient:
    def test_fetch_channels_returns_channels(self):
        channels = fetch_channels()
        assert len(channels) >= 70
        for ch in channels:
            assert isinstance(ch['sid'], str) and ch['sid']
            assert isinstance(ch['t'], str) and ch['t']

    def test_fetch_broadcasts_returns_data(self):
        from zoneinfo import ZoneInfo
        berlin = ZoneInfo('Europe/Berlin')
        today = datetime.datetime.now(tz=berlin).date()

        # Sky Showcase HD, Sky Atlantic HD, Sky Krimi HD
        result = fetch_broadcasts(['142', '110', '23'], today)

        assert isinstance(result, dict)
        assert len(result) > 0
        for sid, events in result.items():
            assert isinstance(sid, str)
            assert len(events) > 0
            for ev in events:
                assert 'st' in ev
                assert 'd' in ev
                assert 't' in ev
