from datetime import datetime

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.models.taxonomy import (
    TaxonomyTuplesResponse,
    TaxonomicTuple,
    TaxonomicEntity,
    ExpansionResponse,
)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_healthcheck(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["message"].endswith("is running")
    assert body["status"] == "healthy"


def test_taxonomy_endpoint(monkeypatch, client):
    fake_response = TaxonomyTuplesResponse(
        scientific_name="Homo sapiens",
        tuples=[
            TaxonomicTuple(
                parent_taxon=TaxonomicEntity(rank="genus", name="Homo"),
                has_child=True,
                child_taxon=TaxonomicEntity(rank="species", name="Homo sapiens"),
            )
        ],
        total_relationships=1,
        extraction_method="real-time",
    )

    monkeypatch.setattr(
        "app.api.routes.taxonomy_extractor.extract_as_tuples",
        lambda scientific_name: fake_response,
    )

    response = client.get("/api/species/taxonomy/Homo%20sapiens")
    assert response.status_code == 200
    body = response.json()
    assert body["scientific_name"] == "Homo sapiens"
    assert body["total_relationships"] == 1


def test_expand_auto_detect(monkeypatch, client):
    fake_response = ExpansionResponse(
        parent_taxon=TaxonomicEntity(rank="genus", name="Homo"),
        children=[TaxonomicEntity(rank="species", name="Homo sapiens")],
        tuples=[
            TaxonomicTuple(
                parent_taxon=TaxonomicEntity(rank="genus", name="Homo"),
                has_child=True,
                child_taxon=TaxonomicEntity(rank="species", name="Homo sapiens"),
            )
        ],
        total_children=1,
    )

    monkeypatch.setattr(
        "app.api.routes.taxonomy_expander.expand_auto_detect",
        lambda *args, **kwargs: fake_response,
    )

    response = client.get("/api/species/expand/Homo%20sapiens")
    assert response.status_code == 200
    body = response.json()
    assert body["total_children"] == 1
    assert body["children"][0]["name"] == "Homo sapiens"
