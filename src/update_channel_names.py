import json

with open('config/all_channels.json') as f:
    all_channels = json.load(f)

name_by_id = {c['id']: c['name'] for c in all_channels}

with open('config/selected_channel_ids.json') as f:
    selected = json.load(f)

updated = 0
for channel in selected:
    api_id = channel['api-id']
    new_name = name_by_id.get(api_id)
    if new_name and new_name != channel['name']:
        print(f"  {api_id}: '{channel['name']}' -> '{new_name}'")
        channel['name'] = new_name
        updated += 1

with open('config/selected_channel_ids.json', 'w') as f:
    json.dump(selected, f, indent=2, ensure_ascii=False)
    f.write('\n')

print(f"\nUpdated {updated} channel names.")
