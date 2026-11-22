#!/usr/bin/env python3
"""Static checker for the news-image-20261122 v1 entry. No network.

Checks the story data (counts, numbering, regions, tags, forbidden
strings), then renders twice and checks determinism, size and dimensions.
Exit 0 = all pass.
"""

import hashlib
import os
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import main as M  # noqa: E402  (importing main only loads data + fonts)

FAIL = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        FAIL.append(msg)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def main():
    # ---- story data ------------------------------------------------------
    check(len(M.LEADS) == 13, "13 leads")
    check(len(M.BRIEFS) == 22, "22 briefs")
    check(len(M.LEADS) + len(M.BRIEFS) == 35, "35 stories total")
    check(len(M.DATE_CHECK) == 10, "DATE CHECK has 10 items")
    check([l[0] for l in M.LEADS] == list(range(1, 14)),
          "leads numbered 1-13")
    check([b[0] for b in M.BRIEFS] == list(range(14, 36)),
          "briefs numbered 14-35")
    counts = Counter([l[2] for l in M.LEADS] + [b[1] for b in M.BRIEFS])
    expect = {"Europe": 9, "Middle East": 7, "Americas": 7,
              "Asia-Pacific": 6, "Oceania": 3, "Africa": 2, "World": 1}
    check(dict(counts) == expect, "region counts %s" % dict(counts))
    check(all(l[6] in ("REPORTED", "CLAIM") for l in M.LEADS),
          "lead tags are REPORTED/CLAIM")
    check([l[0] for l in M.LEADS if l[6] == "CLAIM"] == [2],
          "CLAIM tag only on L2 (IRGC claim)")
    check(sorted(b[0] for b in M.BRIEFS if b[4] == "FORECAST") == [28, 32],
          "FORECAST tag only on B15/B19 (items 28, 32)")
    check(all(l[3] and l[4] for l in M.LEADS), "every lead has headline+body")
    check(all(b[2] and b[3] for b in M.BRIEFS),
          "every brief has headline+body")
    # forbidden strings in the Sunday stories themselves (the DATE CHECK box
    # is allowed to name them as excluded items).
    text = " ".join(l[3] + " " + l[4] for l in M.LEADS)
    text += " " + " ".join(b[2] + " " + b[3] for b in M.BRIEFS)
    check("400 drone" not in text and "400-drone" not in text,
          "no 400-drone barrage claimed as Sunday news")
    check("Bayelsa 26" not in text and "toll 26" not in text,
          "no Bayelsa toll 26 (correct toll is 24)")
    check("$3,553" not in text, "no stale gold $3,553 (corrected to $3,515)")
    check("$3,515" in text, "gold $3,515 present (B16 corrected)")
    check("22 NOVEMBER 2026" in open(os.path.join(HERE, "main.py")).read(),
          "date Sunday 22 November 2026 named in the program")

    # ---- render: determinism, size, dimensions ---------------------------
    tmp = os.path.join(HERE, ".verify-tmp")
    os.makedirs(tmp, exist_ok=True)
    outs = []
    for i in (1, 2):
        out = os.path.join(tmp, "entry-%d.png" % i)
        env = dict(os.environ, ENTRY_OUTPUT=out)
        r = subprocess.run([sys.executable, os.path.join(HERE, "main.py")],
                           env=env, capture_output=True, text=True)
        check(r.returncode == 0, "render run %d exits 0" % i)
        if r.stderr.strip():
            print("  render stderr: %s" % r.stderr.strip())
        outs.append(out)
    h1, h2 = sha256(outs[0]), sha256(outs[1])
    check(h1 == h2, "deterministic render (sha256 %s...)" % h1[:12])
    size = os.path.getsize(outs[0])
    check(size <= 1048576, "entry.png %d bytes <= 1 MiB" % size)
    check(200000 <= size <= 350000,
          "entry.png %d bytes in target 200-350 KB band" % size)
    from PIL import Image
    im = Image.open(outs[0])
    check(im.size == (1024, 1024), "entry.png is 1024x1024 (got %s)" % (im.size,))
    ref = os.path.join(HERE, "entry.png")
    if os.path.exists(ref):
        check(sha256(ref) == h1, "committed entry.png matches fresh render")
    else:
        print("SKIP committed entry.png not present")

    print()
    if FAIL:
        print("%d FAILURES" % len(FAIL))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
