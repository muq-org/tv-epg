# blue tv epg

This project fetches EPG data from a specified API endpoint and converts it to the standard XMLTV format for use with Dispatcharr.

## Features
- Fetches EPG data from a JSON API
- Converts data to XMLTV format
- Designed for easy integration with Dispatcharr

## Requirements
- Python 3.8+
- [uv](https://github.com/astral-sh/uv) for dependency management

## Setup

1. Install [uv](https://github.com/astral-sh/uv):
   ```sh
   curl -Ls https://astral.sh/uv/install.sh | sh
   ```
2. Install dependencies:
   ```sh
   uv pip install -r requirements.txt
   ```

## Usage

Run the script to fetch and convert EPG data:

```sh
python epg_to_xmltv.py
```

## Configuration
- Update the API endpoint and authentication headers in `epg_to_xmltv.py` as needed.

## License
MIT
