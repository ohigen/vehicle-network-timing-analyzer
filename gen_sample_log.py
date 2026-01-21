from __future__ import annotations

import argparse
import random
from pathlib import Path

import pandas as pd


def parse_args():
    p = argparse.ArgumentParser(description="Generate synthetic packet logs for VNTA")
    p.add_argument("--out", default="data/sample_packets.csv")
    p.add_argument("--stream", default="camera_front")
    p.add_argument("--n", type=int, default=2000)
    p.add_argument("--period-ms", type=float, default=33.333)
    p.add_argument("--jitter-ms", type=float, default=0.8)
    p.add_argument("--loss-rate", type=float, default=0.01)
    p.add_argument("--out-of-order-rate", type=float, default=0.0)
    p.add_argument("--seed", type=int, default=1)
    return p.parse_args()


def main():
    args = parse_args()
    random.seed(args.seed)

    ts_ns = 1700000000000000000
    period_ns = int(args.period_ms * 1e6)
    jitter_ns = int(args.jitter_ms * 1e6)

    rows = []
    seq = 0
    for _ in range(args.n):
        seq += 1

        # simulate loss by skipping some seq numbers
        if random.random() < args.loss_rate:
            ts_ns += period_ns + random.randint(-jitter_ns, jitter_ns)
            continue

        ts_ns += period_ns + random.randint(-jitter_ns, jitter_ns)
        rows.append({"ts_rx_ns": ts_ns, "seq": seq, "stream_id": args.stream})

    df = pd.DataFrame(rows)

    # simple out-of-order simulation by swapping adjacent seq values occasionally
    if args.out_of_order_rate > 0 and len(df) > 2:
        for i in range(len(df) - 1):
            if random.random() < args.out_of_order_rate:
                df.loc[i, "seq"], df.loc[i + 1, "seq"] = df.loc[i + 1, "seq"], df.loc[i, "seq"]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Wrote: {out} ({len(df)} rows)")


if __name__ == "__main__":
    main()
