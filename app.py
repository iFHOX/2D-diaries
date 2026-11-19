from zoneinfo import ZoneInfo
from flask import Flask, render_template, url_for, redirect, request
import json
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv

from supabase_client import get_supabase

load_dotenv()

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

app.secret_key = os.environ["SECRET_KEY"]

@app.route('/')
def index():
    c= datecharacter(datetime.now(TIMEZONE).date())
    if c is None:
        return render_template('index.html', c=None), 503
    return render_template('index.html', c=c)

@app.route('/login')
def login():
    client= get_supabase()
    response= client.auth.sign_in_with_oauth({
        "provider" : "google",
        "options" : {
            "redirect_to" : url_for("auth_callback", _external=True),
        }
    })
    return redirect(response.url)

@app.route('/auth/callback')
def auth_callback():
    return request.args.get("code")


def datecharacter(day):
    if femalelist:
        chosencharacter = day.toordinal() % len(femalelist)
        return femalelist[chosencharacter]
    else:
        return None
