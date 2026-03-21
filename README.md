# MUQ tv epg

This project fetches EPG data from a specified API endpoint and converts it to the standard XMLTV format.

## Features
- Fetches EPG data from a JSON API
- Converts data to XMLTV format

## Requirements
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for dependency management

## Usage

Install [uv](https://github.com/astral-sh/uv) if you haven't already, then run:

```sh
uv run python src/epg_to_xmltv.py
```

## Configuration
- Update the channel selection in `config/selected_channel_ids.json`.
- Update the API endpoint in `src/epg_to_xmltv.py` if needed.

## License
MIT
