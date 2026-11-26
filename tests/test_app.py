import app
import fetch_characters
from types import SimpleNamespace
from datetime import date, timedelta, datetime


def test_character_pools_loaded():
    assert len(app.femalelist) == 400
    assert len(app.malelist) == 400
    assert len(app.characterbyid) == 800

def test_index_missing_character_falls_back_to_shared_pick(monkeypatch):

    fake_user = SimpleNamespace(id="user-1", email="test@example.com", user_metadata={})
    monkeypatch.setattr(app, "get_supabase", lambda: None)
    monkeypatch.setattr(app, "get_current_user", lambda client: fake_user)
    monkeypatch.setattr(app, "todayscharacterid", lambda client, user_id, day: -1)  # an ID no character has

    response = app.app.test_client().get("/")

    assert response.status_code == 200

    today = datetime.now(app.TIMEZONE).date()
    character_to_show = app.datecharacter(today)
    namecheck = response.get_data(as_text=True)

    assert character_to_show['name'] in namecheck




def test_clean_description_strips_stats_header():

    raw = "__Age:__ 17\n__Height:__ 160cm\n\nShe is a quiet student who spends every afternoon in the school library."

    result = fetch_characters.clean_description(raw)

    assert result is not None
    assert "__Age:__" not in result
    assert result.startswith("She is a quiet student")

def test_clean_description_real_gojo_format():
    raw = "__Height:__ 190 cm (6\'3)\n__Occupation:__ Jujutsu Sorcerer, Teacher\n__Affiliation:__ Tokyo Metropolitan Curse Technical College, Gojou Family\n__Grade:__ Special Grade Sorcerer\n__Cursed Technique:__ Six Eyes, Limitless\n\nSatoru Gojou is one of the strongest jujutsu sorcerers alive and a teacher at Jujutsu High."

    result = fetch_characters.clean_description(raw)

    assert result is not None
    assert "Height:" not in result
    assert "Occupation:" not in result
    assert "Affiliation:" not in result
    assert "Grade:" not in result
    assert "Cursed Technique:" not in result

    assert result.startswith("Satoru Gojou is one of")

def test_clean_description_without_header_is_unchanged():
    raw = "A cheerful transfer student who joins the cooking club and quickly becomes the heart of the group."
    assert fetch_characters.clean_description(raw) == raw

def test_clean_description_header_single_newline():

    raw = "__Age:__ 17\n__Height:__ 160cm\nShe is a quiet student who spends every afternoon in the school library."
    raw2 = "She is a quiet student who loves books.\n__Age:__ 17\nShe spends every afternoon in the school library."

    result = fetch_characters.clean_description(raw)
    result2 = fetch_characters.clean_description(raw2)

    assert result is not None
    assert result2 is not None

    assert result == "She is a quiet student who spends every afternoon in the school library."
    assert result2 == "She is a quiet student who loves books. She spends every afternoon in the school library."

def test_clean_description_none_input():

    result = fetch_characters.clean_description(None)
    assert result is None

def test_clean_description_empty_string_input():

    result = fetch_characters.clean_description("")
    assert result is None

def test_clean_description_skips_short_paragraph():

    raw = "A loyal knight of the eastern kingdom.\n\nHe swore an oath to protect the royal family and has never once broken it."

    result = fetch_characters.clean_description(raw)

    assert result is not None
    assert result == "He swore an oath to protect the royal family and has never once broken it."

def test_clean_description_check_spoilers():

    raw = "She trains every morning with her older brother. ~!He dies protecting her in the final battle.!~ Her goal is to become the strongest swordswoman in the land."
    result = fetch_characters.clean_description(raw)

    assert result is not None
    assert result == "She trains every morning with her older brother. Her goal is to become the strongest swordswoman in the land."

def test_clean_description_check_links():

    raw = "She is the younger sister of [Satoru Gojou](https://anilist.co/character/127691/Satoru-Gojou) and studies at the same school."

    result = fetch_characters.clean_description(raw)

    assert result is not None
    assert result == "She is the younger sister of Satoru Gojou and studies at the same school."

def test_clean_description_check_br():

    raw = "She lives alone in a small apartment near the station.<br>Her neighbors rarely see her outside."
    raw2 = "__Age:__ 17<br>\nShe lives alone in a small apartment near the station."

    result = fetch_characters.clean_description(raw)
    result2 = fetch_characters.clean_description(raw2)

    assert result is not None
    assert result == "She lives alone in a small apartment near the station. Her neighbors rarely see her outside."
    assert result2 is not None
    assert result2 == "She lives alone in a small apartment near the station."


def test_clean_description_39_and_40_character():
    raw_39 = "a" * 39
    raw_40 = "b" * 40

    assert fetch_characters.clean_description(raw_39) is None
    assert fetch_characters.clean_description(raw_40) == "b" * 40

def test_clean_description_spoiler_dotall():
    raw = "She trains every morning with her older brother. ~!He dies\nprotecting her in the final battle.!~ Her goal is to become the strongest swordswoman in the land."
    result = fetch_characters.clean_description(raw)
    assert result is not None
    assert result == "She trains every morning with her older brother. Her goal is to become the strongest swordswoman in the land."

def test_datecharacter_same_day_same_character():

    day = date(2026, 11, 25)

    character = app.datecharacter(day)
    character2 = app.datecharacter(day)

    assert character is not None
    assert character == character2

def test_datecharacter_character_in_the_pool():

    day = date(2026, 11, 25)
    character = app.datecharacter(day)

    assert character is not None
    assert character['id'] in app.characterbyid
    assert character == app.characterbyid[character['id']]

def test_datecharacter_different_days_characters():
    day = date(2026, 11, 25)
    characters = set()
    for i in range(30):
        characters.add(app.datecharacter(day + timedelta(days=i))['id'])
    assert len(characters) > 1





