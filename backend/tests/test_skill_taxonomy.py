from app.services.skill_taxonomy import get_skill_taxonomy


def test_normalize_known_aliases():
    tax = get_skill_taxonomy()
    assert tax.normalize("ReactJS") == "React"
    assert tax.normalize("react.js") == "React"
    assert tax.normalize("Postgres") == "PostgreSQL"
    assert tax.normalize("PostgresSQL") is None or tax.normalize("postgressql") == "PostgreSQL"


def test_normalize_unknown_returns_none():
    tax = get_skill_taxonomy()
    assert tax.normalize("SomeMadeUpTechThatDoesNotExist") is None


def test_extract_from_text_multiword_alias_wins():
    tax = get_skill_taxonomy()
    found = tax.extract_from_text("Experienced in machine learning and Python.")
    assert "Machine Learning" in found
    assert "Python" in found


def test_extract_from_text_word_boundaries():
    tax = get_skill_taxonomy()
    # "Java" should not match inside "JavaScript"
    found = tax.extract_from_text("I write JavaScript daily.")
    assert "Java" not in found
    assert "JavaScript" in found


def test_category_of():
    tax = get_skill_taxonomy()
    assert tax.category_of("Python") == "programming_languages"
    assert tax.category_of("FastAPI") == "frameworks_backend"
