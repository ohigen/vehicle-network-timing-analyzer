from __future__ import annotations

from pathlib import Path
import pandas as pd


def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Normalize column names (strip spaces / BOM)
    df.columns = [c.strip().lstrip("\ufeff") for c in df.columns]

    # Required columns
    if "ts_rx_ns" not in df.columns or "seq" not in df.columns:
        raise ValueError(f"CSV must contain ts_rx_ns and seq. Found: {list(df.columns)}")

    df["ts_rx_ns"] = pd.to_numeric(df["ts_rx_ns"], errors="coerce")
    df["seq"] = pd.to_numeric(df["seq"], errors="coerce")

    df = df.dropna(subset=["ts_rx_ns", "seq"]).copy()
    df["ts_rx_ns"] = df["ts_rx_ns"].astype("int64")
    df["seq"] = df["seq"].astype("int64")

    return df
