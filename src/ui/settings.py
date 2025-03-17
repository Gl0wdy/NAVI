import os
import json


def get_config():
    if not os.path.exists('config.json'):
        with open('config.json', 'w') as file:
            data = {'wait_for_name': False, 'use_cached_code': True}
            json.dump(
                data,
                file, indent=4
            )
        return data

    with open('config.json', 'r') as file:
        return json.load(file)

def update_config(**kwargs):
    data = get_config()
    data.update(kwargs)

    with open('config.json', 'w') as file:
        json.dump(data, file, indent=4)