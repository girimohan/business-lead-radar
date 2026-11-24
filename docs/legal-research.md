# Reaching Finnish small businesses lawfully: what the radar is built on

Written 24.11.2026 for a sole trader (toiminimi) selling software to other small businesses. The full
research report, with a citation for every claim, is in `research-full.md`; this page is the short version the
radar's rules follow.
**This is research to build a tool on, not legal advice.** Have the two open points at the end checked
(Suomen Yrittäjät's members' legal advice is free and covers exactly this) before a large campaign.

## Summary: the rules the radar enforces

1. **Email, SMS, automated calls and similar to a natural person need prior consent.** A sole trader
   (toiminimi, *yksityinen elinkeinonharjoittaja*) has no legal personality separate from the owner, so the
   owner is the recipient: **no cold email or SMS to a toiminimi.** (917/2014 § 200(1)) The Data Protection
   Ombudsman applied § 200 to a sole trader in decision 3578/157/2019 (23.7.2020): being an elinkeinonharjoittaja
   does not by itself make B2B rules apply.
2. **To a company's generic address (Oy, Ky, Ay, osuuskunta: *yhteisö*), direct marketing is allowed unless
   it has explicitly refused**, and every message must offer an easy, free way to refuse. (917/2014 § 202)
   **A named employee's own address is a natural person's address:** consent is needed unless their duties are
   essentially related to the offer (*asemavaltuus*), which you must check and document first (TSV FAQ). A
   salon's owner or manager usually qualifies; junior staff usually do not.
3. **Phone calls by a person, letters and visits are allowed to natural persons too, unless they have refused.**
   (917/2014 § 200(2)) So a toiminimi can be called or visited, and asked for permission to email. In the
   first call, say where you got the number and where your privacy notice is. A refusal said out loud counts.
4. **Marketing must be recognisable as marketing** when received, and must not hide the sender.
   (917/2014 § 203)
5. **GDPR applies to all of it**: a toiminimi's details, and named employees at companies, are personal data.
   The lawful basis for prospecting is legitimate interest (Art. 6(1)(f); Recital 47 says direct marketing
   *may* be one), which needs a written balancing test (see `lia.md`).
6. **The first contact must carry the Art. 14 notice**: who you are, why you process the data, where it came
   from, the right to object. Every template in `outreach.yaml` does this in a few lines and links to the full
   privacy notice (`tietosuojaseloste.md`).
7. **An objection is final** (Art. 21(2)-(3)): stop and suppress. The radar's opt-out list is checked
   before anything is shown, by business ID, domain, email, phone and name+postcode.
8. **Keep less, for less time**: the radar stores only what businesses published about themselves, keeps it
   on your computer, forgets uncontacted leads after `retention_days` (180) and drops cached website data for
   businesses no longer shown.

## Channel by channel

| Channel | Oy / Ky / Ay / osuuskunta (confirmed in PRH) | Toiminimi, or company form unknown |
|---|---|---|
| Email to a generic address (info@, ajanvaraus@) | **Yes**, opt-out rule (§ 202) | **No**, consent needed (§ 200(1)) |
| Email to a named employee's own address | **Only with consent, or a documented check** that their role (owner, manager) is essentially related to the offer | **No** |
| SMS / WhatsApp / Instagram or Facebook DM | Avoided: legally like email for a company, but these usually reach a person's own phone/account | **No** (electronic message, consent needed) |
| Contact form on their website | Treated like email: **yes** for companies | **No** |
| Phone call by you | **Yes**, unless they refuse | **Yes**, unless they refuse (§ 200(2)). The best way to ask for email consent. |
| Addressed letter | **Yes** | **Yes**, unless they refuse |
| Visit to the premises | **Yes** (outside busy hours, short) | **Yes** |

Consent recorded in the dashboard (date, how, address) unlocks the email draft for a toiminimi. For a named
person at a company, a documented role check (e.g. "owner, named on the About page") unlocks it too.

Opt-out registers: ASML's Robinson services and the DVV direct-marketing ban protect consumers and do not bind
B2B use. The only binding B2B ban is each business's own refusal, which is why the radar's opt-out list matters
(`research-full.md` § 4).

## Statute text (Finlex, 917/2014, read 24.11.2026)

Source: https://www.finlex.fi/fi/lainsaadanto/2014/917 (chapter 24). Laws are not protected by copyright in
Finland (tekijänoikeuslaki § 9).

