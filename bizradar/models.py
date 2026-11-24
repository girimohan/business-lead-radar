from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Email:
    address: str
    kind: str = "generic"      # generic (info@, ajanvaraus@ ...) | personal (looks like a person's own address)
    source_url: str = ""       # the page where the business itself published it


@dataclass
class Business:
    id: str                    # "prh:1234567-8" or "osm:node/123"
    name: str
    segment: str = ""          # key into config.segments
    business_id: str = ""      # Y-tunnus, when known
    legal_form: str = "unknown"   # oy | ky | ay | osk | tmi | other | unknown
    legal_form_source: str = ""   # prh | name | ""
    industry_code: str = ""
    industry: str = ""
    other_names: list[str] = field(default_factory=list)
    street: str = ""
    postcode: str = ""
    city: str = ""             # postal town, as written in the address
    municipality: str = ""     # kunta (Statistics Finland), for filtering
    region: str = ""           # maakunta
    lat: float | None = None
    lon: float | None = None
    website: str = ""
    domain: str = ""
    phone: str = ""
    phone_source: str = ""
    emails: list[Email] = field(default_factory=list)
    contact_form: str = ""     # URL of a contact form on the business's own site
    instagram: str = ""
    facebook: str = ""
    opening_hours: str = ""
    registered: str = ""       # registration date in the trade register
    signals: dict = field(default_factory=dict)    # what the website shows: booking tool, chat, shop, languages ...
    provenance: list[dict] = field(default_factory=list)   # [{field, source, ref}] where each fact came from
    osm_ref: str = ""
    # Filled in later by compliance / scoring.
    channels: dict = field(default_factory=dict)
    score: int = 0
    reasons: list[str] = field(default_factory=list)
    offers: list[str] = field(default_factory=list)
    offer_why: dict = field(default_factory=dict)   # offer -> {"en": ..., "fi": ...}, written to the business
    first_seen: str = ""

    def note(self, fld: str, source: str, ref: str = "") -> None:
        if not any(p["field"] == fld and p["source"] == source for p in self.provenance):
            self.provenance.append({"field": fld, "source": source, "ref": ref})

    def to_public(self) -> dict:
        return asdict(self)
