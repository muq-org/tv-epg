# MUQ TV EPG

Fetches TV schedule data from two sources and converts it to [XMLTV](http://wiki.xmltv.org/index.php/XMLTVFormat) format for use with media centers like Kodi, Jellyfin, and Plex.

## Public feeds

| Feed | URL |
|---|---|
| Swiss provider channels | `https://muq-org.github.io/tv-epg/epg.xml` |
| Sky.de channels | `https://muq-org.github.io/tv-epg/epg_sky.xml` |

Both feeds cover today and tomorrow and are regenerated daily at 05:00 UTC via GitHub Actions.

## Sources

| Script | Source | Output |
|---|---|---|
| `src/epg_to_xmltv.py` | Swiss provider (Sunrise/Blue) | `epg.xml` |
| `src/epg_sky_to_xmltv.py` | Sky.de (all 78 channels) | `epg_sky.xml` |

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)

## Usage

```sh
# Swiss provider EPG
uv run python src/epg_to_xmltv.py

# Sky.de EPG
uv run python src/epg_sky_to_xmltv.py
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

The Sky.de feed always includes all available channels — no configuration needed.

## Testing

```sh
# All tests (unit + integration — integration tests call the live Sky.de API)
uv run pytest tests/ -v

# Unit tests only (no network required)
uv run pytest tests/ -v -m "not integration"
```

## License

MIT
