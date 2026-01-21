from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.vnta.io import load_csv
from src.vnta.metrics import compute_metrics
from src.vnta.plot import plot_iat_hist, plot_iat_timeseries


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Vehicle Network Timing Analyzer (VNTA)")
    p.add_argument("--csv", required=True, help="Path to CSV file (ts_rx_ns, seq, stream_id)")
    p.add_argument("--period-ms", type=float, default=33.333, help="Expected period in ms")
    p.add_argument("--stream", default=None, help="Filter by stream_id (optional)")
    p.add_argument("--outdir", default="out", help="Output directory for outputs")
    p.add_argument("--plots", action="store_true", help="Generate plots")
    p.add_argument("--events", action="store_true", help="Write event list CSV (spikes / threshold violations / missing bursts)")
    p.add_argument("--summary-by-stream", action="store_true", help="Print summary table for each stream_id")
    p.add_argument("--dev-thresholds", default="1,5", help="Comma-separated abs deviation thresholds in ms (e.g. 1,5)")
    p.add_argument("--spike-factor", type=float, default=2.0, help="Spike threshold = expected_period_ms * spike_factor")
    p.add_argument("--format", choices=["text", "json"], default="text", help="Output format for summary")
    p.add_argument("--report", default=None, help="Write JSON report to this path (optional)")
    p.add_argument(
        "--fail-on-abs-dev-gt",
        type=float,
        default=None,
        help="Exit with code 2 if violations_abs_dev_gt_Xms > 0 (X in ms). Example: --fail-on-abs-dev-gt 5",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    csv_path = Path(args.csv)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = load_csv(csv_path)

    if args.stream and "stream_id" in df.columns:
        df = df[df["stream_id"] == args.stream].copy()

    dev_thresholds = tuple(float(x.strip()) for x in args.dev_thresholds.split(",") if x.strip())

    metrics, detail, events = compute_metrics(
        df,
        expected_period_ms=args.period_ms,
        dev_thresholds_ms=dev_thresholds,
        spike_factor=args.spike_factor,
    )

    # Output summary
    if args.format == "text":
        print("\n=== VNTA SUMMARY ===")
        for k, v in metrics.items():
            print(f"{k}: {v}")
    else:
        print(json.dumps(metrics, indent=2))

    # Report JSON
    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"\nSaved report to: {report_path}")

    # Optional plots
    if args.plots:
        ts_plot = outdir / "iat_timeseries.png"
        hist_plot = outdir / "iat_hist.png"
        plot_iat_timeseries(detail, ts_plot)
        plot_iat_hist(detail, hist_plot)
        print(f"\nSaved plots to: {outdir}")

    # Optional events.csv
    if args.events:
        events_path = outdir / "events.csv"
        events.to_csv(events_path, index=False)
        print(f"Saved events to: {events_path}")

    # Optional per-stream summary table
    if args.summary_by_stream and "stream_id" in df.columns:
        rows = []
        for sid, g in df.groupby("stream_id"):
            m, _, _ = compute_metrics(
                g,
                expected_period_ms=args.period_ms,
                dev_thresholds_ms=dev_thresholds,
                spike_factor=args.spike_factor,
            )
            rows.append(
                {
                    "stream_id": sid,
                    "packets": int(m["packets_observed"]),
                    "loss_rate": float(m["loss_rate_est"]) if m["loss_rate_est"] != "n/a" else None,
                    "jitter_ms": float(m["jitter_ms_std"]) if m["jitter_ms_std"] != "n/a" else None,
                    "abs_dev_p95_ms": float(m["abs_dev_ms_p95"]) if m["abs_dev_ms_p95"] != "n/a" else None,
                    "spike_count": int(m["iat_spike_count"]),
                    "missing_burst_max": int(m.get("missing_burst_max", "0")),
                }
            )

        table = pd.DataFrame(rows).sort_values("stream_id")
        print("\n=== SUMMARY BY STREAM ===")
        print(table.to_string(index=False))

    # Fail-on threshold (CI-friendly)
    if args.fail_on_abs_dev_gt is not None:
        key = f"violations_abs_dev_gt_{args.fail_on_abs_dev_gt:g}ms"
        count = int(metrics.get(key, "0"))
        if count > 0:
            print(f"\nFAIL: {key} = {count} > 0")
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
