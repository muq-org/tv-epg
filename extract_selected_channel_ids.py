import json

def main():
    with open('all_channels.json', 'r') as f:
        channels = json.load(f)
    selected = [ch['id'] for ch in channels if 'blue' in ch['name'].lower() or 'mysports' in ch['name'].lower()]
    with open('selected_channel_ids.json', 'w') as f:
        json.dump(selected, f, indent=2)
    print(f"Extracted {len(selected)} Blue Sport/MySports channel IDs to selected_channel_ids.json")

if __name__ == "__main__":
    main()