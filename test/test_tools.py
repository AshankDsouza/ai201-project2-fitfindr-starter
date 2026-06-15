# tests/test_tools.py
from tools import search_listings, suggest_outfit, create_fit_card, get_filter_criteria_values
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

def test_get_filter_criteria_values():
    query = "looking for a vintage graphic tee under $30 in size M"
    expected_output = {
        "description": "vintage graphic tee",
        "size": "M",
        "max_price": 30.0,
    }
    output = get_filter_criteria_values(query)
    assert output == expected_output


def test_get_filter_criteria_values_without_price():
    query = "looking for a vintage graphic tee in size M"
    expected_output = {
        "description": "vintage graphic tee",
        "size": "M",
        "max_price": None,
    }
    output = get_filter_criteria_values(query)
    assert output == expected_output


def test_get_filter_criteria_values_without_size():
    query = "looking for a vintage graphic tee under $30"
    expected_output = {
        "description": "vintage graphic tee",
        "size": None,
        "max_price": 30.0,
    }
    output = get_filter_criteria_values(query)
    assert output == expected_output

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []   # empty list, no exception

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


def test_suggest_outfit_with_empty_new_item():
    empty_new_item = None
    suggestion = suggest_outfit(empty_new_item, get_empty_wardrobe())

    assert suggestion is not None
    # suggestion should be a non-empty string:
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0
    assert suggestion == "Black and white is a safe choice. Other color pairings should be based on common color theory rules."

def test_suggest_outfit_with_empty_wardrobe():
    results = search_listings('vintage graphic tee', size=None, max_price=50)
    suggestion = suggest_outfit(results[0], get_empty_wardrobe())

    assert suggestion is not None
    # suggestion should be a non-empty string:
    assert isinstance(suggestion, str)
    assert len(suggestion) > 0
    assert suggestion == "Black and white is a safe choice. Other color pairings should be based on common color theory rules."


def test_create_fit_card_empty_outfit():
    results = search_listings('vintage graphic tee', size=None, max_price=50)
    fit_card = create_fit_card(outfit='', new_item=results[0])
    
    # check that error is 'Could not create a fit due to insufficient information.':
    assert fit_card == "Could not create a fit due to insufficient information."