- **§ 200(1)**: "Automatisoitujen soittojärjestelmien sekä telekopiolaitteiden, sähköpostiviestien,
  tekstiviestien, puheviestien, ääniviestien tai kuvaviestien avulla toteutettua suoramarkkinointia saa
  kohdistaa vain sellaisiin luonnollisiin henkilöihin, jotka ovat antaneet siihen ennalta suostumuksensa."
- **§ 200(2)**: "Muuta kuin 1 momentissa tarkoitettua suoramarkkinointia luonnolliselle henkilölle saa
  harjoittaa, jollei tämä ole sitä nimenomaisesti kieltänyt. Luonnollisen henkilön on voitava helposti ja
  maksutta kieltää tässä momentissa tarkoitettu suoramarkkinointi."
- **§ 200(3)**: the existing-customer exception: an address received from your own customer during a sale may
  be used for your own similar products, with an opt-out each time. (Not relevant to cold prospecting.)
- **§ 202**: "Suoramarkkinointia yhteisölle saa harjoittaa, jollei tämä ole sitä nimenomaisesti kieltänyt.
  Yhteisölle on annettava mahdollisuus helposti ja ilman erillistä maksua kieltää yhteystietojensa käyttö
  jokaisen suoramarkkinointitarkoituksessa lähetetyn sähköpostiviestin, tekstiviestin [...] yhteydessä.
  Suoramarkkinointia harjoittavan on selkeästi tiedotettava kieltomahdollisuudesta."
- **§ 203**: a direct-marketing email or text under §§ 200 and 202 "on voitava sitä vastaanotettaessa
  selvästi ja yksiselitteisesti tunnistaa markkinoinniksi"; the section also bars hiding the sender.

## Data sources

| Source | Used for | Contact data | Terms | Status |
|---|---|---|---|---|
| **PRH / YTJ open data API v3** (`avoindata.prh.fi/opendata-ytj-api/v3`) | Registered companies by TOL 2025 industry code and municipality: business ID, names, company form, address, website | **None**: "Email addresses and phone numbers are not available" (ytj.fi) | Free; cite the source; do not use PRH/YTJ logos or imitate their services. **Sole traders ("private traders") are excluded** | Collected |
| **OpenStreetMap** (Overpass API) | The places themselves (cafés, salons...), including sole traders | phone and website tags on many places | ODbL 1.0: show "© OpenStreetMap contributors" | Collected |
| **The business's own website** | Published email, phone, contact form, booking tool, chat, platform | what the business itself published | robots.txt respected, ≤ 4 pages, once per 30 days | Read |
| Google Maps / Places | not used | | Terms restrict storing results | Not used |
| Fonecta / Finder, Yritystele, Wolt, Timma, Fresha, Instagram | not used for collection | | Their terms forbid scraping | Look up by hand if needed |
| Paid B2B registers (Asiakastieto, Vainu, Fonecta Profinder) | an option later | named decision-makers, checked against ban registers | Paid licence | Not used |

Checked 24.11.2026: https://ytj.fi/en/index/opendata.html ("except private traders"; no emails or phone
numbers), https://avoindata.prh.fi/faq.html (cite the source; no PRH/YTJ logos). The API itself was tested
live: no sole-trader company form appears in its company-form code list (YRMU), and Vantaa queries return
Oy, Ky, Ay and osuuskunta records only.

## Settled by the full research (24.11.2026, details in `research-full.md`)

- **Telemarketing:** the written-confirmation rule for phone sales (KSL 6:12, since 1.1.2023) protects consumers
  only. A sole trader buying for the business is not a consumer (KSL 1:4). The Ministry of Justice's 30.12.2025
  evaluation proposes no B2B extension. Robocalls still need consent (TSV decision 19.3.2026).
- **Named employee addresses:** consent, or a documented *asemavaltuus*, as above (TSV FAQ, decision 3578/157/2019).
- **Platform terms:** Google Places content may not be stored (only place_id, and coordinates for 30 days);
  Fonecta/Finder (terms updated 5.1.2026), Fresha, Wolt, Instagram, LinkedIn and ytj.fi/Virre bar scraping.
  Varaa.com was a domain for sale on 24.11.2026.

## Still not verified

- Whether Instagram/Facebook DMs and website contact forms legally count as email messages under § 200: no
  Finnish ruling. The radar treats them like email (no cold contact to a toiminimi).
- How strict "essentially related" is for general-purpose business software sold to a sole trader: untested.
  The radar stays on the safe side (consent first).
- Timma and Foodora terms could not be read; neither is used as a source.
- See `research-full.md` § 9 for the full list.
