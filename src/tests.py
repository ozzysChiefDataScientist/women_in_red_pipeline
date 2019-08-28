import pandas as pd

def test_key(df,key_col_names):
    '''
    Test if keys specified in key_col_names are primary keys
    :param df: A Pandas data frame
    :param key_col_names: A list with names of key columns
    '''
    row_cts = df.fillna("").groupby(key_col_names).count().reset_index()
    assert max(row_cts.iloc[:,-1]) == 1