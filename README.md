# MUQ tv epg

This project fetches EPG data from a specified API endpoint and converts it to the standard XMLTV format.

## Features
- Fetches EPG data from a JSON API
- Converts data to XMLTV format

## Requirements
- Python 3.8+
- [uv](https://github.com/astral-sh/uv) for dependency management

## Usage

Install [uv](https://github.com/astral-sh/uv) if you haven't already, then run:

```sh
uv run epg_to_xmltv.py
```

## Configuration
- Update the API endpoint and authentication headers in `epg_to_xmltv.py` as needed.

## License
MIT
