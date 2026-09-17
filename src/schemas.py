from pydantic import BaseModel, ConfigDict, field_validator

# Allowed income groups (World Bank style). Anything else is quarantined.
ALLOWED_INCOME_GROUPS = {
    "High income",
    "Upper middle income",
    "Lower middle income",
    "Low income",
}


class PopulationRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    country: str
    population: int
    year: int

    @field_validator("country")
    @classmethod
    def country_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("country is blank")
        return v

    @field_validator("population")
    @classmethod
    def population_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("population must be non-negative")
        return v

    @field_validator("year")
    @classmethod
    def year_in_range(cls, v: int) -> int:
        if not (1900 <= v <= 2100):
            raise ValueError("year out of plausible range (1900-2100)")
        return v


class RegionRecord(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    country: str
    region: str
    income_group: str

    @field_validator("country", "region")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("field is blank")
        return v

    @field_validator("income_group")
    @classmethod
    def known_income_group(cls, v: str) -> str:
        if v not in ALLOWED_INCOME_GROUPS:
            raise ValueError(f"unknown income group: '{v}'")
        return v