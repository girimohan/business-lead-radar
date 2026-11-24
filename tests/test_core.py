import datetime as dt

import yaml

from bizradar import compliance, enrich, merge, score
from bizradar.models import Business, Email
from bizradar.sources import prh
from bizradar.text import legal_form_from_name, name_similarity, normalize_phone

CFG = yaml.safe_load(open("config.yaml", encoding="utf-8"))


def biz(**kw):
    d = dict(id="x", name="Salon Aurora", segment="hair")
    d.update(kw)
    return Business(**d)


# --- who may be emailed -------------------------------------------------------------------------------------

def test_sole_trader_never_gets_cold_email():
    b = biz(legal_form="unknown", emails=[Email("info@aurora.fi", "generic", "https://aurora.fi/yhteys")])
    ch = compliance.channels(b)
    assert not ch["email"]["allowed"]
    assert "consent" in ch["email"]["why"]
    assert not ch["sms"]["allowed"]
    assert not ch["form"]["allowed"] if "form" in ch else True


def test_toiminimi_from_name_still_no_email():
    b = biz(name="Tmi Aurora", legal_form="tmi", legal_form_source="name", emails=[Email("info@aurora.fi")])
    assert not compliance.channels(b)["email"]["allowed"]


def test_registered_oy_generic_address_allowed():
    b = biz(legal_form="oy", legal_form_source="prh", business_id="1234567-8",
            emails=[Email("anna@aurora.fi", "personal"), Email("info@aurora.fi", "generic")])
    ch = compliance.channels(b)
    assert ch["email"]["allowed"] and ch["email"]["to"] == "info@aurora.fi"


def test_oy_by_name_only_is_not_enough():
    b = biz(name="Aurora Oy", legal_form="oy", legal_form_source="name", emails=[Email("info@aurora.fi")])
    ch = compliance.channels(b)
    assert not ch["email"]["allowed"] and "PRH" in ch["email"]["why"]


def test_personal_address_at_oy_needs_consent_or_documented_role():
    b = biz(legal_form="oy", legal_form_source="prh", emails=[Email("anna@aurora.fi", "personal")])
    ch = compliance.channels(b)
    assert not ch["email"]["allowed"] and ch["email"].get("role_unlock") and ch["email"]["to"] == "anna@aurora.fi"


def test_phone_letter_visit_for_anyone_with_details():
    b = biz(legal_form="unknown", phone="+358401234567", street="Kauppakatu 1", postcode="01300", city="Vantaa")
    ch = compliance.channels(b)
    assert ch["phone"]["allowed"] and ch["letter"]["allowed"] and ch["visit"]["allowed"]
    assert compliance.best_channel(ch) == "phone"


# --- opt-out ------------------------------------------------------------------------------------------------

def test_optout_blocks_by_any_identifier(tmp_path):
    oo = compliance.OptOut(tmp_path / "optout.json")
    oo.add(["email:info@aurora.fi"], how="replied no")
    oo.save()
    oo2 = compliance.OptOut(tmp_path / "optout.json")
    assert oo2.blocked(biz(emails=[Email("info@aurora.fi")]))
    assert not oo2.blocked(biz(name="Other", emails=[Email("info@other.fi")]))


# --- parsing and matching -----------------------------------------------------------------------------------

def test_legal_form_from_name():
    assert legal_form_from_name("Hiushuone Nevalampi Oy") == "oy"
    assert legal_form_from_name("Kampaamo Ky") == "ky"
    assert legal_form_from_name("Tmi Liisa Virtanen") == "tmi"
    assert legal_form_from_name("Salon Aurora") == "unknown"


def test_phone_normalised():
    assert normalize_phone("09 876 4291") == "+35898764291"
    assert normalize_phone("040-123 4567; 050 1") == "+358401234567"
    assert normalize_phone("abc") == ""
    assert normalize_phone("200449812772") == ""      # junk from a tel: link
    assert normalize_phone("+358 40 123 4567") == "+358401234567"


def test_prh_skips_liquidation_and_maps_form():
    rec = {"businessId": {"value": "1234567-8"}, "names": [{"name": "Aurora Oy", "type": "1"}],
           "companyForms": [{"type": "16"}], "mainBusinessLine": {"type": "96210", "descriptions": []},
           "addresses": [], "companySituations": [], "tradeRegisterStatus": "1"}
    b = prh.parse(rec, "hair")
    assert b.legal_form == "oy" and b.legal_form_source == "prh"
    rec["companySituations"] = [{"type": "SELTILA"}]
    assert prh.parse(rec, "hair") is None


