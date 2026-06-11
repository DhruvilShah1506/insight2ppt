import pandas as pd
from typing import Union


def load_csv(path: str) -> pd.DataFrame:
    """Simple CSV loader."""
    # Try common encodings to avoid UnicodeDecodeError on Windows/legacy files
    encodings = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']
    last_exc = None
    for enc in encodings:
        try:
            return pd.read_csv(path, encoding=enc)
        except Exception as e:
            last_exc = e
            continue
    # If all attempts fail, raise the last exception
    raise last_exc
