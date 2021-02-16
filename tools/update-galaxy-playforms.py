import requests
from typing import Dict, List

GALAXY_API_URL = "https://galaxy.ansible.com"


if __name__ == "__main__":

    print("Dumping list of Galaxy platforms")
    platforms: Dict[str, List[str]] = {}
    result = {'next_link': '/api/v1/platforms/'}
    while result.get('next_link', None):
        url = GALAXY_API_URL + result['next_link']
        result = requests.get(url).json()
        for entry in result['results']:
            if not isinstance(entry, dict):
                continue
            name = entry.get('name', None)
            release = entry.get('release', None)
            if not name or not isinstance(name, str):
                continue
            if name and name not in platforms:
                platforms[name] = []
            if (
                release not in ['any', 'None']
                and release not in platforms[name]
            ):
                platforms[name].append(release)

    with open("src/ansiblelint/schemas/_galaxy.py", "w") as f:
        f.write("GALAXY_PLATFORMS = %s" % platforms)
