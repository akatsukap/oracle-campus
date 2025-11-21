import json

def load_data():
    with open('data/database.json', 'r') as f:
        return json.load(f)