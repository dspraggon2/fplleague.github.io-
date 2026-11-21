import json
import pathlib
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent

def get(path):
    request = urllib.request.Request('https://fantasy.premierleague.com/api/' + path, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.load(response)

def main():
    config = json.loads((ROOT / 'league-config.json').read_text())
    events = get('bootstrap-static/')['events']
    entries = {}
    for page in range(1, 11):
        result = get(f"leagues-classic/{config['leagueId']}/standings/?page_standings={page}")
        league = result['league']
        for entry in result['standings']['results']:
            entries[entry['entry']] = entry
        if not result['standings']['has_next']:
            break
    else:
        raise ValueError('League exceeds supported pagination')
    managers = []
    for entry in entries.values():
        history = get(f"entry/{entry['entry']}/history/")
        managers.append(dict(id=entry['entry'], manager=entry['player_name'], team=entry['entry_name'], history=history['current'], chips=history['chips']))
    if not events or not managers:
        raise ValueError('FPL returned incomplete data; not publishing')
    data = dict(league=league, events=events, managers=managers, fetchedAt=datetime.now(timezone.utc).isoformat(), sourceMode='live')
    (ROOT / 'data/league.json').write_text(json.dumps(data))
    (ROOT / 'data/config.json').write_text(json.dumps(config))
    print(f'Updated {len(managers)} teams')

if __name__ == '__main__':
    main()
