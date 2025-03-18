import requests
import yaml


def get_tts_models():
    response = requests.get(
        'https://raw.githubusercontent.com/snakers4/silero-models/refs/heads/master/models.yml'
    )
    data = yaml.safe_load(response.content)
    models = data['tts_models']
    res = {}
    for lang, model in models.items():
        res[lang] = list(model.keys())
    return res