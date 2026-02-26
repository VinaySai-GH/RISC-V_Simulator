import json

def load_config(filepath):
    with open(filepath,"r") as f:
        config=json.load(f)
    return config