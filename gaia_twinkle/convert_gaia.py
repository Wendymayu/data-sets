"""Convert GAIA validation parquet → harness eval-set jsonl.

Presets:
  --preset easy         -> L1, no-attachment            -> data/easy/tasks.jsonl
  --preset medium       -> L2, no-attachment            -> data/medium/tasks.jsonl
  --preset hard         -> L3, no-attachment            -> data/hard/tasks.jsonl
  --preset attachments  -> any level, WITH attachment   -> data/attachments/tasks.jsonl
Or use --parquet/--out/--level/--no-attachment/--with-attachment/--limit manually.

GAIA is a gated dataset (HF license: do NOT reshare validation/test in a
crawlable format). The parquet and derived jsonl are gitignored, never committed.
Requires pyarrow (pip install pyarrow).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # Windows GBK console

import pyarrow.parquet as pq

from gaia_twinkle.runner import Sample

PRESETS = {
    "easy":        {"level": 1,    "no_attachment": True,  "with_attachment": False, "out": "gaia_twinkle/data/easy/tasks.jsonl"},
    "medium":      {"level": 2,    "no_attachment": True,  "with_attachment": False, "out": "gaia_twinkle/data/medium/tasks.jsonl"},
    "hard":        {"level": 3,    "no_attachment": True,  "with_attachment": False, "out": "gaia_twinkle/data/hard/tasks.jsonl"},
    "attachments": {"level": None, "no_attachment": False, "with_attachment": True,  "out": "gaia_twinkle/data/attachments/tasks.jsonl"},
}
DEFAULT_PARQUET = "gaia_twinkle/data/gaia/2023/validation/metadata.parquet"


def convert(
    parquet_path: str,
    out_path: str,
    level: int | None = None,
    only_no_attachment: bool = False,
    only_with_attachment: bool = False,
    limit: int | None = None,
) -> list[Sample]:
    rows = pq.read_table(parquet_path).to_pylist()
    samples: list[Sample] = []
    for r in rows:
        if level is not None and int(r.get("Level", 0)) != level:
            continue
        fname = str(r.get("file_name") or "").strip()
        if only_no_attachment and fname:
            continue
        if only_with_attachment and not fname:
            continue
        samples.append(Sample(
            task_id=r["task_id"],
            question=r["Question"],
            ground_truth=str(r["Final answer"]),
            level=int(r.get("Level", 1)),
            attachment=fname or None,
        ))
        if limit and len(samples) >= limit:
            break
    out = pathlib.Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "\n".join(json.dumps(s.__dict__, ensure_ascii=False) for s in samples) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(samples)} tasks -> {out}")
    return samples


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Convert GAIA validation parquet -> harness jsonl.")
    p.add_argument("--preset", choices=sorted(PRESETS), default=None,
                   help="easy/medium/hard(L无附件) / attachments(带附件)")
    p.add_argument("--parquet", default=DEFAULT_PARQUET, help="path to metadata[.levelN].parquet")
    p.add_argument("--out", default=None, help="output jsonl (default: per --preset)")
    p.add_argument("--level", type=int, default=None, help="filter to level 1/2/3")
    p.add_argument("--no-attachment", action="store_true", help="only tasks WITHOUT file attachments")
    p.add_argument("--with-attachment", action="store_true", help="only tasks WITH file attachments")
    p.add_argument("--limit", type=int, default=None, help="cap number of tasks")
    args = p.parse_args(argv)

    cfg = dict(PRESETS[args.preset]) if args.preset else {}
    out = args.out or cfg.get("out")
    level = args.level if args.level is not None else cfg.get("level")
    no_att = args.no_attachment or cfg.get("no_attachment", False)
    with_att = args.with_attachment or cfg.get("with_attachment", False)
    if not out:
        p.error("--out or --preset required")
    convert(args.parquet, out, level, no_att, with_att, args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
