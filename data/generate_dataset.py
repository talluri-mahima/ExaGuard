"""Seeded PaySim-shaped ledger; synthetic scenarios, not a PaySim distribution replica.

Ground truth is a separate artifact and never supplied to the detection sweep.
Amounts are generated and persisted in integer cents / decimal strings.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

PROVENANCE = {
    "simulated": True,
    "authored": "2026-09-13",
    "basis": "Original seeded PaySim-shaped synthetic ledger; not the PaySim dataset.",
    "warning": "SIMULATED DATA - no real people, accounts, or financial activity.",
}
TXN_COLUMNS = ["TXN_ID", "TS", "SRC_ACCT", "DST_ACCT", "AMOUNT", "TXN_TYPE",
               "CHANNEL", "IS_FLAGGED_LEGACY", "IS_FRAUD_LABEL"]
ACCOUNT_COLUMNS = ["ACCT_ID", "CUSTOMER_NAME", "OPENED_TS", "KYC_TIER", "COUNTRY",
                   "DEVICE_FP", "EMAIL", "PHONE", "RISK_BASE", "PROFILE_VEC"]
START = datetime(2026, 9, 1)


def generate(out: Path, rows: int = 1_000_000, accounts: int = 50_000,
             seed: int = 42, rings: int = 50) -> dict:
    if rows < 2000 or accounts < 1000 or rings != 50:
        raise ValueError("Use >=2,000 rows, >=1,000 accounts and 50 scenarios")
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    acct = lambda n: f"A{n:06d}"
    # Reserve randomly sampled accounts, so account prefixes cannot reveal labels.
    selected = rng.sample(range(100, accounts), 700)
    reserved = set(selected)
    normal = [n for n in range(100, accounts) if n not in reserved]
    profiles: dict[int, dict] = {}
    transactions: list[list] = []
    truth = []

    def emit(src: int, dst: int, cents: int, at: datetime, label: int,
             kind: str = "TRANSFER") -> str:
        tid = f"T{len(transactions):09d}"
        transactions.append([tid, at.isoformat(sep=" "), acct(src), acct(dst),
                             f"{cents // 100}.{cents % 100:02d}", kind, "MOBILE",
                             int(cents >= 1_000_000), label])
        return tid

    types = ["CYCLE", "FANOUT_FANIN", "LAYERING", "IDENTITY_CLUSTER", "MULE_BURST"]
    for i in range(50):
        members = selected[i * 10:i * 10 + 10]
        typology = types[i % 5]
        at = START + timedelta(days=10, minutes=i * 20)
        ids = []
        if typology in {"CYCLE", "LAYERING"}:
            n = 3 + i % 4
            members = members[:n if typology == "CYCLE" else n + 1]
            for j in range(n):
                ids.append(emit(members[j], members[(j + 1) % len(members)],
                                920_000 - j * 10_000, at + timedelta(seconds=45 * j), 1))
        elif typology == "FANOUT_FANIN":
            members = members[:7]
            for j in range(1, 6):
                ids.append(emit(members[0], members[j], 930_000,
                                at + timedelta(seconds=j), 1))
                ids.append(emit(members[j], members[6], 920_000,
                                at + timedelta(seconds=60 + j), 1))
        elif typology == "IDENTITY_CLUSTER":
            members = members[:5]
            for j, member in enumerate(members):
                profiles[member] = {"device": f"shared-{i}", "phone": f"+1555{i:04d}{j:03d}",
                                    "vec": [0.8, 0.2, 0.7, 0.1 + j * 0.001],
                                    "opened": "2026-08-30 09:00:00"}
                ids.append(emit(member, members[(j + 1) % 5], 410_000 + j * 1_000,
                                at + timedelta(seconds=j * 40), 1))
        else:
            members = members[:9]
            for j in range(1, 9):
                ids.append(emit(members[0], members[j], 740_000 + j * 500,
                                at + timedelta(seconds=j * 10), 1))
        truth.append({"ring_id": f"G{i:03d}", "typology": typology,
                      "members": [acct(n) for n in members], "txn_ids": ids})

    # Hard negatives: legitimate rapid treasury cycles and split payments. These are
    # intentionally detectable; a topology detector cannot infer legal intent.
    for i in range(10):
        m = selected[500 + i * 4:504 + i * 4]
        at = START + timedelta(days=10, hours=20, minutes=i * 5)
        for j in range(4):
            emit(m[j], m[(j + 1) % 4], 880_000 - j * 5_000,
                 at + timedelta(seconds=j * 40), 0)

    while len(transactions) < rows:
        src = rng.choice(normal)
        # Merchant hubs and benign larger transfers produce realistic rule noise.
        is_payment = rng.random() < 0.72
        dst = rng.randrange(100) if is_payment else rng.choice(normal)
        if src == dst:
            continue
        cents = max(100, min(8_000_000, int(rng.lognormvariate(10.0, 1.5))))
        at = START + timedelta(days=rng.randrange(12), hours=rng.randrange(8, 22),
                               minutes=rng.randrange(60), seconds=rng.randrange(60))
        emit(src, dst, cents, at, 0, "PAYMENT" if is_payment else rng.choice(["TRANSFER", "CASH_OUT"]))

    with (out / "transactions.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(TXN_COLUMNS)
        writer.writerows(sorted(transactions, key=lambda x: (x[1], x[0])))
    with (out / "accounts.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(ACCOUNT_COLUMNS)
        for n in range(accounts):
            p = profiles.get(n, {})
            writer.writerow([acct(n), f"Synthetic customer {n:06d}",
                             p.get("opened", "2025-01-01 09:00:00"),
                             "STANDARD", rng.choice(["IN", "SG", "GB", "AE"]),
                             p.get("device", f"device-{n}"), f"user{n}@example.invalid",
                             p.get("phone", f"+1999{n:08d}"), "0.10",
                             json.dumps(p.get("vec", [round(rng.random(), 4) for _ in range(4)]))])
    meta = {"_provenance": PROVENANCE, "seed": seed, "rows": rows,
            "accounts": accounts, "currency": "USD", "as_of": "2026-09-13T00:00:00Z",
            "rings": truth, "hard_negative_cycles": 10}
    meta["snapshot_id"] = hashlib.sha256((out / "transactions.csv").read_bytes()).hexdigest()
    (out / "ground_truth.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (out / "provenance.json").write_text(json.dumps({k: v for k, v in meta.items() if k != "rings"}, indent=2), encoding="utf-8")
    return {k: v for k, v in meta.items() if k != "rings"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=1_000_000)
    parser.add_argument("--accounts", type=int, default=50_000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("data/generated"))
    args = parser.parse_args()
    print(json.dumps(generate(args.out, args.rows, args.accounts, args.seed), indent=2))
