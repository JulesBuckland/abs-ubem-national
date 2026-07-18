import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.data.archetypes import get_archetype_counts
from pathlib import Path

@patch("src.data.archetypes.pd.read_csv")
@patch("src.data.archetypes.Path.exists")
@patch("src.data.archetypes.pd.DataFrame.to_csv")
def test_get_archetype_counts_exists(mock_to_csv, mock_exists, mock_read_csv):
    mock_exists.return_value = True
    
    mock_read_csv.side_effect = [
        pd.DataFrame({
            "property_type": ["Detached", "Semi-detached", "Flat", "Flat"],
            "property_age": ["1900-1929", "1900-1929", "1930-1949", "1930-1949"]
        }),
        pd.DataFrame({
            "property_type": ["House", "Flat"],
            "property_age": ["1900-1929", "1930-1949"],
            "hlc": [150.0, 80.0]
        })
    ]
    
    get_archetype_counts()
    mock_to_csv.assert_called_once()

@patch("src.data.archetypes.Path.exists")
def test_get_archetype_counts_not_exists(mock_exists):
    mock_exists.return_value = False
    assert get_archetype_counts() is None
