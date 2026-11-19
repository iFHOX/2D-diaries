from zoneinfo import ZoneInfo
from flask import Flask, render_template, url_for, redirect, request
import json
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase_auth.errors import AuthApiError

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
    client = get_supabase()
    response = client.auth.get_user()
    if response:
        user = response.user
    else: user = None
    c= datecharacter(datetime.now(TIMEZONE).date())
    if c is None:
        return render_template('index.html', c=None, user=user), 503
    return render_template('index.html', c=c, user=user)

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

@app.route('/logout')
def logout():
    client = get_supabase()
    client.auth.sign_out()
    return redirect(url_for("index"))

@app.route('/auth/callback')
def auth_callback():
    code = request.args.get("code")
    if request.args.get("error") or not code:
        return redirect(url_for("index"))
    client = get_supabase()
    try:
        client.auth.exchange_code_for_session({
            "auth_code" : code,
        })
    except AuthApiError as apierror:
        print(f"Code exchange failed: {apierror}")
    return redirect(url_for("index"))


def datecharacter(day):
    if femalelist:
        chosencharacter = day.toordinal() % len(femalelist)
        return femalelist[chosencharacter]
    else:
        return None
