import pytest

from chefs_kitchen.models.chef_model import create_chef, get_chef_by_id, get_chef_by_name, delete_chef, update_chef_stats

@pytest.fixture
def sample_chef():
    return {
        "name": "Gordon Ramsay",
        "specialty": "British",
        "years_experience": 25,
        "signature_dishes": 15,
        "age": 55
    }

def test_create_chef(session, sample_chef):
    create_chef(**sample_chef)
    chef = get_chef_by_name(sample_chef["name"])
    assert chef.name == sample_chef["name"]
    assert chef.specialty == sample_chef["specialty"]

def test_create_duplicate_chef(session, sample_chef):
    create_chef(**sample_chef)
    with pytest.raises(ValueError, match="already exists"):
        create_chef(**sample_chef)

def test_get_chef_by_id(session, sample_chef):
    create_chef(**sample_chef)
    chef = get_chef_by_name(sample_chef["name"])
    retrieved = get_chef_by_id(chef.id)
    assert retrieved.name == chef.name

def test_delete_chef(session, sample_chef):
    create_chef(**sample_chef)
    chef = get_chef_by_name(sample_chef["name"])
    delete_chef(chef.id)
    with pytest.raises(ValueError):
        get_chef_by_id(chef.id)

def test_update_chef_stats(session, sample_chef):
    create_chef(**sample_chef)
    chef = get_chef_by_name(sample_chef["name"])
    update_chef_stats(chef.id, "win")
    updated_chef = get_chef_by_id(chef.id)
    assert updated_chef.wins == 1
    assert updated_chef.cookoffs == 1
