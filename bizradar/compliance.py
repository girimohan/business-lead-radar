"""Which channels are lawful for each lead, an opt-out list that always wins, and retention.

The rules (details and sources in docs/legal-research.md):
- Email, SMS and other electronic direct marketing to a NATURAL person needs prior consent
  (Laki sähköisen viestinnän palveluista 917/2014, § 200). A sole trader (toiminimi / yksityinen
  elinkeinonharjoittaja) is a natural person. So: no cold email or SMS to a toiminimi.
- To a LEGAL person (Oy, Ky, Ay, osuuskunta) electronic direct marketing to its generic address is allowed
  unless it has refused (§ 202). A named employee's own address is a natural person's address: consent is
  needed unless their duties are essentially related to the offer (asemavaltuus), which must be checked and
  documented first (TSV FAQ; TSV decision 3578/157/2019). Being a sole trader does not give asemavaltuus.
- Phone, letter and an in-person visit are allowed to both unless the business has said no.
- Unknown company form is treated as a natural person: the strict rule applies until PRH shows otherwise.
- GDPR: data about a toiminimi, and named people at companies, is personal data. Lawful basis is legitimate
  interest (Art. 6(1)(f)) with a written balancing test; the first message must carry the Art. 14 notice
  (who you are, where you got the data, how to object). An objection (Art. 21) is final.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .models import Business

LEGAL_PERSON = {"oy", "ky", "ay", "osk", "other"}


def channels(b: Business) -> dict:
    """{channel: {allowed: bool, why: str, to: str}} for this business."""
    legal = b.legal_form in LEGAL_PERSON and b.legal_form_source == "prh"
    likely_legal = b.legal_form in LEGAL_PERSON   # from the name only: good, not proof
    generic = next((e for e in b.emails if e.kind == "generic"), None)
    personal = next((e for e in b.emails if e.kind == "personal"), None)
    out: dict[str, dict] = {}

    if not b.emails:
        out["email"] = {"allowed": False, "why": "no address published on the business's own website", "to": ""}
    elif legal and generic:
        out["email"] = {"allowed": True, "to": generic.address,
                        "why": f"registered {b.legal_form.upper()} (PRH): opt-out rule, generic business address"}
    elif legal and personal:
        # TSV: a named employee's address is a natural person's address. Opt-out applies only if their duties
        # are essentially related to the offer (asemavaltuus), checked and documented before sending.
        out["email"] = {"allowed": False, "to": personal.address, "role_unlock": True,
                        "why": f"registered {b.legal_form.upper()} (PRH), but this is a named person's address: "
                               "needs their consent, or a documented check that their role (owner, manager) is "
                               "directly about what you offer"}
    elif likely_legal:
        out["email"] = {"allowed": False, "to": "",
                        "why": "name says company, but PRH has not confirmed it: check the Y-tunnus on ytj.fi first"}
    else:
        out["email"] = {"allowed": False, "to": "",
                        "why": "sole trader or unknown company form: email marketing needs the person's prior consent"}
    out["sms"] = {"allowed": False, "to": "",
                  "why": "not used: consent needed for sole traders, and texting a company's mobile reaches a person"}
    out["phone"] = ({"allowed": True, "to": b.phone, "why": "phone calls to businesses are allowed unless they refuse"}
                    if b.phone else {"allowed": False, "to": "", "why": "no published phone number"})
    addr = ", ".join(x for x in (b.street, f"{b.postcode} {b.city}".strip()) if x)
    out["letter"] = ({"allowed": True, "to": f"{b.name}, {addr}", "why": "addressed letter to the business"}
                     if b.street else {"allowed": False, "to": "", "why": "no street address"})
    out["visit"] = ({"allowed": True, "to": addr, "why": "a short visit outside the busiest hours"}
                    if b.street else {"allowed": False, "to": "", "why": "no street address"})
    out["form"] = ({"allowed": legal, "to": b.contact_form,
                    "why": "contact form on a registered company's site: same rule as email" if legal else
                           "a contact form is electronic mail too: not for sole traders without consent"}
                   if b.contact_form else {"allowed": False, "to": "", "why": "no contact form"})
    return out


def best_channel(ch: dict) -> str:
    for k in ("email", "phone", "visit", "letter"):
        if ch.get(k, {}).get("allowed"):
            return k
    return ""


class OptOut:
    """data/optout.json: businesses that said no. Kept for as long as needed to honour it, and nothing else.

    Each entry stores only the identifiers needed to recognise the business again (business ID, domain,
    email, phone, name+postcode), the date, and how they said it.
    """

    def __init__(self, path: Path):
        self.path = path
        try:
            self.entries = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.entries = []
        self._keys = set()
        for e in self.entries:
            self._keys.update(k for k in e.get("keys", []) if k)

    @staticmethod
    def keys_for(b: Business) -> list[str]:
        k = [f"id:{b.business_id}" if b.business_id else "", f"domain:{b.domain}" if b.domain else "",
             f"phone:{b.phone}" if b.phone else "", f"name:{b.name.lower()}|{b.postcode}"]
        k += [f"email:{e.address}" for e in b.emails]
        return [x for x in k if x]

    def blocked(self, b: Business) -> bool:
        return any(k in self._keys for k in self.keys_for(b))

    def add(self, keys: list[str], how: str = "", today: dt.date | None = None) -> None:
        keys = [k for k in keys if k and k not in self._keys]
        if not keys:
            return
        self.entries.append({"keys": keys, "date": (today or dt.date.today()).isoformat(), "how": how})
        self._keys.update(keys)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.entries, ensure_ascii=False, indent=1), encoding="utf-8")
