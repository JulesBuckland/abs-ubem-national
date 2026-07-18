import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from src.inference.gp_emulator import load_data, train_gp, plot_validation, save_model, validate_saved, main
import src.inference.gp_emulator as gp_emulator

@patch('src.inference.gp_emulator.COMBINED_CSV')
@patch('src.inference.gp_emulator.pd.read_csv')
def test_load_data(mock_read_csv, mock_combined):
    mock_combined.exists.return_value = True
    df = pd.DataFrame({
        'status': ['ok', 'error', 'ok'],
        'floor_area': [1, 2, 3],
        'wall_u': [1, 2, 3],
        'ach': [1, 2, 3],
        'wwr': [1, 2, 3],
        'form_code': [1, 2, 3],
        'hdd': [1, 2, 3],
        'T_h': [100, 200, -10]
    })
    mock_read_csv.return_value = df
    res = load_data()
    assert len(res) == 1
    assert res.iloc[0]['status'] == 'ok'
    assert res.iloc[0]['T_h'] == 100

@patch('src.inference.gp_emulator.COMBINED_CSV')
def test_load_data_missing(mock_combined):
    mock_combined.exists.return_value = False
    with pytest.raises(FileNotFoundError):
        load_data()

@patch('src.inference.gp_emulator.GaussianProcessRegressor')
@patch('src.inference.gp_emulator.STATS_PATH')
@patch('builtins.open')
def test_train_gp(mock_open, mock_stats_path, mock_gpr):
    # Create mock GP
    mock_gp = MagicMock()
    mock_gp.predict.side_effect = lambda X, return_std: (np.random.rand(len(X)), np.random.rand(len(X)))
    mock_gp.kernel_ = "mock_kernel"
    mock_gpr.return_value = mock_gp
    
    df = pd.DataFrame({
        'floor_area': np.random.rand(600),
        'wall_u': np.random.rand(600),
        'ach': np.random.rand(600),
        'wwr': np.random.rand(600),
        'form_code': np.random.rand(600),
        'hdd': np.random.rand(600),
        'T_h': np.random.rand(600)
    })
    
    with patch('src.inference.gp_emulator.r2_score', return_value=0.995):
        gp, scaler, X_test, y_test, y_pred, y_std, stats = train_gp(df)
        
    assert gp == mock_gp
    assert stats['acceptance_met'] is True

@patch('src.inference.gp_emulator.plt')
def test_plot_validation(mock_plt):
    mock_plt.subplots.return_value = (MagicMock(), [MagicMock(), MagicMock()])
    y_test = np.array([1, 2])
    y_pred = np.array([1.1, 1.9])
    y_std = np.array([0.1, 0.1])
    plot_validation(y_test, y_pred, y_std, 0.99)
    mock_plt.savefig.assert_called_once()

@patch('src.inference.gp_emulator.joblib.dump')
def test_save_model(mock_dump):
    save_model("gp", "scaler")
    mock_dump.assert_called_once()

@patch('src.inference.gp_emulator.MODEL_PATH')
@patch('src.inference.gp_emulator.STATS_PATH')
@patch('src.inference.gp_emulator.joblib.load')
@patch('src.inference.gp_emulator.load_data')
@patch('builtins.open')
def test_validate_saved(mock_open, mock_load_data, mock_load, mock_stats_path, mock_model_path):
    mock_model_path.exists.return_value = True
    mock_stats_path.exists.return_value = True
    
    mock_gp = MagicMock()
    mock_gp.predict.return_value = (np.array([1.0]), np.array([0.1]))
    mock_scaler = MagicMock()
    mock_load.return_value = {"gp": mock_gp, "scaler": mock_scaler}
    
    mock_df = pd.DataFrame({
        'floor_area': [1], 'wall_u': [1], 'ach': [1], 'wwr': [1], 'form_code': [1], 'hdd': [1], 'T_h': [100]
    })
    mock_load_data.return_value = mock_df
    
    with patch('src.inference.gp_emulator.json.load', return_value={"r2": 0.99}):
        validate_saved()

@patch('src.inference.gp_emulator.validate_saved')
def test_main_validate(mock_validate):
    main(validate=True)
    mock_validate.assert_called_once()

@patch('src.inference.gp_emulator.load_data')
@patch('src.inference.gp_emulator.train_gp')
@patch('src.inference.gp_emulator.save_model')
@patch('src.inference.gp_emulator.plot_validation')
def test_main(mock_plot, mock_save, mock_train, mock_load):
    mock_train.return_value = ("gp", "scaler", "X_test", "y_test", "y_pred", "y_std", {"r2": 0.99})
    main(validate=False)
    mock_load.assert_called_once()
    mock_train.assert_called_once()
    mock_save.assert_called_once()
    mock_plot.assert_called_once()
