import random
from zoneinfo import ZoneInfo
from flask import Flask, session, render_template, url_for, redirect, request
import json
from pathlib import Path
from datetime import datetime
import os
from dotenv import load_dotenv
from postgrest import APIError
from supabase_auth.errors import AuthApiError
from flask_wtf.csrf import CSRFProtect
from supabase_client import get_supabase

load_dotenv()

BASE_DIR = Path(__file__).parent
TIMEZONE = ZoneInfo("America/Vancouver")
DEFAULT_GENDER_PREF = "female"
GENDER_PREF = {"female", "male", "both"}

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

malelist = []
for character in data:
    if character['gender'] == 'Male':
        malelist.append(character)

characterbyid = {}
for character in data:
    characterbyid[character['id']] = character




app = Flask(__name__)

app.secret_key = os.environ["SECRET_KEY"]
csrf = CSRFProtect(app)

@app.route('/')
def index():
    today = datetime.now(TIMEZONE).date()
    client = get_supabase()
    user = get_current_user(client)
    if user:
        todaysdraw = todayscharacterid(client, user.id, today)
        if todaysdraw is None:
            todaysdraw = createstodaysdraw(client, user.id, today, genderpreference(client, user.id))
        if todaysdraw is not None:
            c = characterbyid[todaysdraw]
        else:
            c = datecharacter(today)
    else:
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

@app.route('/logout', methods=["POST"])
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

@app.route('/history')
def history():
    client = get_supabase()
    user = get_current_user(client)
    if not user:
        return redirect(url_for("login"))
    draws = client.table("draws").select("day", "character_id").eq("user_id", user.id).order("day", desc=True).execute()
    characterdata = []
    for row in draws.data:
        characterlooked = characterbyid.get(row["character_id"])
        if characterlooked is not None:
            characterdata.append({
                "day": row["day"],
                "character": characterlooked,
            })
    return render_template("history.html", draws=characterdata, user=user)

@app.route('/settings', methods=["GET", "POST"])
def settings():
    client = get_supabase()
    user = get_current_user(client)
    if not user:
        return redirect(url_for("login"))
    if request.method == "POST":
        choice = request.form.get("gender_pref")
        if choice not in GENDER_PREF:
            return redirect(url_for("settings"))
        client.table("profiles").upsert({
            "user_id": user.id,
            "gender_pref": choice,
        }).execute()
        return redirect(url_for("settings"))
    current_pref = genderpreference(client, user.id)
    return render_template("settings.html", user=user, current_pref=current_pref)






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

def createstodaysdraw(client, user_id, day, genderpref):
    if genderpref == "female":
        pool = femalelist
    elif genderpref == "male":
        pool = malelist
    elif genderpref == 'both':
        pool = malelist + femalelist
    else:
        pool = femalelist
    response = client.table("draws").select("character_id").eq("user_id", user_id).execute()
    listofdraws = set()
    for row in response.data:
        listofdraws.add(row["character_id"])
    candidates = []
    for character in pool:
        if character["id"] not in listofdraws:
            candidates.append(character["id"])
    if not candidates:
        return None
    else:
        randomcharacter = random.choice(candidates)
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

def genderpreference(client, user_id):
    response = client.table("profiles").select("gender_pref").eq("user_id", user_id).execute()
    if not response.data:
        return DEFAULT_GENDER_PREF
    else:
        return response.data[0]["gender_pref"]

def get_current_user(client):
    try:
        response = client.auth.get_user()
    except AuthApiError as apierror:
        session.clear()
        print(f"Session was invalid, and it got cleared: {apierror}")
        return None
    if response is None:
        return None
    else:
        return response.user





