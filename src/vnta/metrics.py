from __future__ import annotations

from typing import Dict, Tuple, Sequence
import numpy as np
import pandas as pd


def estimate_missing_bursts(seq_series: pd.Series) -> pd.DataFrame:
    """
    Estimate missing-burst events from sequence gaps.
    Returns rows with:
      index, prev_seq, curr_seq, missing_count
    """
    seq = seq_series.astype("int64").reset_index(drop=True)
    prev = seq.shift(1)
    gap = seq - prev

    bursts = []
    for idx, g in gap.items():
        if pd.isna(g):
            continue
        if g > 1:
            bursts.append(
                {
                    "index": int(idx),
                    "prev_seq": int(prev.iloc[idx]),
                    "curr_seq": int(seq.iloc[idx]),
                    "missing_count": int(g - 1),
                }
            )
    return pd.DataFrame(bursts)


def compute_metrics(
    df: pd.DataFrame,
    expected_period_ms: float,
    dev_thresholds_ms: Sequence[float] = (1.0, 5.0),
    spike_factor: float = 2.0,
) -> Tuple[Dict[str, str], pd.DataFrame, pd.DataFrame]:
    """
    Returns:
      summary: Dict[str, str]
      detail:  DataFrame with iat_ms, abs_dev_ms
      events:  DataFrame with notable timing issues and missing bursts
    Required columns:
      - ts_rx_ns (int): receive timestamp in ns
      - seq (int): sequence number
    Optional:
      - stream_id
    """
    work = df.copy()
    work = work.sort_values("ts_rx_ns").reset_index(drop=True)

    # Inter-arrival time (ms)
    work["iat_ms"] = work["ts_rx_ns"].diff() / 1e6
    work["abs_dev_ms"] = (work["iat_ms"] - expected_period_ms).abs()

    iat = work["iat_ms"].dropna()
    abs_dev = work["abs_dev_ms"].dropna()

    jitter_ms = float(iat.std(ddof=0)) if len(iat) else float("nan")
    mean_dev_ms = float(abs_dev.mean()) if len(abs_dev) else float("nan")
    p95_dev_ms = float(np.percentile(abs_dev, 95)) if len(abs_dev) else float("nan")

    # Loss / duplicates / out-of-order based on seq
    seq = work["seq"].astype("int64")
    seq_diff = seq.diff()
    duplicates = int((seq_diff == 0).sum())
    out_of_order = int((seq_diff < 0).sum())

    seq_min = int(seq.min())
    seq_max = int(seq.max())
    expected_total = (seq_max - seq_min + 1) if seq_max >= seq_min else 0
    observed_unique = int(seq.nunique())
    missing = max(expected_total - observed_unique, 0)
    loss_rate = (missing / expected_total) if expected_total > 0 else float("nan")

    # Threshold violations
    vio_counts: Dict[str, int] = {}
    for th in dev_thresholds_ms:
        key = f"violations_abs_dev_gt_{th:g}ms"
        vio_counts[key] = int((work["abs_dev_ms"] > th).sum())

    # Spike detection (large inter-arrival gaps)
    spike_iat_ms = expected_period_ms * spike_factor
    spike_count = int((work["iat_ms"] > spike_iat_ms).sum())

    # Events DataFrame (timing anomalies)
    events = work.dropna(subset=["iat_ms"]).copy()
    events["event_type"] = ""

    # Mark spikes
    events.loc[events["iat_ms"] > spike_iat_ms, "event_type"] = "iat_spike"

    # Threshold labels (strongest wins)
    for th in sorted(dev_thresholds_ms, reverse=True):
        mask = (events["abs_dev_ms"] > th) & (events["event_type"] == "")
        events.loc[mask, "event_type"] = f"abs_dev_gt_{th:g}ms"

    events = events[events["event_type"] != ""].copy()

    keep_cols = [c for c in ["ts_rx_ns", "seq", "iat_ms", "abs_dev_ms", "event_type", "stream_id"] if c in events.columns]
    events = events[keep_cols]

    # Missing burst events (seq gaps)
    bursts = estimate_missing_bursts(work["seq"])
    if not bursts.empty:
        bursts_events = bursts.copy()
        bursts_events["event_type"] = "missing_burst"
        bursts_events["ts_rx_ns"] = work.loc[bursts_events["index"], "ts_rx_ns"].values
        if "stream_id" in work.columns:
            bursts_events["stream_id"] = work.loc[bursts_events["index"], "stream_id"].values

        bursts_events = bursts_events[
            [c for c in ["ts_rx_ns", "prev_seq", "curr_seq", "missing_count", "event_type", "stream_id"] if c in bursts_events.columns]
        ]
        events = pd.concat([events, bursts_events], ignore_index=True, sort=False)

    summary: Dict[str, str] = {
        "packets_observed": str(len(work)),
        "seq_min": str(seq_min),
        "seq_max": str(seq_max),
        "missing_packets_est": str(missing),
        "loss_rate_est": f"{loss_rate:.4f}" if expected_total > 0 else "n/a",
        "iat_ms_mean": f"{float(iat.mean()):.3f}" if len(iat) else "n/a",
        "iat_ms_min": f"{float(iat.min()):.3f}" if len(iat) else "n/a",
        "iat_ms_max": f"{float(iat.max()):.3f}" if len(iat) else "n/a",
        "jitter_ms_std": f"{jitter_ms:.3f}" if len(iat) else "n/a",
        "abs_dev_ms_mean": f"{mean_dev_ms:.3f}" if len(abs_dev) else "n/a",
        "abs_dev_ms_p95": f"{p95_dev_ms:.3f}" if len(abs_dev) else "n/a",
        "duplicates": str(duplicates),
        "out_of_order": str(out_of_order),
        "iat_spike_threshold_ms": f"{spike_iat_ms:.3f}",
        "iat_spike_count": str(spike_count),
    }

    for k, v in vio_counts.items():
        summary[k] = str(v)

    if not bursts.empty:
        summary["missing_bursts_count"] = str(len(bursts))
        summary["missing_burst_max"] = str(int(bursts["missing_count"].max()))
    else:
        summary["missing_bursts_count"] = "0"
        summary["missing_burst_max"] = "0"

    return summary, work, events
