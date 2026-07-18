import pandas as pd
from src.utils.clean_results import clean_results_data

def test_clean_results_data():
    df = pd.DataFrame({
        'msoa21cd': ['E02000001', 'msoa21cd', 'E02000002', 'E02000003', 'E02000001'],
        'val': ['1.0', 'val', '2.0', 'invalid', '1.0']
    })
    imd = ['E02000001', 'E02000002']
    res = clean_results_data(df, imd)
    assert len(res) == 2
    assert 'E02000001' in res['msoa21cd'].values
    assert 'E02000002' in res['msoa21cd'].values
    assert res['val'].dtype == float
    assert res.loc[res['msoa21cd'] == 'E02000001', 'val'].iloc[0] == 1.0