def test_merge_by_name_and_postcode():
    co = biz(id="prh:1", name="Hiushuone Aurora Oy", postcode="01300", city="Vantaa", legal_form="oy",
             legal_form_source="prh", business_id="1234567-8")
    place = biz(id="osm:node/1", name="Hiushuone Aurora", postcode="01300", city="Vantaa", osm_ref="node/1",
                phone="+35891234567")
    out, st = merge.merge([co], [place])
    assert st["matched"] == 1 and len(out) == 1
    assert out[0].phone == "+35891234567" and out[0].business_id == "1234567-8"
    assert name_similarity("Kahvila Kultainen", "Kultainen Kahvila Oy") == 1.0


def test_email_kinds():
    b = biz(name="Salon Aurora", domain="aurora.fi")
    assert enrich.classify_email("info@aurora.fi", b) == "generic"
    assert enrich.classify_email("salonaurora@gmail.com", b) == "generic"
    assert enrich.classify_email("liisa.virtanen@aurora.fi", b) == "personal"


def test_site_reading_keeps_only_own_and_freemail_addresses():
    html = ('<a href="mailto:info@aurora.fi">x</a> designer@webagency.com '
            'ajanvaraus(at)aurora.fi <a href="tel:09 123 4567">soita</a>'
            '<form><textarea></textarea></form> <script src="https://timma.fi/w.js"></script>')
    assert set(enrich._emails(html)) >= {"info@aurora.fi", "ajanvaraus@aurora.fi"}


# --- claims in drafts must be backed by evidence ------------------------------------------------------------

def test_no_website_claim_needs_a_mapped_storefront_and_a_search():
    prh_only = biz(segment="hair", legal_form="oy", legal_form_source="prh")
    score.score(prh_only, CFG, dt.date(2026, 11, 24))
    assert "website" not in prh_only.offers          # PRH simply lacks the field: no claim
    shop = biz(segment="hair", osm_ref="node/1", signals={"site_searched": True})
    score.score(shop, CFG, dt.date(2026, 11, 24))
    assert "website" in shop.offers


def test_unread_site_makes_no_quality_claims():
    b = biz(website="https://aurora.fi", domain="aurora.fi", signals={"site_ok": False})
    score.score(b, CFG, dt.date(2026, 11, 24))
    assert "website" not in b.offers and "receptionist" not in b.offers


def test_receptionist_fits_site_without_chat():
    b = biz(website="https://aurora.fi", domain="aurora.fi",
            signals={"site_ok": True, "mobile": True, "https": True, "booking": ["Timma"]})
    score.score(b, CFG, dt.date(2026, 11, 24))
    assert b.offers[0] == "receptionist" and "chat" in b.offer_why["receptionist"]["en"]


# --- the whole country: geography, area, compact page, encryption -------------------------------------------

from pathlib import Path

from bizradar import dashboard, geo, pipeline, secure

GEO = geo.Geo(Path("data/geo.json"))


def test_geo_finds_municipality_and_region():
    assert GEO.names(GEO.locate("01300")) == ("Vantaa", "Uusimaa")
    assert GEO.names(GEO.locate(lat=65.012, lon=25.47)) == ("Oulu", "Pohjois-Pohjanmaa")
    assert GEO.names(GEO.locate(city="Tammerfors"))[0] == "Tampere"
    assert GEO.locate("99999x") == ""


def test_area_spec():
    assert pipeline.area_spec({"area": "all"}, GEO) == (None, set(), set())
    q, m, r = pipeline.area_spec({"area": ["Vantaa", "Kerava"]}, GEO)
    assert q == ["Kerava", "Vantaa"] and m == {"vantaa", "kerava"} and not r
    q, m, r = pipeline.area_spec({"area": ["Pirkanmaa", "Vantaa"]}, GEO)
    assert q is None and r == {"pirkanmaa"} and m == {"vantaa"}   # a region means a nationwide query, then filter


def test_compact_keeps_what_the_page_needs():
    b = biz(legal_form="oy", legal_form_source="prh", business_id="1234567-8", emails=[Email("info@aurora.fi")])
    b.channels = compliance.channels(b)
    b.note("business_id", "prh", "1234567-8")
    c = dashboard.compact({"leads": [b.to_public()]})
    lead = c["leads"][0]
    assert "street" not in lead and lead["channels"]["email"][0] == 1
    assert c["whys"][lead["channels"]["email"][2]].startswith("registered OY")
    assert lead["provenance"] == [["business_id", "prh"]]


def test_state_round_trip_only_restores_known_files(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "optout.json").write_text('[{"keys": ["id:1"]}]', encoding="utf-8")
    blob = secure.pack_state(tmp_path, "p" * 12, secure.SHARED_FILES)
    (tmp_path / "data" / "optout.json").unlink()
    assert secure.unpack_state(blob, tmp_path, "p" * 12, secure.SHARED_FILES) == ["data/optout.json"]
    assert secure.unpack_state(blob, tmp_path, "p" * 12, ["private/sites.json"]) == []
    try:
        secure.unpack_state(blob, tmp_path, "q" * 12, secure.SHARED_FILES)
        assert False
    except secure.BadPassphrase:
        pass
