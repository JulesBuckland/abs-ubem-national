import pytest
from unittest.mock import patch, MagicMock
from src.inference.nuts_runner import run_inference
import pymc as pm

@patch('src.inference.nuts_runner.pm.sample')
@patch('src.inference.nuts_runner.pm.NUTS')
def test_run_inference(mock_nuts, mock_sample):
    mock_model = MagicMock()
    # mock context manager
    mock_model.__enter__ = MagicMock(return_value=mock_model)
    mock_model.__exit__ = MagicMock(return_value=None)
    
    mock_idata = MagicMock()
    mock_sample.return_value = mock_idata
    mock_nuts.return_value = 'nuts_step'
    
    result = run_inference(mock_model, tune=10, draws=20)
    
    assert result == mock_idata
    mock_nuts.assert_called_once()
    mock_sample.assert_called_once_with(
        draws=20,
        tune=10,
        step='nuts_step',
        return_inferencedata=True,
        progressbar=False,
        cores=1,
        chains=2
    )
