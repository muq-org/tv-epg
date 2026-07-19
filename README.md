# MUQ TV EPG

Fetches TV schedule data from three sources and converts it to [XMLTV](http://wiki.xmltv.org/index.php/XMLTVFormat) format for use with media centers like Kodi, Jellyfin, and Plex.

## Public feeds

| Feed | URL | Coverage |
|---|---|---|
| Swiss provider channels | `https://muq-org.github.io/tv-epg/epg.xml` | 3 days |
| Sky Germany channels | `https://muq-org.github.io/tv-epg/epg_sky.xml` | 3 days |
| DAZN channels | `https://muq-org.github.io/tv-epg/epg_dazn.xml` | 3 days |

Feeds are regenerated daily at 05:00 UTC via GitHub Actions and published to GitHub Pages.

## Sources

| Script | Source | Channels | Output |
|---|---|---|---|
| `src/epg_to_xmltv.py` | Swiss provider (Sunrise/Blue) | configurable | `epg.xml` |
| `src/epg_sky_to_xmltv.py` | Sky Germany (Sky Q cloud EPG) | all (~336) | `epg_sky.xml` |
| `src/epg_dazn_to_xmltv.py` | DAZN (Germany) | all (~11) | `epg_dazn.xml` |

The DAZN and Sky feeds include channel logo images and per-programme artwork.

The Sky feed uses the Sky Q set-top-box cloud EPG (`atlantis.epgsky.com` / `awk.epgsky.com`), since Sky retired the public sky.de web TV guide in July 2026. It covers the full German Sky Q lineup including free-to-air channels.

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

## Usage

```sh
# Swiss provider EPG
uv run python src/epg_to_xmltv.py

# Sky Germany EPG
uv run python src/epg_sky_to_xmltv.py

# DAZN EPG
uv run python src/epg_dazn_to_xmltv.py
```

Output files are written to the repo root.

## Configuration

The Swiss provider feed is driven by `config/selected_channel_ids.json` — edit this file to add or remove channels. Each entry maps an internal API ID to an EPG ID used in the XMLTV output:

```json
{ "api-id": "4", "epg-id": "3+.ch", "name": "3+" }
```

To discover available channels:

```sh
uv run python src/list_channels.py
```

The Sky and DAZN feeds always include all available channels — no configuration needed.

## Testing

```sh
# Unit tests only (no network required)
uv run pytest tests/ -v -m "not integration"

# All tests including integration (calls live APIs)
uv run pytest tests/ -v
```

## License

MIT
