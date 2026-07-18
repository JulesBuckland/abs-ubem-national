import pandas as pd
import pytest
from src.utils.data_contracts import population_schema

def test_population_schema_valid():
    df = pd.DataFrame({
        "msoa21cd": ["E02000001"],
        "property_type": ["House"],
        "tenure": ["Owned"],
        "form_code": [1],
        "empirical_thermal_kwh": [100.0],
        "empirical_gas_kwh": [50.0],
        "floor_area": [50.0],
        "wall_u": [1.0],
        "ach": [1.0],
        "wwr": [0.2]
    })
    validated = population_schema.validate(df)
    assert not validated.empty

def test_population_schema_invalid():
    df = pd.DataFrame({
        "msoa21cd": ["X02000001"], # invalid prefix
        "property_type": ["House"],
        "tenure": ["Owned"],
        "form_code": [1],
        "empirical_thermal_kwh": [100.0],
        "empirical_gas_kwh": [50.0],
        "floor_area": [50.0],
        "wall_u": [1.0],
        "ach": [1.0],
        "wwr": [0.2]
    })
    import pandera as pa
    with pytest.raises(pa.errors.SchemaError):
        population_schema.validate(df)
