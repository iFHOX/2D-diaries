from flask import Flask
from flask import render_template
import json
from pathlib import Path
from datetime import date, timedelta

BASE_DIR = Path(__file__).parent

try:
    with open(BASE_DIR / "characters.json", "r", encoding="utf-8") as file:
        data = json.load(file)
except (FileNotFoundError, json.JSONDecodeError) as e:
    data = []
    print("Error retrieving characters: {e}")


app = Flask(__name__)

@app.route('/')
def index():
    c= datecharacter(date.today())
    if c is None:
        return render_template('index.html', c=None), 503
    return render_template('index.html', c=datecharacter(date.today()))


def datecharacter(day):
    if data:
        chosencharacter = day.toordinal() % len(data)
        return data[chosencharacter]
    else:
        return None
