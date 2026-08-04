from src.context import build_schema_card


def test_card_contains_all_tables(adapter):
    card = build_schema_card(adapter)
    for table in [
        "accounts",
        "budgets",
        "categories",
        "merchants",
        "savings_goals",
        "subscriptions",
        "transactions",
    ]:
        assert "CREATE TABLE" in card
        assert table in card


def test_card_has_fk_section(adapter):
    card = build_schema_card(adapter)
    assert "transactions.category_id -> categories.category_id" in card


def test_card_enumerates_low_cardinality_values(adapter):
    card = build_schema_card(adapter)
    assert "Groceries" in card
    assert "expense" in card


def test_card_skips_high_cardinality_columns(adapter):
    card = build_schema_card(adapter, enum_cap=5)
    assert card.count("June salary") == 0 or "transactions.description:" not in card


def test_card_has_sample_rows(adapter):
    card = build_schema_card(adapter)
    assert "Sample rows" in card
    assert "Everyday Checking" in card


def test_card_is_reasonably_sized(adapter):
    card = build_schema_card(adapter)
    assert 2_000 < len(card) < 60_000


def test_glossary_merged_when_present(adapter, tmp_path):
    glossary = tmp_path / "glossary.md"
    glossary.write_text("- best-selling: rank by total revenue, not units")
    card = build_schema_card(adapter, glossary_path=str(glossary))
    assert "Business glossary" in card
    assert "total revenue" in card


def test_glossary_skipped_when_absent(adapter):
    card = build_schema_card(adapter, glossary_path="does/not/exist.md")
    assert "Business glossary" not in card
