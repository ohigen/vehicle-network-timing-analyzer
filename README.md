# Vehicle Network Timing Analyzer (VNTA)

A small, self-contained Python tool that demonstrates how to analyze **latency, jitter, and packet loss** from synthetic vehicle network packet logs.

In production automotive systems, periodic data streams exchanged between ECUs and sensors (e.g., over Ethernet/UDP) can exhibit timing variation due to scheduling, load, buffering, and network effects. Commercial tools are typically used in such environments; this project focuses on **understanding and validating the underlying timing metrics** that those tools report, rather than replacing them.

> Note: All logs in this repository are synthetic and do not represent any proprietary system.

---

## Features

* **Inter-arrival time (IAT)** analysis (min / mean / max)
* **Jitter estimation** using standard deviation of IAT
* **Deviation from expected period** (mean and p95)
* **Sequence-based integrity checks**:

  * packet loss estimation
  * duplicate packets
  * out-of-order packets
* **Threshold-based event detection** for timing anomalies
* Optional visualizations:

  * IAT time series
  * IAT histogram
* Optional outputs:

  * event list CSV for debugging and triage
  * per-stream summary for multi-sensor logs

---

## Input Format

CSV file with the following columns:

* `ts_rx_ns` : receive timestamp in nanoseconds
* `seq` : sequence number
* `stream_id` (optional) : stream identifier (e.g., `camera_front`, `radar_front`)

Example:

```csv
ts_rx_ns,seq,stream_id
1700000000000000000,1,camera_front
1700000000033333333,2,camera_front
```

---

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt 
```

Run analysis with plots:

```bash
python cli.py --csv data/sample_packets.csv --period-ms 33.333 --plots
```

Generate event list and per-stream summary:

```bash
python cli.py --csv data/sample_packets.csv --period-ms 33.333 --events --summary-by-stream
```

---

## Running with VS Code and Virtual Environment (Optional)

This project can be run using a Python virtual environment and VS Code for convenience.

### Create and activate a virtual environment

```bash
python -m venv .venv
```

On Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install pandas numpy matplotlib
```

---

## Synthetic Log Generation

A helper script is included to generate synthetic packet logs for testing and demonstration purposes.

Example:

```bash
python gen_sample_log.py \
  --n 2000 \
  --period-ms 33.333 \
  --jitter-ms 0.8 \
  --loss-rate 0.01 \
  --out-of-order-rate 0.001
```

This allows controlled reproduction of timing jitter, packet loss, and out-of-order behavior.

---

## Typical Use Cases

* Sanity-checking timing behavior reported by commercial network analysis tools
* Identifying timing spikes, jitter, or packet loss during bench or vehicle testing
* Comparing timing stability across multiple ECU or sensor streams
* Supporting validation and debugging of automotive embedded and ADAS systems

---

## Design Notes

* The code is intentionally kept **small and modular** to emphasize clarity and reasoning.
* All metrics are derived directly from timestamps and sequence numbers to remain tool-agnostic.
* The structure reflects common validation workflows rather than production deployment code.

This repository reflects validation and debugging approaches commonly used in production automotive environments.
