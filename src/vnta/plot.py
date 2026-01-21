from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def plot_iat_timeseries(detail: pd.DataFrame, outpath: Path) -> None:
    d = detail.dropna(subset=["iat_ms"]).copy()
    if d.empty:
        return

    plt.figure()
    plt.plot(d.index, d["iat_ms"])
    plt.xlabel("Packet Index")
    plt.ylabel("Inter-arrival time (ms)")
    plt.title("Inter-arrival time over packets")
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()


def plot_iat_hist(detail: pd.DataFrame, outpath: Path) -> None:
    d = detail.dropna(subset=["iat_ms"]).copy()
    if d.empty:
        return

    plt.figure()
    plt.hist(d["iat_ms"], bins=50)
    plt.xlabel("Inter-arrival time (ms)")
    plt.ylabel("Count")
    plt.title("Inter-arrival time histogram")
    plt.tight_layout()
    plt.savefig(outpath)
    plt.close()
