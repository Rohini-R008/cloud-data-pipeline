import pytest
from pydantic import ValidationError

from src.schemas import PopulationRecord, RegionRecord


def test_population_valid():
    rec = PopulationRecord(country="India", population="1380004385", year="2020")
    assert rec.population == 1380004385
    assert rec.year == 2020


def test_population_missing_population_rejected():
    with pytest.raises(ValidationError):
        PopulationRecord(country="Brazil", population=None, year="2020")


def test_population_bad_year_rejected():
    with pytest.raises(ValidationError):
        PopulationRecord(country="Nigeria", population="206139589", year="twenty-twenty")


def test_population_year_out_of_range_rejected():
    with pytest.raises(ValidationError):
        PopulationRecord(country="X", population="1", year="1800")


def test_region_valid():
    rec = RegionRecord(country="India", region="South Asia", income_group="Lower middle income")
    assert rec.income_group == "Lower middle income"


def test_region_unknown_income_group_rejected():
    with pytest.raises(ValidationError):
        RegionRecord(country="X", region="Y", income_group="Middle-ish")