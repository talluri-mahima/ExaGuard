\# ExaGuard



Evidence-first financial crime topology investigations on Exasol Personal



\## Problem

Traditional fraud detection systems mostly look at single transactions. Real financial crime often appears as multi-account topologies (cycles, layering, fan-out/fan-in, mule networks). Investigators need clear, auditable evidence — not just a black-box score.



\## Solution

ExaGuard loads a synthetic but realistic transaction ledger into \*\*Exasol Personal\*\*, runs topology-aware detection, stores deterministic evidence with hashes, and presents an investigation interface. Ground-truth labels are never used as detector features.



\## Track

Primary: Predict, Detect \& Optimize  

Secondary: AI Trust, Safety \& Governance



\## Architecture

\- Synthetic data generator (`data/generate\_dataset.py`)

\- Exasol Personal as the system of record

\- FastAPI service for queries and detection

\- Streamlit investigation UI

\- Evidence stored with deterministic hashes for auditability



\## Quick Start



\### Prerequisites

\- Python 3.11+

\- Exasol Personal running (local or cloud)

\- Git



\### 1. Install dependencies

```bash

python -m venv .venv

.venv\\Scripts\\activate

pip install -r requirements.txt

