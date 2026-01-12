import pandas as pd

def to_dataframe(data: list):
    """
    Convert list of dicts to DataFrame safely
    """
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def hide_columns(df: pd.DataFrame, columns: list):
    """
    Remove unwanted columns from DataFrame
    """
    return df.drop(columns=columns, errors="ignore")


def select_columns(df: pd.DataFrame, columns: list):
    """
    Select only required columns
    """
    return df[columns]


def rename_columns(df: pd.DataFrame, mapping: dict):
    """
    Rename columns for display
    """
    return df.rename(columns=mapping)
