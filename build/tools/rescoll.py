#!/usr/bin/env python3
"""ETH Research Collection "Educational Material" (lecture scripts, course notes).

  python3 build/tools/rescoll.py list                 # all items' metadata -> data/rescoll_educational.json
  python3 build/tools/rescoll.py fetch <handle> <dir> # download the item's open-access PDFs into <dir>
"""
import json, sys, time
from pathlib import Path

import requests

API = "https://www.research-collection.ethz.ch/server/api"
S = requests.Session()
S.headers["User-Agent"] = "scrapbot/1.0 (study material collector)"


def mv(m, k):
    return [x["value"] for x in m.get(k, [])]


def list_all():
    items, page = [], 0
    while True:
        d = S.get(f"{API}/discover/search/objects", params=dict(
            query="*", size=100, page=page, **{"f.itemtype": "Educational Material,equals"}), timeout=60).json()
        r = d["_embedded"]["searchResult"]
        for o in r["_embedded"]["objects"]:
            it = o["_embedded"]["indexableObject"]
            m = it["metadata"]
            items.append(dict(uuid=it["uuid"], handle=it.get("handle"),
                              url=f"https://www.research-collection.ethz.ch/handle/{it.get('handle')}",
                              title=(mv(m, "dc.title") or [""])[0], authors=mv(m, "dc.contributor.author"),
                              date=(mv(m, "dc.date.issued") or [""])[0],
                              orgs=mv(m, "ethz.leitzahl.certified") + mv(m, "ethz.leitzahl"),
                              subjects=mv(m, "dc.subject"), abstract=(mv(m, "dc.description.abstract") or [""])[0],
                              rights=mv(m, "ethz.availability") + mv(m, "dc.rights.uri")))
        print(page, len(items), flush=True)
        page += 1
        if page >= r["page"]["totalPages"]:
            break
        time.sleep(0.5)
    Path("data/rescoll_educational.json").write_text(json.dumps(items, indent=1, ensure_ascii=False))


def fetch(uuid_or_handle, dst):
    dst = Path(dst); dst.mkdir(parents=True, exist_ok=True)
    if "/" in uuid_or_handle:
        uuid = S.get(f"{API}/pid/find", params=dict(id=f"hdl:{uuid_or_handle}"), timeout=60).json()["uuid"]
    else:
        uuid = uuid_or_handle
    bundles = S.get(f"{API}/core/items/{uuid}/bundles", timeout=60).json()["_embedded"]["bundles"]
    got = []
    for b in bundles:
        if b["name"] != "ORIGINAL":
            continue
        bs = S.get(b["_links"]["bitstreams"]["href"], timeout=60).json()["_embedded"]["bitstreams"]
        for x in bs:
            r = S.get(x["_links"]["content"]["href"], timeout=300)
            if r.status_code == 200 and r.content[:4] == b"%PDF":
                (dst / x["name"]).write_bytes(r.content); got.append(x["name"])
            else:
                print("  not open:", x["name"], r.status_code)
    print(uuid_or_handle, "->", got)
    return got


if __name__ == "__main__":
    if sys.argv[1] == "list":
        list_all()
    else:
        fetch(sys.argv[2], sys.argv[3])
