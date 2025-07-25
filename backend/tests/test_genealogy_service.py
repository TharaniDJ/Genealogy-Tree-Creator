import pytest
from app.services.genealogy_service import collect_bidirectional_relationships
from unittest.mock import patch

@pytest.fixture
def mock_fetch_entity():
    with patch('app.services.genealogy_service.fetch_entity') as mock:
        yield mock

@pytest.fixture
def mock_get_labels():
    with patch('app.services.genealogy_service.get_labels') as mock:
        yield mock

def test_collect_bidirectional_relationships(mock_fetch_entity, mock_get_labels):
    mock_fetch_entity.side_effect = [
        {
            "claims": {
                "P22": [{"mainsnak": {"datavalue": {"value": {"id": "Q1"}}}}],
                "P25": [{"mainsnak": {"datavalue": {"value": {"id": "Q2"}}}},
                "P40": [{"mainsnak": {"datavalue": {"value": {"id": "Q3"}}}}],
                "P26": [{"mainsnak": {"datavalue": {"value": {"id": "Q4"}}}}],
            }
        },
        {
            "claims": {
                "P22": [],
                "P25": [],
                "P40": [],
                "P26": [],
            }
        },
        {
            "claims": {
                "P22": [],
                "P25": [],
                "P40": [],
                "P26": [],
            }
        },
        {
            "claims": {
                "P22": [],
                "P25": [],
                "P40": [],
                "P26": [],
            }
        },
    ]

    mock_get_labels.return_value = {
        "Q1": "Father Name",
        "Q2": "Mother Name",
        "Q3": "Child Name",
        "Q4": "Spouse Name",
    }

    relationships = collect_bidirectional_relationships("Q0", 2)

    assert len(relationships) == 4
    assert relationships[0] == ["Child Name", "child of", "Q0"]
    assert relationships[1] == ["Father Name", "child of", "Q1"]
    assert relationships[2] == ["Mother Name", "child of", "Q2"]
    assert relationships[3] == ["Q0", "spouse of", "Spouse Name"]