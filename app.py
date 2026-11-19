import random
from zoneinfo import ZoneInfo
from flask import Flask, render_template, url_for, redirect, request
import json
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv
from postgrest import APIError
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

characterbyid = {}
for character in data:
    characterbyid[character['id']] = character




app = Flask(__name__)

app.secret_key = os.environ["SECRET_KEY"]

@app.route('/')
def index():
    today = datetime.now(TIMEZONE).date()
    client = get_supabase()
    response = client.auth.get_user()
    if response:
        user = response.user
        todaysdraw = todayscharacterid(client, user.id, today)
        if todaysdraw is None:
            todaysdraw = createstodaysdraw(client, user.id, today)
        if todaysdraw is not None:
            c = characterbyid[todaysdraw]
        else:
            c = datecharacter(today)
    else:
        user = None
        c = datecharacter(today)
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

def todayscharacterid(client, user_id, day):
    response = client.table("draws").select("character_id").eq("user_id", user_id).eq("day", day.isoformat()).execute()
    if response.data:
        return response.data[0]["character_id"]
    else:
        return None

def createstodaysdraw(client, user_id, day):
    response = client.table("draws").select("character_id").eq("user_id", user_id).execute()
    listofdraws = set()
    for row in response.data:
        listofdraws.add(row["character_id"])
    femalecandidates = []
    for character in femalelist:
        if character["id"] not in listofdraws:
            femalecandidates.append(character["id"])
    if not femalecandidates:
        return None
    else:
        randomcharacter = random.choice(femalecandidates)
        characterdict = {
            "user_id": user_id,
            "day": day.isoformat(),
            "character_id": randomcharacter,
        }
        try:
            client.table("draws").insert(characterdict).execute()
        except APIError as e:
            if e.code == "23505":
                return todayscharacterid(client, user_id, day)
            else:
                raise
        return randomcharacter

