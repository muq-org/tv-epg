import pytest
from epg_dazn_to_xmltv import fetch_tiles, to_xmltv


# --- Fixtures ---

SAMPLE_TILES = [
    {
        'Title': 'DAZN 1',
        'AssetId': 'asset-dazn1',
        'LogoImage': {'Id': 'Logo_LTV_DAZN_1', 'ImageMimeType': 'png'},
        'LinearSchedule': {
            'Now': {
                'Title': 'Fußball: Bundesliga',
                'EpisodeTitle': 'VfB Stuttgart - Leverkusen',
                'Start': '2026-05-12T07:15:00Z',
                'End': '2026-05-12T09:15:00Z',
                'Genre': [{'name': 'Soccer', 'MappedValue': [1]}],
                'Image': {'Id': 'prog-img-001', 'ImageMimeType': 'jpg'},
            },
            'Next': {
                'Title': 'La Liga',
                'EpisodeTitle': 'Barcelona - Real Madrid',
                'Start': '2026-05-12T09:15:00Z',
                'End': '2026-05-12T11:15:00Z',
                'Genre': [{'name': 'Soccer'}],
                'Image': {'Id': 'prog-img-002', 'ImageMimeType': 'jpg'},
            },
            'Later': [
                {
                    'Title': 'Best of DAZN',
                    'EpisodeTitle': '',
                    'Start': '2026-05-12T11:15:00Z',
                    'End': '2026-05-12T11:45:00Z',
                    'Genre': [{'name': 'Entertainment'}],
                    'Image': None,
                },
            ],
        },
    },
    {
        'Title': 'DAZN 2',
        'AssetId': 'asset-dazn2',
        'LogoImage': {'Id': 'Logo_LTV_DAZN_2', 'ImageMimeType': 'png'},
        'LinearSchedule': {
            'Now': {
                'Title': 'Same Title',
                'EpisodeTitle': 'Same Title',
                'Start': '2026-05-12T08:00:00Z',
                'End': '2026-05-12T09:00:00Z',
                'Genre': [],
                'Image': {'Id': 'prog-img-003', 'ImageMimeType': 'jpg'},
            },
            'Next': None,
            'Later': [],
        },
    },
    {
        'Title': 'Rally TV',
        'AssetId': 'asset-rally',
        'LogoImage': {'Id': 'Logo_Rally_TV', 'ImageMimeType': 'png'},
        'LinearSchedule': None,
    },
]


# --- Unit tests ---

class TestToXmltvStructure:
    def setup_method(self):
        self.tv = to_xmltv(SAMPLE_TILES)

    def test_returns_tv_element(self):
        assert self.tv.tag == 'tv'

    def test_null_schedule_channel_excluded(self):
        ids = [ch.get('id') for ch in self.tv.findall('channel')]
        assert 'rally-tv.de' not in ids

    def test_channel_count(self):
        assert len(self.tv.findall('channel')) == 2

    def test_channel_epg_ids(self):
        ids = [ch.get('id') for ch in self.tv.findall('channel')]
        assert 'dazn-1.de' in ids
        assert 'dazn-2.de' in ids

    def test_channel_display_name(self):
        ch = self.tv.find("channel[@id='dazn-1.de']")
        assert ch.find('display-name').text == 'DAZN 1'

    def test_channel_logo_url(self):
        ch = self.tv.find("channel[@id='dazn-1.de']")
        icon = ch.find('icon')
        assert icon is not None
        assert icon.get('src') == (
            'https://image.discovery.indazn.com/eu/v3/linear-channel/none/'
            'Logo_LTV_DAZN_1/contain/center/center/none/80/136/112/png/image?brand=dazn'
        )

    def test_programme_count(self):
        # DAZN 1: Now + Next + 1 Later = 3; DAZN 2: Now only = 1
        assert len(self.tv.findall('programme')) == 4

    def test_programme_times(self):
        progs = self.tv.findall("programme[@channel='dazn-1.de']")
        now_prog = progs[0]
        assert now_prog.get('start') == '20260512071500 +0000'
        assert now_prog.get('stop') == '20260512091500 +0000'

    def test_programme_title(self):
        progs = self.tv.findall("programme[@channel='dazn-1.de']")
        assert progs[0].find('title').text == 'Fußball: Bundesliga'

    def test_sub_title_when_different(self):
        progs = self.tv.findall("programme[@channel='dazn-1.de']")
        assert progs[0].find('sub-title').text == 'VfB Stuttgart - Leverkusen'

    def test_sub_title_omitted_when_same_as_title(self):
        prog = self.tv.find("programme[@channel='dazn-2.de']")
        assert prog.find('sub-title') is None

    def test_sub_title_omitted_when_empty(self):
        progs = self.tv.findall("programme[@channel='dazn-1.de']")
        best_of = next(p for p in progs if p.find('title').text == 'Best of DAZN')
        assert best_of.find('sub-title') is None

    def test_category(self):
        progs = self.tv.findall("programme[@channel='dazn-1.de']")
        assert progs[0].find('category').text == 'Soccer'

    def test_category_omitted_when_empty_genre(self):
        prog = self.tv.find("programme[@channel='dazn-2.de']")
        assert prog.find('category') is None

    def test_programme_icon_url(self):
        progs = self.tv.findall("programme[@channel='dazn-1.de']")
        icon = progs[0].find('icon')
        assert icon is not None
        assert icon.get('src') == (
            'https://image.discovery.indazn.com/eu/v3/eu/none/'
            'prog-img-001/fill/none/top/none/80/668/374/webp/image?brand=dazn'
        )

    def test_programme_icon_omitted_when_no_image(self):
        progs = self.tv.findall("programme[@channel='dazn-1.de']")
        best_of = next(p for p in progs if p.find('title').text == 'Best of DAZN')
        assert best_of.find('icon') is None


# --- Integration tests ---

@pytest.mark.integration
class TestDaznApiClient:
    def test_fetch_tiles_returns_channels(self):
        tiles = fetch_tiles()
        linear = [t for t in tiles if t.get('IsLinear')]
        assert len(linear) >= 10

    def test_at_least_one_tile_has_schedule(self):
        tiles = fetch_tiles()
        with_schedule = [t for t in tiles if t.get('LinearSchedule')]
        assert len(with_schedule) >= 1
        assert with_schedule[0]['LinearSchedule'].get('Now') is not None
