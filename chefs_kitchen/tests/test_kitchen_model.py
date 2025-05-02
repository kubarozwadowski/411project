import time

import pytest

from chefs_kitchen.models.kitchen_model import KitchenModel
from chefs_kitchen.models.chef_model import Chef

@pytest.fixture
def kitchen_model():
    """Fixture to provide a new instance of KitchenModel for each test.

    """
    return KitchenModel()

# Fixtures providing sample chefs
@pytest.fixture
def sample_chef1(session):
    """Fixture for a sample chef
    """
    chef = Chef(
        name="Gordon Ramsay",
        specialty="Italian",
        years_experience= 25,
        signature_dishes= 20,
        age= 58
    )
    session.add(chef)
    session.commit()
    return chef

@pytest.fixture
def sample_chef2(session):
    """Fixture for a sample chef
    """
    chef = Chef(
        name="Alvin Leung",
        specialty="Chinese",
        years_experience= 30,
        signature_dishes= 10,
        age= 64
    )
    session.add(chef)
    session.commit()
    return chef

@pytest.fixture
def sample_chef3(session):
    """Fixture for a sample chef
    """
    chef = Chef(
        name="Aaron Sanchez",
        specialty= "Mexican",
        years_experience= 20,
        signature_dishes= 4,
        age= 49
    )
    session.add(chef)
    session.commit()
    return chef

@pytest.fixture
def sample_chefs(sample_chef1, sample_chef2, sample_chef3):
    """Fixture for a list with the sample chefs
    """
    return [sample_chef1, sample_chef2, sample_chef3]

##########################################################
# Chef Prep
##########################################################

def test_clear_kitchen(kitchen_model):
    """ Tests that clear_kitchen leaves no objects within self.kitchen
    """
    kitchen_model.kitchen = [1, 2, 3]
    kitchen_model.clear_kitchen()
    assert len(kitchen_model.kitchen) == 0, "Kitchen should be empty after calling clear_kitchen."
    
def test_clear_kitchen_empty(kitchen_model, caplog):
    """ Tests that clear_kitchen doesn't do anything when the kitchen is already empty
    """
    with caplog.at_level("WARNING"):
        kitchen_model.clear_kitchen()

    assert len(kitchen_model.kitchen) == 0, "Kitchen should remain empty if it was already empty."

    assert "Attempted to clear an empty kitchen." in caplog.text, "Expected a warning when cleakitchen an empty kitchen."
    
def test_get_chefs_empty(kitchen_model, caplog):
    """Test that get_chefs returns an empty list when there are no chefs and logs a warning.

    """
    with caplog.at_level("WARNING"):
        chefs = kitchen_model.get_chefs()

    assert chefs == [], "Expected get_chefs to return an empty list when there are no chefs."

    assert "Retrieving chefs from an empty kitchen." in caplog.text, "Expected a warning when getting chefs from an empty kitchen."

def test_get_chefs_with_data(app, kitchen_model, sample_chefs):
    """Test that get_chefs returns the correct list when there are chefs.

    # Note app is a fixture defined in the conftest.py file

    """
    kitchen_model.kitchen.extend([chef.id for chef in sample_chefs])

    chefs = kitchen_model.get_chefs()
    assert chefs == sample_chefs, "Expected get_chefs to return the correct chefs list."

def test_get_chefs_uses_cache(kitchen_model, sample_chef1, mocker):
    """ Tests that get_chefs accesses self._chefs_cache if the chef is in the cache
    """
    kitchen_model.kitchen.append(sample_chef1.id)

    kitchen_model._chefs_cache[sample_chef1.id] = sample_chef1
    kitchen_model._ttl[sample_chef1.id] = time.time() + 100  # still valid

    mock_get_by_id = mocker.patch("models.kitchen_model.Chef.get_chef_by_id")

    chefs = kitchen_model.get_chefs()

    assert chefs[0] == sample_chef1
    mock_get_by_id.assert_not_called()

def test_get_chefs_refreshes_on_expired_ttl(kitchen_model, sample_chef1, mocker):
    """ Tests that get_chefs refreshs on expired ttls
    """
    kitchen_model.kitchen.append(sample_chef1.id)

    stale_chef = mocker.Mock()
    kitchen_model._chefs_cache[sample_chef1.id] = stale_chef
    kitchen_model._ttl[sample_chef1.id] = time.time() - 1  # TTL expired

    mock_get_by_id = mocker.patch("models.kitchen_model.Chef.get_chef_by_id", return_value=sample_chef1)

    chefs = kitchen_model.get_chefs()

    assert chefs[0] == sample_chef1
    mock_get_by_id.assert_called_once_with(sample_chef1.id)
    assert kitchen_model._chefs_cache[sample_chef1.id] == sample_chef1

