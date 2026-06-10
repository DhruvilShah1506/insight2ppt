import pandas as pd
from typing import Union


def load_csv(path: str) -> pd.DataFrame:
    """Simple CSV loader."""
    return pd.read_csv(path)


def load_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy()
