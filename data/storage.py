import pandas as pd
from pathlib import Path
from typing import Optional

def save_parquet(df: pd.DataFrame, path: Path, compression: str = "snappy"):
    """Save DataFrame to Parquet with compression."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, compression=compression, index=False)

def load_parquet(path: Path) -> Optional[pd.DataFrame]:
    """Load DataFrame from Parquet if exists."""
    if path.exists():
        return pd.read_parquet(path)
    return None

def append_parquet(df: pd.DataFrame, path: Path):
    """Append data to existing Parquet or create new."""
    if path.exists():
        existing = pd.read_parquet(path)
        combined = pd.concat([existing, df]).drop_duplicates(subset=['timestamp']).sort_values('timestamp')
        save_parquet(combined, path)
    else:
        save_parquet(df, path)
