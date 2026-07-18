import pandas as pd
import pytest
import logging
from src.utils.tracker import calculate_distribution_stats, log_distribution

def test_calculate_distribution_stats():
    df = pd.DataFrame({'a': [1, 2, 3, 4, 5]})
    stats = calculate_distribution_stats(df, 'a')
    assert stats['count'] == 5
    assert stats['mean'] == 3.0
    assert stats['min'] == 1.0
    assert stats['max'] == 5.0

def test_calculate_distribution_stats_missing():
    df = pd.DataFrame({'a': [1]})
    with pytest.raises(ValueError):
        calculate_distribution_stats(df, 'b')

def test_log_distribution(caplog):
    df = pd.DataFrame({'a': [1, 2, 3, 4, 5]})
    logger = logging.getLogger("test")
    with caplog.at_level(logging.INFO):
        log_distribution(df, 'a', 'test_stage', logger)
    assert "test_stage" in caplog.text
    assert "Mean : 3.00" in caplog.text

def test_log_distribution_missing(caplog):
    df = pd.DataFrame({'a': [1, 2, 3]})
    logger = logging.getLogger("test")
    with pytest.raises(ValueError):
        log_distribution(df, 'b', 'test_stage', logger)
    assert "FATAL LINEAGE TRACKING" in caplog.text
