import json

# Path to your data file
DATA_PATH = 'extraction_data.json'

def migrate_total_time_to_time_taken():
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)

    changed = False
    for site in data.get('site_results', []):
        for attempt in site.get('extraction_attempts', []):
            if 'total_time' in attempt:
                attempt['time_taken'] = attempt.pop('total_time')
                changed = True

    if changed:
        with open(DATA_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        print('Migration complete: total_time -> time_taken')
    else:
        print('No migration needed: no total_time fields found')

if __name__ == '__main__':
    migrate_total_time_to_time_taken() 