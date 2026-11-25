# tests/test_app.py
import app
import fetch_characters


def test_character_pools_loaded():
    assert len(app.femalelist) == 400
    assert len(app.malelist) == 400
    assert len(app.characterbyid) == 800

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