def test_cache_populated_on_get_chefs(kitchen_model, sample_chef1, mocker):
    """ Tests that get_chef adds chefs to the cache
    """
    mock_get_by_id = mocker.patch("models.kitchen_model.Chef.get_chef_by_id", return_value=sample_chef1)

    kitchen_model.kitchen.append(sample_chef1.id)

    chefs = kitchen_model.get_chefs()

    assert sample_chef1.id in kitchen_model._chefs_cache
    assert sample_chef1.id in kitchen_model._ttl
    assert chefs[0] == sample_chef1
    mock_get_by_id.assert_called_once_with(sample_chef1.id)

def test_enter_kitchen(kitchen_model, sample_chefs, app):
    """Test that a chef is correctly added to the kitchen.

    """
    kitchen_model.enter_kitchen(sample_chefs[0].id)  # Assuming chef with ID 1 is "Muhammad Ali"

    assert len(kitchen_model.kitchen) == 1, "Kitchen should contain one chef after calling enter_kitchen."
    assert kitchen_model.kitchen[0] == 1, "Expected 'Gordan Ramsay' (id 1) in the kitchen."

    kitchen_model.enter_kitchen(sample_chefs[1].id)  # Assuming chef with ID 2 is "Mike Tyson"

    assert len(kitchen_model.kitchen) == 2, "Kitchen should contain two chefs after calling enter_kitchen."
    assert kitchen_model.kitchen[1] == 2, "Expected 'Alvin Leung' (id 2) in the kitchen."

def test_enter_kitchen_full(kitchen_model):
    """Test that enter_kitchen raises an error when the kitchen is full.

    """
    kitchen_model.kitchen = list(range(20))

    with pytest.raises(ValueError, match="Kitchen is full"):
        kitchen_model.enter_kitchen(21)

    assert len(kitchen_model.kitchen) == 20, "Kitchen should still contain only 2 chefs after trying to add a third."


##########################################################
# Fight
##########################################################


def test_calculate_chef_skill(kitchen_model, sample_chefs):
    """Test the calculate_chef_skill method.

    """
    expected_score_1 = (25 * 4) + (20 * 2) + 5 - 5 
    assert kitchen_model.calculate_chef_skill(sample_chefs[0], "Italian") == expected_score_1, f"Expected score: {expected_score_1}, got {kitchen_model.calculate_chef_skill(sample_chef1, "Italian")}"

    expected_score_2 = (30 * 4) + (10 * 2) - 5  
    assert kitchen_model.calculate_chef_skill(sample_chefs[1], "Italian") == expected_score_2, f"Expected score: {expected_score_2}, got {kitchen_model.calculate_chef_skill(sample_chef2, "Italian")}"

    expected_score_3 = (20 * 4) + (4 * 2) - 5
    assert kitchen_model.calculate_chef_skill(sample_chefs[3], "Italian") == expected_score_3, f"Expected score: {expected_score_2}, got {kitchen_model.calculate_chef_skill(sample_chef3, "Italian")}"

def test_cookoff(kitchen_model, sample_chefs, caplog, mocker):
    """Test the cookoff method with sample chefs.

    """
    kitchen_model.kitchen.extend(sample_chefs)

    mocker.patch("models.kitchen_model.KitchenModel.calculate_chef_skill", side_effect=[2526.8, 2206.1])
    mocker.patch("models.kitchen_model.get_random", return_value=0.42)
    mocker.patch("models.kitchen_model.KitchenModel.get_chefs", return_value=sample_chefs)
    mock_update_stats = mocker.patch("models.kitchen_model.Chef.update_stats")

    winner_name = kitchen_model.cookoff("Italian")

    assert winner_name == "Gordon Ramsay", f"Expected chef 1 to win, but got {winner_name}"

    mock_update_stats.assert_any_call('win')  # chef_1 is the winner

    assert len(kitchen_model.kitchen) == 0, "Kitchen should be empty after the cookoff."

    assert "The winner is: Gordon Ramsay" in caplog.text, "Expected winner log message not found."

def test_cookoff_with_empty_kitchen(kitchen_model):
    """Test that the cookoff method raises a ValueError when there are fewer than two chefs.

    """
    with pytest.raises(ValueError, match="There must be two chefs to start a cookoff."):
        kitchen_model.cookoff("Italian")

def test_cookoff_with_one_chef(kitchen_model, sample_chef1):
    """Test that the cookoff method raises a ValueError when there's only one chef.

    """
    kitchen_model.kitchen.append(sample_chef1)

    with pytest.raises(ValueError, match="There must be two chefs to start a cookoff."):
        kitchen_model.cookoff("Italian")

def test_clear_cache(kitchen_model, sample_chef1):
    kitchen_model._chefs_cache[sample_chef1.id] = sample_chef1
    kitchen_model._ttl[sample_chef1.id] = time.time() + 100

    kitchen_model.clear_cache()

    assert kitchen_model._chefs_cache == {}
    assert kitchen_model._ttl == {}
