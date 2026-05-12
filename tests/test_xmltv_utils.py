import pytest
from xmltv_utils import slugify, format_xmltv_time, ms_to_xmltv_time


class TestSlugify:
    def test_basic(self):
        assert slugify("Sky Atlantic HD") == "sky-atlantic-hd"

    def test_special_chars(self):
        assert slugify("Crime + Investigation") == "crime-investigation"

    def test_leading_number(self):
        assert slugify("13th Street HD") == "13th-street-hd"

    def test_trailing_spaces(self):
        assert slugify("SPORTDIGITAL FUSSBALL  ") == "sportdigital-fussball"

    def test_multiple_separators(self):
        assert slugify("Sky  --  One") == "sky-one"

    def test_already_slug(self):
        assert slugify("natgeo") == "natgeo"


class TestFormatXmltvTime:
    def test_z_suffix(self):
        assert format_xmltv_time("2026-05-12T22:25:00Z") == "20260512222500 +0000"

    def test_utc_offset(self):
        assert format_xmltv_time("2026-05-12T22:25:00+00:00") == "20260512222500 +0000"

    def test_midnight(self):
        assert format_xmltv_time("2026-01-01T00:00:00Z") == "20260101000000 +0000"


class TestMsToXmltvTime:
    def test_known_value(self):
        # 1778538300000 ms = 2026-05-11T22:25:00Z
        assert ms_to_xmltv_time(1778538300000) == "20260511222500 +0000"

    def test_epoch_zero(self):
        assert ms_to_xmltv_time(0) == "19700101000000 +0000"

    def test_round_trip_consistency(self):
        # Verify ms→XMLTV and ISO→XMLTV agree for the same moment
        iso = "2026-05-12T10:30:00Z"
        ms = 1778581800000  # 2026-05-12T10:30:00Z
        assert format_xmltv_time(iso) == ms_to_xmltv_time(ms)
