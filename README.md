# Business Lead Radar

Finds small businesses **across Finland** (salons, barbers, beauty and wellness, cafés, restaurants, clinics,
dentists, vets, car repair, trades, guest houses, estate agents, small shops, sole traders) that one of
**Barmo's** products fits, explains *why* it fits, and shows **the lawful way to reach each one**. Email is
offered wherever Finnish law allows it without consent (registered companies' generic addresses); for sole
traders the radar gives you a phone or visit plan and asks you to get consent first.

Sister project of `hr-contact-radar` and `remote-job-radar` (collect, match, score, dashboard). Like
hr-contact-radar, its output is about people (a toiminimi *is* a person), so online it exists only encrypted.

## What you get

| | |
|---|---|
| **Dashboard** | Online: `https://girimohan.github.io/business-lead-radar/` (encrypted, asks for your passphrase), rebuilt every morning by GitHub Actions. Locally: `private/dashboard.html`. Businesses ranked by fit; filters by kind of business, **region and municipality**, company form, which product fits and how you may reach them. For each one: why the product fits ("your website has no chat and no online booking"), a channel table (email / phone / visit / letter / form / SMS: allowed or not, and why), a draft for the best allowed channel in Finnish or English, **Open in my email app / Open in Gmail**, a consent recorder and a tracker. |
| **Email queue** | *Reach by: Email allowed* (or sort *Email allowed first*): every lead you may email today. The dashboard counts the emails you send and warns past `email_daily_limit` (25). |
| **Daily issue** | A GitHub issue (GitHub emails it to you) with counts only: new leads by kind and region. No names. |
| **Data** | `private/leads.json` locally. |

Nothing is ever sent for you. You review each draft and send it yourself, one at a time.

## How it works

```
PRH open data (registered companies, whole country) ─┐
                                                     ├─ merge ─ region ─ opt-out ─ find website ─ read website ─ channels ─ score ─ dashboard
OpenStreetMap (places, incl. toiminimi)             ─┘
```

1. **Collect.** PRH/YTJ open data API v3: companies by TOL 2025 industry code, for the whole country (business
   ID, company form, address, website; no phone or email; sole traders not included). OpenStreetMap via
   Overpass: the places themselves, with phone and website where mapped; reused for `osm_refresh_days` (6)
   to spare the public servers. Chains (anything with a `brand` tag) are skipped.
2. **Merge.** A place is matched to a company by business ID, website domain, or name + postcode, so it learns
   its business ID and company form. A place with no match is probably a sole trader.
3. **Region.** Each business gets its municipality and region (maakunta) from its postcode, map point or town
   (Statistics Finland, `data/geo.json`; refresh with `python -m bizradar geo`).
4. **Find the website.** If neither source has one, a few domains are tried from the name and accepted only if
   the homepage shows the business's name.
5. **Read the website** (robots.txt respected, ≤ 4 pages, cached 30 days, **registered companies first**,
   because those may be emailed): the email, phone and contact form the business publishes there, and what it
   already uses: booking tool, chat, delivery, platform, mobile-friendliness, https, copyright year. Emails are
   kept only if they are on the business's own domain or a free-mail address. Nationwide there are tens of
   thousands of sites: each run reads `max_sites_per_run` (1,500) new ones, so coverage fills in over the
   first two weeks of daily runs.
6. **Channels** (`bizradar/compliance.py`): see the rules below.
7. **Score** (`bizradar/score.py`): which products fit, from evidence only. The radar never claims "no
   website" unless the business is a mapped storefront and a search found nothing, and never comments on a
   site it could not read. Leads below `min_score` (30) are not shown.

## The rules (summary in `docs/legal-research.md`, full cited research in `docs/research-full.md`)

| | Oy / Ky / Ay / osuuskunta confirmed in PRH | Toiminimi or unknown |
|---|---|---|
| Email to a generic address | yes (917/2014 § 202, opt-out) | **no**: consent needed (§ 200) |
| Email to a named person's own address | consent, or a documented role check (owner/manager) | no |
| SMS, DMs | not used | no |
| Phone, letter, visit | yes, unless they refuse | yes, unless they refuse |

Every template says who you are (name, Barmo, Y-tunnus), why you are writing, where you got their details, and
how to say no; keep those lines. **"No" is final**: mark *Do not contact again*, then sync.

Email drafts to businesses whose website the radar read end with a P.S. offering Barmo's free website audit
(`audit` in `config.yaml`), the lowest-commitment next step barmo.fi offers.

## Run it online (GitHub Actions + Pages)

The workflow `.github/workflows/daily.yml` runs every morning: tests, collect the whole country, read a batch of
websites, score, encrypt, publish to GitHub Pages, and open an issue with the counts.

1. Set the passphrase (12+ characters; you type it to open the dashboard; keep it in your password manager):

   ```powershell
   gh secret set RADAR_PASSPHRASE --repo girimohan/business-lead-radar
   ```

2. Optional: sender details you'd rather not commit (the phone number, say), as YAML:

   ```powershell
   gh secret set RADAR_SENDER --repo girimohan/business-lead-radar --body "phone: '+358 ...'"
   ```

3. Start the first run (later runs are automatic): **Actions → Daily business lead radar → Run workflow**, or

   ```powershell
   gh workflow run daily.yml --repo girimohan/business-lead-radar
   ```

What is on GitHub: the code, `config.yaml`, the docs, `data/geo.json` (public statistics) and
`data/shared.enc`. Leads, website contact details, the opt-out list and contact statuses exist there only
encrypted (the published page, the Actions cache, `shared.enc`). The passphrase is a GitHub secret.

### Keep the radar in step with your tracker

Your statuses live in the browser. Every week or so: **Rules, sources, sync → Download my tracker**, then

```powershell
$env:RADAR_PASSPHRASE = Read-Host "Radar passphrase"
python -m bizradar sync "$HOME\Downloads\bizradar-tracker-2026-11-24.json"
git add data/shared.enc; git commit -m "Sync tracker"; git push
```

"Do not contact again" goes to `data/optout.json` (checked on every run, never shown again); contacted
businesses are kept past the retention limit; a contact log is written to `private/contact-log.csv`. With the
passphrase set, the same command writes the encrypted `data/shared.enc`, which the online run reads.

A "no" by email or phone outside the dashboard:

```powershell
python -m bizradar optout info@salon.fi --how "replied no thanks 2026-12-01"
```

## Run it on your computer

```powershell
pip install -r requirements-dev.txt
python -m pytest -q
python -m bizradar run --area Vantaa --segments hair,beauty --open    # quick: one town, two kinds
python -m bizradar run --area Uusimaa,Pirkanmaa --open                # regions
python -m bizradar run --open                                         # the whole country (slow the first time)
```

1. In `config.yaml`, check `sender` and publish your privacy notice (`docs/tietosuojaseloste.md` is a ready
   template) and put its link in `sender.privacy_url`. Sign `docs/lia.md`.
2. Tune `area`, `segments` (industry codes, map tags, which products to offer) and `offers`. Message texts are
   in `outreach.yaml`.

## Data kept, and where

| File | Contents | Committed? |
|---|---|---|
| `private/` | leads, website cache (published contact details), OSM cache, contact log, dashboard | never (git-ignored) |
| `data/optout.json`, `data/contacts.json` | businesses that said no; whom you contacted | never in clear; encrypted in `data/shared.enc` |
| `data/seen.json`, `data/domains.json` | lead ids and dates; websites found from names | no (encrypted in the Actions cache) |
| `data/geo.json` | municipalities, regions, postcodes (Statistics Finland) | yes, public statistics |

Uncontacted leads expire after `retention_days` (180), unless a conversation started. Website data for
businesses no longer shown is deleted on every run.

## Sources and credit

Company data: PRH open data, CC BY 4.0 (cite the source; no PRH/YTJ logos). Regions and postcodes:
Statistics Finland, CC BY 4.0. Map data © OpenStreetMap contributors, ODbL. Not used on purpose: Google
Maps/Places (storage terms), Fonecta/Finder, Yritystele, Wolt, Timma, Fresha and Instagram (their terms forbid
scraping); look a business up there by hand if you need to.

## Limits

- Sole traders are found only if they are on OpenStreetMap; coverage is good for storefronts (salons, cafés),
  poor for mobile or home-based businesses. They can't be emailed cold anyway: call or visit.
- A place without a name match in PRH is shown as "Probably toiminimi"; it may be a company whose sign differs
  from its registered name. Check the Y-tunnus on ytj.fi before emailing anyone the radar could not confirm.
- This is guidance, not legal advice.
