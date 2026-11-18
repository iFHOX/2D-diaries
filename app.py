from zoneinfo import ZoneInfo
from flask import Flask
from flask import render_template
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
TIMEZONE = ZoneInfo("America/Vancouver")

try:
    with open(BASE_DIR / "characters.json", "r", encoding="utf-8") as file:
        data = json.load(file)
except (FileNotFoundError, json.JSONDecodeError) as e:
    data = []
    print(f"Error retrieving characters: {e}")

femalelist = []
for character in data:
    if character['gender'] == 'Female':
        femalelist.append(character)




app = Flask(__name__)

@app.route('/')
def index():
    c= datecharacter(datetime.now(TIMEZONE).date())
    if c is None:
        return render_template('index.html', c=None), 503
    return render_template('index.html', c=c)


def datecharacter(day):
    if femalelist:
        chosencharacter = day.toordinal() % len(femalelist)
        return femalelist[chosencharacter]
    else:
        return None
