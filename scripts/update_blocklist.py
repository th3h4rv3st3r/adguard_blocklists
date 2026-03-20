#!/usr/bin/env python3
"""
update_blocklist.py
Busca dominios de anuncios do YouTube nas listas upstream,
mescla com as regras customizadas e salva em blocklists/youtube-ads.txt
"""

import hashlib
import os
import re
import requests
from datetime import datetime, timezone

UPSTREAM_SOURCES = [
    {
        "name": "hagezi Pro",
        "url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/pro.txt",
        "filter": r"(youtube|doubleclick|googlevid|googlesyndication|googleadservices|adservice\.google)",
    },
    {
        "name": "EasyList",
        "url": "https://easylist.to/easylist/easylist.txt",
        "filter": r"(youtube|doubleclick|googlevid|googlesyndication|googleadservices|adservice\.google)",
    },
    {
        "name": "AdGuard Base",
        "url": "https://filters.adtidy.org/extension/ublock/filters/2.txt",
        "filter": r"(youtube|doubleclick|googlevid|googlesyndication|googleadservices|adservice\.google)",
    },
]

CUSTOM_RULES = """
! -- REGRAS CUSTOMIZADAS (sempre presentes) ------------------
||ad.doubleclick.net^
||googleads.g.doubleclick.net^
||pagead2.googlesyndication.com^
||pagead2.googleadservices.com^
||ads.youtube.com^
||ads2.youtube.com^
||youtube.com/api/stats/ads^
||youtube.com/pagead/^
||youtube.com/ptracking^
||youtube.com/youtubei/v1/log_event^
||youtubei.googleapis.com/youtubei/v1/log_event^
||www.youtube.com/api/stats/ads^
||www.youtube.com/ptracking^
||adservice.google.com^
||adservice.google.com.br^
||googleadservices.com^
||googlesyndication.com^
||tpc.googlesyndication.com^
||stats.g.doubleclick.net^
||cm.g.doubleclick.net^
||youtube.com/get_midroll_info^
||www.youtube.com/get_midroll_info^
||play.google.com/log^
||play.googleapis.com/log^
||beacons.gcp.gvt2.com^
""".strip()

OUTPUT_FILE = "blocklists/youtube-ads.txt"
HASH_FILE   = "blocklists/.upstream_hash"


def fetch_rules(source):
    try:
        resp = requests.get(source["url"], timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"  AVISO: Erro ao buscar {source['name']}: {e}")
        return set()

    pattern = re.compile(source["filter"], re.IGNORECASE)
    rules = set()

    for line in resp.text.splitlines():
        line = line.strip()
        if not line or line.startswith("!") or line.startswith("#"):
            continue
        if pattern.search(line):
            rules.add(line)

    print(f"  OK {source['name']}: {len(rules)} regras encontradas")
    return rules


def load_hash():
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE) as f:
            return f.read().strip()
    return ""


def save_hash(content):
    with open(HASH_FILE, "w") as f:
        f.write(hashlib.sha256(content.encode()).hexdigest())


def build_blocklist(all_rules):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "! Title: YouTube Ads Blocklist -- AdGuard Home",
        "! Description: Bloqueia anuncios do YouTube (atualizado automaticamente)",
        "! Homepage: https://github.com/th3h4rv3st3r/adguard_blocklists",
        f"! Version: {datetime.now(timezone.utc).strftime('%Y%m%d')}",
        f"! Last modified: {now}",
        "! Expires: 1 day",
        f"! Entries: {len(all_rules)}",
        "!",
        CUSTOM_RULES,
        "!",
        "! -- REGRAS IMPORTADAS DAS LISTAS UPSTREAM ------------------",
    ]
    lines += sorted(all_rules)
    return "\n".join(lines) + "\n"


def main():
    print("Buscando listas upstream...")

    upstream_rules = set()
    for source in UPSTREAM_SOURCES:
        upstream_rules |= fetch_rules(source)

    for line in CUSTOM_RULES.splitlines():
        if line and not line.startswith("!"):
            upstream_rules.discard(line)

    content = build_blocklist(upstream_rules)
    new_hash = hashlib.sha256(content.encode()).hexdigest()
    old_hash = load_hash()

    if new_hash == old_hash:
        print("Nenhuma mudanca detectada. Nada para commitar.")
        return

    os.makedirs("blocklists", exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        f.write(content)

    save_hash(content)
    print(f"Lista atualizada -> {OUTPUT_FILE} ({len(upstream_rules)} regras upstream)")


if __name__ == "__main__":
    main()
