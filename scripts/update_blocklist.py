#!/usr/bin/env python3
import hashlib, os, re, requests
from datetime import datetime, timezone

UPSTREAM_SOURCES = [
    {"name": "hagezi Pro",    "url": "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/adblock/pro.txt",  "filter": r"(youtube|doubleclick|googlesyndication|googleadservices|adservice\.google)"},
    {"name": "EasyList",      "url": "https://easylist.to/easylist/easylist.txt",                                      "filter": r"(youtube|doubleclick|googlesyndication|googleadservices|adservice\.google)"},
    {"name": "AdGuard Base",  "url": "https://filters.adtidy.org/extension/ublock/filters/2.txt",                     "filter": r"(youtube|doubleclick|googlesyndication|googleadservices|adservice\.google)"},
]

CUSTOM_RULES = [
    "! ── REGRAS CUSTOMIZADAS ────────────────────────────────────",
    "||ad.doubleclick.net^", "||googleads.g.doubleclick.net^",
    "||pagead2.googlesyndication.com^", "||pagead2.googleadservices.com^",
    "||ads.youtube.com^", "||ads2.youtube.com^",
    "||adservice.google.com^", "||adservice.google.com.br^",
    "||googleadservices.com^", "||googlesyndication.com^",
    "||tpc.googlesyndication.com^", "||stats.g.doubleclick.net^",
    "||cm.g.doubleclick.net^", "||youtube.com/get_midroll_info^",
    "||www.youtube.com/get_midroll_info^", "||play.google.com/log^",
    "||play.googleapis.com/log^", "||beacons.gcp.gvt2.com^",
]

OUTPUT_FILE = "blocklists/youtube-ads.txt"
HASH_FILE   = "blocklists/.upstream_hash"

def fetch_rules(source):
    try:
        resp = requests.get(source["url"], timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"  WARNING: {source['name']}: {e}"); return set()
    pattern = re.compile(source["filter"], re.IGNORECASE)
    rules = {l.strip() for l in resp.text.splitlines() if l.strip() and not l.startswith(("!","#")) and pattern.search(l)}
    print(f"  OK {source['name']}: {len(rules)} regras"); return rules

def load_hash():
    return open(HASH_FILE).read().strip() if os.path.exists(HASH_FILE) else ""

def save_hash(content):
    os.makedirs(os.path.dirname(HASH_FILE), exist_ok=True)
    open(HASH_FILE,"w").write(hashlib.sha256(content.encode()).hexdigest())

def build_output(upstream_rules):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    custom_set = {r for r in CUSTOM_RULES if not r.startswith("!")}
    upstream_only = sorted(upstream_rules - custom_set)
    header = [
        "! Title: YouTube Ads Blocklist",
        "! Description: Bloqueia anuncios do YouTube para AdGuard Home",
        "! Homepage: https://github.com/th3h4rv3st3r/adguard_blocklists",
        f"! Last modified: {now}",
        f"! Entries: {len(custom_set) + len(upstream_only)}",
        "! Expires: 1 day", "!",
    ]
    return "\n".join(header + CUSTOM_RULES + ["!", "! ── REGRAS UPSTREAM ─────────────────────────────────────────"] + upstream_only) + "\n"

def main():
    print("Buscando listas upstream...")
    upstream_rules = set()
    for s in UPSTREAM_SOURCES: upstream_rules |= fetch_rules(s)
    content = build_output(upstream_rules)
    if hashlib.sha256(content.encode()).hexdigest() == load_hash():
        print("Sem mudancas."); return
    os.makedirs("blocklists", exist_ok=True)
    open(OUTPUT_FILE,"w").write(content)
    save_hash(content)
    print(f"Lista atualizada -> {OUTPUT_FILE} ({len(upstream_rules)} regras)")

if __name__ == "__main__": main()