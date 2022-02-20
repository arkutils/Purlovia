import os
import sys
import time
from datetime import datetime
from subprocess import PIPE, Popen
from typing import List

import httpx

# Which depots do we need from each app?
app_ids = {
    "376030": [
        ["376031", 'Server: Content'],
    ],
    "346110": [
        ["346111", 'Client Core Content'],
        ["346114", 'Client: TheCenter'],
        ["346117", 'Client: Primitive+'],
        ["375351", 'Client: Scorched Earth'],
        ["375354", 'Client: Ragnarok'],
        ["375357", 'Client: Aberration'],
        ["473851", 'Client: Extinction'],
        ["473854", 'Client: Valguero'],
        ["473857", 'Client: Genesis 1&2'],
        ["1318685", 'Client: Crystal Isles'],
        ["1691801", 'Client: Lost Island'],
        ["1887561", 'Client: Fjordur'],
    ],
}


def parseAcf(data: str, outputType=dict):
    '''Adapted from github.com/leovp/steamfiles (MIT licensed).'''
    output = outputType()
    current_section = output
    sections: List[str] = []

    for line in data.splitlines():
        if not line:
            break
        line = line.strip()
        try:
            key, value = line.split(None, 1)
            key = key.replace('"', '').lstrip()
            value = value.replace('"', '').rstrip()
        except ValueError:
            if line == '{':
                # Initialize the last added section.
                current = output
                for i in sections[:-1]:
                    current = current[i]
                current[sections[-1]] = outputType()
                current_section = current[sections[-1]]
            elif line == '}':
                # Remove the last section from the queue.
                sections.pop()
            else:
                # Add a new section to the queue.
                sections.append(line.replace('"', ''))
            continue

        current_section[key] = value

    return output


def parseSteamCmd(data: str):
    '''
    Parse the mess that comes out of steamcmd.
    Returns a merged dictionary of the ACF data found.
    '''
    capturedAcf = ''
    capturedData = {}
    for line in data.splitlines():
        if not line:
            continue

        if not capturedAcf and line.startswith('"'):  # begin capturing acf
            capturedAcf = line
            continue

        if line[0] in ' \t{}':  # continue to capture
            capturedAcf += '\n' + line
            continue

        # End capturing and process the data
        new_data = parseAcf(capturedAcf)

        # Merge it with the existing data and continue
        capturedData.update(new_data)
        capturedAcf = ''

    # Ensure any trailing data is captured
    if capturedAcf:
        new_data = parseAcf(capturedAcf)
        capturedData.update(new_data)

    return capturedData


def fetchDepotStates():
    '''Run steamcmd and get all the latest app info'''

    # Gather the commands to fetch data for each app
    cmds = ['steamcmd.exe', '+login', 'anonymous', '+app_info_update', '1']

    for app_id in app_ids:
        cmds.extend(['+app_info_print', app_id])

    cmds.append('+quit')

    # Run the commands
    process = Popen(cmds, stdout=PIPE)
    output = process.communicate()[0].decode('utf-8')
    exitcode = process.wait()
    if exitcode != 0:
        print('Steam Error:', exitcode)
        return None

    # Process it into nice data structures
    data = parseSteamCmd(output)

    # Gather just the manifest IDs and names we need
    results = {}
    for app_id, depots in app_ids.items():
        for depot_id, name in depots:
            manifest_id = data[app_id]['depots'][depot_id]['manifests'].get('public', '-')
            results[depot_id] = dict(manifest_id=manifest_id, name=name)

    return results


def alert(depot_id, name, manifest_id):
    '''Send a message to a Discord channel'''
    url = os.getenv('PURLOVIA_WATCHER_WEBHOOK')
    role = os.getenv('PURLOVIA_WATCHER_ROLE', '@everyone')
    data = {
        'content': f'''{role}
**{name}** [{depot_id}] updated to `{manifest_id}`.
https://steamdb.info/depot/{depot_id}/history/.'''
    }
    httpx.post(url, json=data)


def printout(state):
    print(f'{datetime.now()}:')
    for depot_id in sorted(state.keys()):
        print(f'{state[depot_id]["manifest_id"]:>22}: [{depot_id}] {state[depot_id]["name"]}')


def main():
    # alert(376031, 'Server: Content', '7421526770546443422')
    # sys.exit(0)

    if not os.getenv('PURLOVIA_WATCHER_WEBHOOK'):
        print('Set PURLOVIA_WATCHER_WEBHOOK to a Discord webhook URL to receive alerts.', file=sys.stderr)
        sys.exit(1)

    if not os.getenv('PURLOVIA_WATCHER_ROLE'):
        print('Set PURLOVIA_WATCHER_ROLE to full Discord role syntax like: <@&944922011791147008>', file=sys.stderr)
        sys.exit(1)

    os.chdir('livedata/Steam')

    print('Fetching initial manifests...')
    current_ids = fetchDepotStates()
    printout(current_ids)

    while True:
        try:
            time.sleep(60)
        except KeyboardInterrupt:
            sys.exit(0)

        new_ids = fetchDepotStates()
        if new_ids is None:
            continue

        changes = {}
        for depot_id in current_ids:
            if new_ids[depot_id]['manifest_id'] != current_ids[depot_id]['manifest_id']:
                changes[depot_id] = new_ids[depot_id]

        if changes:
            print('Detected changes...')
            printout(changes)
            for depot_id in changes:
                alert(depot_id, changes[depot_id]['name'], changes[depot_id]['manifest_id'])

        current_ids = new_ids


if __name__ == '__main__':
    main()
