"""Validates generated EPG XML files for basic sanity."""
import sys
from lxml import etree

CHECKS = [
    ('epg.xml',      {'min_channels': 50,  'min_programmes': 1000}),
    ('epg_sky.xml',  {'min_channels': 70,  'min_programmes': 2000}),
    ('epg_dazn.xml', {'min_channels': 10,  'min_programmes': 200}),
]

errors = []
for path, limits in CHECKS:
    try:
        root = etree.parse(path).getroot()
    except Exception as e:
        errors.append(f"{path}: failed to parse — {e}")
        continue

    channels = root.findall('channel')
    programmes = root.findall('programme')
    print(f"{path}: {len(channels)} channels, {len(programmes)} programmes")

    if len(channels) < limits['min_channels']:
        errors.append(f"{path}: only {len(channels)} channels (expected >= {limits['min_channels']})")
    if len(programmes) < limits['min_programmes']:
        errors.append(f"{path}: only {len(programmes)} programmes (expected >= {limits['min_programmes']})")

if errors:
    for e in errors:
        print(f"FAIL: {e}", file=sys.stderr)
    sys.exit(1)

print("All checks passed.")
