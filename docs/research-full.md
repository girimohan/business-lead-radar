# Finland B2B lead radar: legal ground, data sources and a compliant design

Research date: 24.11.2026. Written for a Finnish sole trader (toiminimi) selling a micro-SaaS to small local businesses.

> **This is general research, not legal advice.** It summarises public sources as read on 24.11.2026. Laws, regulator guidance and platform terms change. Before a large campaign, have the grey areas (section 9) checked. Suomen Yrittäjät members get free legal advice, which covers this topic.

Companion files in this repo: `docs/legal-research.md` (short rule set), `docs/lia.md` (balancing test), `docs/tietosuojaseloste.md` (privacy notice). This document is the long, source-backed version. Where it adds nuance to those files, it says so.

---

## Executive summary: the rules that matter most

1. **Email or SMS to a toiminimi is opt-in by default.** A sole trader is a natural person. Section 200(1) of Act 917/2014 requires prior consent for email, SMS and automated-call marketing to natural persons ([Finlex 917/2014](https://www.finlex.fi/fi/lainsaadanto/2014/917)). The Data Protection Ombudsman (TSV) applied §200 to a sole trader in 2020. It held that being an elinkeinonharjoittaja does not by itself give the role-based exemption (*asemavaltuus*) ([TSV decision 3578/157/2019, 23.7.2020](https://tietosuoja.fi/documents/6927448/22406974/Apulaistietosuojavaltuutetun_p%C3%A4%C3%A4t%C3%B6s_3578.157.19.pdf/42226fe6-6ad7-5b51-d8dc-a5287c1d7ad6/Apulaistietosuojavaltuutetun_p%C3%A4%C3%A4t%C3%B6s_3578.157.19.pdf?t=1596613001067)). The same decision says the decisive test is whether the product is essentially related to the person's work. That leaves a narrow, untested grey area for software that runs the sole trader's own business. **The radar should treat it as consent-required.**
2. **Email to a company's generic address (info@ of an Oy, Ky, Ay or osuuskunta) is opt-out.** This is allowed unless the company has refused, and every message must offer an easy, free way to refuse (§202). TSV says no consent is needed for a *yleinen sähköpostiosoite* ([TSV FAQ on direct marketing](https://tietosuoja.fi/usein-kysyttya-suoramarkkinointi)).
3. **A named employee's own work address (etunimi.sukunimi@yritys.fi) counts as a natural person's address.** Consent is needed unless the person's role is essentially related to what you sell (*asemavaltuus*). You must check and document that role before sending ([TSV FAQ](https://tietosuoja.fi/usein-kysyttya-suoramarkkinointi); [3578/157/2019](https://tietosuoja.fi/documents/6927448/22406974/Apulaistietosuojavaltuutetun_p%C3%A4%C3%A4t%C3%B6s_3578.157.19.pdf/42226fe6-6ad7-5b51-d8dc-a5287c1d7ad6/Apulaistietosuojavaltuutetun_p%C3%A4%C3%A4t%C3%B6s_3578.157.19.pdf?t=1596613001067)). For a salon or café Oy, the owner or manager usually qualifies and a junior employee usually does not.
4. **Phone calls by a human, letters and walk-in visits need no consent, even to a toiminimi**, but must stop on refusal (§200(2); [TSV FAQ](https://tietosuoja.fi/usein-kysyttya-suoramarkkinointi)). Robocalls need consent. **The 2023 written-confirmation rule for phone sales protects consumers only.** A sole trader buying software for the business is not a *kuluttaja* ([Kuluttajansuojalaki 1:4 and 6:12](https://www.finlex.fi/fi/laki/ajantasa/1978/19780038)).
5. **GDPR applies to every toiminimi lead and every named person.** TSV lists a sole trader's name and Y-tunnus as personal data. An Oy's Y-tunnus and info@ address are not ([TSV: Mikä on henkilötieto?](https://tietosuoja.fi/mika-on-henkilotieto)). Lawful basis: legitimate interest with a **written** balancing test ([TSV: oikeutettu etu](https://tietosuoja.fi/rekisterinpitajan-oikeutettu-etu)). The EDPB adopted its final legitimate-interest guidelines in November 2026 ([TSV news 13.11.2026](https://tietosuoja.fi/-/euroopan-tietosuojaneuvostolta-arviointi-tiedonsiirroista-etela-koreaan-seka-lopulliset-versiot-bcr-suosituksista-ja-oikeutettua-etua-koskevasta-ohjeesta)).
6. **The first message must carry the Art. 14 notice**: who you are, the purpose, **where the data came from**, and the right to object. The right to object must be stated separately from other information ([TSV: rekisteröidyn informointi](https://tietosuoja.fi/rekisteroidyn-informointi); [GDPR Art. 14(3), 21(4)](https://eur-lex.europa.eu/eli/reg/2016/679/oj)). An objection is permanent for marketing (Art. 21(3)), including one made orally during a call ([TSV FAQ](https://tietosuoja.fi/usein-kysyttya-suoramarkkinointi)).
7. **PRH open data finds companies, not sole traders.** It excludes *private traders*, emails and phones, but it does return a website field (confirmed with live API calls, section 6.1). Google Places content may not be stored, apart from place_id and short-lived coordinates ([Google Maps Platform EEA terms](https://cloud.google.com/terms/maps-platform/eea)). Scraping Fonecta/Finder, Wolt, Fresha, Instagram or LinkedIn is barred by their terms (section 5).
8. **Robinson lists and the DVV ban protect consumers; no B2B ban register exists.** ASML's phone and post Robinson services and the DVV population-register ban do not bind B2B use of business-register data ([ASML kieltopalvelut](https://asml.fi/kieltopalvelut/); [KKV](https://www.kkv.fi/en/consumer-affairs/marketing-sales-and-indicating-prices/direct-marketing/prohibiting-direct-marketing-and-telemarketing/)). The only binding B2B "ban list" is each business's own refusal, so your suppression list is the critical feature.

---

## 1. Channel table: Do / Don't / Grey

"Yhteisö" means Oy, Oyj, Ky, Ay, osuuskunta, association or foundation. Finnish partnerships (Ky, Ay) are legal persons, but their named partners are natural persons.

| Channel | Do | Don't | Grey area |
|---|---|---|---|
| **Email to an Oy/Ky/Ay generic address** (info@, ajanvaraus@, myynti@) | Send relevant B2B offers. Put an opt-out in every message, plus clear sender ID, Y-tunnus and a privacy link (§202, §203; [ASML B2B practice](https://asml.fi/wp-content/uploads/2023/12/ASML_B2B_Email_marketing_practice.pdf)). Honour refusals at once. | Mass-blast unrelated offers. Hide the sender. Omit the opt-out. Keep mailing after a refusal. | An address like *maija@salonki.fi* at a one-person Oy is really a person's address. Treat it as named (next row). |
| **Email to a named Oy employee** (etunimi.sukunimi@) | Only if the role is *essentially* related to the product (owner, manager, CEO of a salon buying salon software). Record why you judged so ([TSV FAQ](https://tietosuoja.fi/usein-kysyttya-suoramarkkinointi)). Opt-out in every message. | Send to staff whose job has nothing to do with the product. Rely only on "they work there" ([3578/157/2019](https://tietosuoja.fi/documents/6927448/22406974/Apulaistietosuojavaltuutetun_p%C3%A4%C3%A4t%C3%B6s_3578.157.19.pdf/42226fe6-6ad7-5b51-d8dc-a5287c1d7ad6/Apulaistietosuojavaltuutetun_p%C3%A4%C3%A4t%C3%B6s_3578.157.19.pdf?t=1596613001067)). | How strict "essentially related" is for a general-purpose SaaS is untested. |
| **Email to a toiminimi** (any address, including info@) | Get consent first, for example by phone, in person, from an inbound form, or at an event. After a sale, the existing-customer exception allows similar offers with an opt-out (§200(3)). | Send cold marketing email. | The 2020 decision leaves room for a role-relevance argument when the product runs the trader's own business. It has not been tested. Don't build on it without advice. |
| **Phone (human caller)** to an Oy or toiminimi | Allowed unless refused (§200(2)). In the first call, say who you are, where you got the number, and where the privacy notice is ([TSV FAQ](https://tietosuoja.fi/usein-kysyttya-suoramarkkinointi)). Record refusals made during the call. | Use robocalls or prerecorded messages without consent (§200(1); [TSV 19.3.2026](https://www.edilex.fi/tsv/20260008)). Ignore a refusal or demand it in writing. | If the number is the owner's personal mobile, it is still a business call to a natural person. Allowed, but expect a higher refusal rate. ASML's Puhelin-Robinson covers consumer subscriptions (section 4). |
| **SMS** | To a yhteisö: as for email (§202). From 4.5.2026, operators verify organisational sender IDs. From 2.11.2026, unverified ones show as "Roskaposti" ([Traficom](https://www.traficom.fi/en/news/measures-combat-scam-messages-further-strengthened-consumer-vigilance-still-required)). | Send cold SMS to a toiminimi or a personal mobile (§200(1)). | Most small-business numbers are the owner's mobile, so treat SMS as consent-only in practice. |
| **Postal letter** | Allowed to companies and toiminimi unless refused (§200(2)). Address it to the business. Include sender ID and how to refuse. | Ignore a written refusal. | Posti-Robinson is a consumer service and filtering needs an ASML licence. Screening is optional for B2B (section 4). |
| **Social media DM** (Instagram, Facebook, LinkedIn) | One-to-one, manual, relevant message to a **business** account, treated with the same rules as email for that recipient type. Respect the platform's messaging rules. | Automate DMs. Scrape profiles. Send bulk connection-plus-pitch sequences. These are barred by [LinkedIn's User Agreement](https://www.linkedin.com/legal/user-agreement) and [Instagram's Terms](https://help.instagram.com/581066165581870). | Whether a DM is a "sähköpostiviesti" under §200 is not settled in Finland (section 3). Assume it is. |
| **Walk-in visit** | Allowed: no consent rule for in-person B2B visits. Come at quiet hours, bring a one-page leaflet with Y-tunnus and contact details, and ask permission to follow up by email. | Visit at peak service hours. Return after a "no". | Home-sales consumer rules don't apply to business purchases ([KSL 1:4](https://www.finlex.fi/fi/laki/ajantasa/1978/19780038)). Notes you write about the owner are personal data. |
| **Website contact form** | Treat it exactly like email to that business's type (Oy generic is OK with opt-out; toiminimi needs consent). One relevant message only, with full sender ID. | Submit automatically or repeatedly. Ignore a "no sales offers" notice on the form. | No Finnish guidance found on whether a form submission is an electronic message under §200. It is delivered electronically, so assume it is. |

---

## 2. Email marketing law in detail (open question a)

### 2.1 The statute
Already verified in this project: §200(1) opt-in for natural persons, §200(2) opt-out for other channels, §202 opt-out for yhteisö with an opt-out in every message, §203 recognisability ([Finlex 917/2014](https://www.finlex.fi/fi/lainsaadanto/2014/917)). The following points were also read from the consolidated text on Finlex (24.11.2026):
- **§200(3)** is the existing-customer exception (contact details obtained in connection with a sale, used for similar products, with an opt-out at collection and in every message).
- **§201** bans marketing mobile subscriptions to consumers by phone. Not relevant here.
- **§203(2)** prohibits marketing messages that conceal the sender or lack a valid address for opt-out requests.
- **§204** lets operators block direct marketing at the user's request.
- **§305** makes the Data Protection Ombudsman the supervisor of §§200–204. Traficom does not supervise marketing email ([Finlex 917/2014 §305](https://www.finlex.fi/fi/laki/ajantasa/2014/20140917)).
- **§176** sets the general information duty for information-society service providers (identity and contact details), which applies to your website ([Finlex 917/2014](https://www.finlex.fi/fi/laki/ajantasa/2014/20140917)).

### 2.2 TSV guidance (primary source)
From the TSV direct-marketing FAQ ([tietosuoja.fi/usein-kysyttya-suoramarkkinointi](https://tietosuoja.fi/usein-kysyttya-suoramarkkinointi), read 24.11.2026):
- An address in the form *firstname.lastname@company* is in principle a **natural person's address**, so prior consent is the main rule.
- Consent is **not** required if the person works in duties that the marketed goods or services **essentially relate to** (*asemavaltuus*). The controller must verify this before sending and be able to show it afterwards, for example by documenting the assessment.
- **No consent is needed for a yhteisö's generic address** ("esimerkiksi yrityksen yleiseen sähköpostiosoitteeseen"), but the opt-out must be offered.
- For prospects who are private persons, electronic marketing needs consent. "Traditional" phone and letter marketing does not.
- A refusal given during a call must be processed. You cannot require the person to use another channel.
- If contact data came from elsewhere, the first marketing call must state where it came from, who the controller is, and where to find the privacy information.

### 2.3 Decisions
| Decision | What it says for the radar |
|---|---|
| **TSV 3578/157/2019, 23.7.2020** ([PDF](https://tietosuoja.fi/documents/6927448/22406974/Apulaistietosuojavaltuutetun_p%C3%A4%C3%A4t%C3%B6s_3578.157.19.pdf/42226fe6-6ad7-5b51-d8dc-a5287c1d7ad6/Apulaistietosuojavaltuutetun_p%C3%A4%C3%A4t%C3%B6s_3578.157.19.pdf?t=1596613001067)) | The recipient was a **sole trader** (magazine publishing) who got SMS ads for courses. The sender claimed B2B (§202). TSV held that the mere fact of being an elinkeinonharjoittaja does **not** give a natural person *asemavaltuus*. What matters is whether the person's duties essentially relate to the marketed products. The courses were unrelated, so §200(1) applied and consent was missing. Outcome: reprimand, orders, and referral to the sanctions board for a fine. 11 similar complaints were pending against the same controller. |
| **TSV 2020/702, 27.4.2020**, "Sähköinen suoramarkkinointi yhteisölle ja rekisteröidyn oikeus saada tieto siitä, mistä hakijan henkilötiedot on saatu" ([Finlex](https://finlex.fi/fi/viranomaiset/tietosuojavaltuutettu/2020/702)) | By its title, it concerns marketing to a yhteisö and the right to be told the data source. The full text could not be extracted (section 9). |
| **TSV 2025/2476, 9.6.2025**, "Informointi henkilötietojen käsittelystä puhelinmarkkinoinnissa" ([Finlex](https://www.finlex.fi/fi/viranomaiset/tietosuojavaltuutettu/2025/2476)) | Information duty in phone marketing. Its content is reflected in the FAQ text above. |
| **TSV/206/2021, 19.3.2026** ([Edilex](https://www.edilex.fi/tsv/20260008)) | Automated marketing calls need prior consent (§200(1)). Relying on CJEU C-654/23, TSV held that a GDPR legitimate-interest claim cannot replace the ePrivacy consent rule. Outcome: reprimand and order. Not final at the time of publication. |

**Fines:** TSV referred the 2020 sole-trader case to the sanctions board. A secondary guide reports a €7,000 fine in 2020 for unsolicited SMS ([Brovenly](https://www.brovenly.fi/oppaat/kylmasahkoposti-gdpr)). This was **not verified** in a primary source.

**Traficom:** no Traficom guidance on B2B marketing email was found. It is not the supervisor (§305). Traficom's relevant 2026 work is SMS sender-ID verification (section 3.3).

### 2.4 Interaction with GDPR (CJEU 2024–2025)
- **C-621/22 KNLTB (4.10.2024):** a purely commercial interest can be a legitimate interest under Art. 6(1)(f), subject to necessity and balancing ([curia C-621/22](https://curia.europa.eu/juris/liste.jsf?num=C-621/22)).
- **C-654/23 Inteligo Media (13.11.2025):** where the ePrivacy direct-marketing rule (Art. 13, which §§200–202 transpose) governs the *sending*, a separate GDPR Art. 6 basis for that sending is not required ([curia C-654/23](https://curia.europa.eu/juris/liste.jsf?num=C-654/23); commentary: [Reed Smith](https://viewpoints.reedsmith.com/post/102luvt/ecj-rules-on-soft-opt-in-for-freemium-newsletters-no-separate-gdpr-legal-basis-r), [Taylor Wessing](https://www.taylorwessing.com/en/insights-and-events/insights/2025/11/european-court-of-justice-backs-the-advocate-general)). TSV applied this in March 2026 (above). **The radar's own database (collecting, storing and profiling leads) still needs a GDPR basis**, which here is legitimate interest with an LIA.
- **Digital Omnibus (GDPR/ePrivacy amendments):** the Council adopted its position in autumn 2026, and the process is still ongoing ([Addleshaw Goddard](https://www.addleshawgoddard.com/en/insights/insights-briefings/2026/data-protection/eu-digital-omnibus-european-council-adopts-its-position/); [IAPP](https://iapp.org/news/a/eu-member-states-finalize-digital-omnibus-negotiating-stance)). No change to the marketing rules is in force.

---

## 3. Phone, SMS, DMs and contact forms (open questions b and c)

### 3.1 Phone sales: the written-confirmation rule does not cover B2B (b)
- The rule is KSL 6:12, in force since **1.1.2023**. After a phone offer to a *consumer*, the trader must send the offer in durable form, and the consumer is bound only after accepting it in durable form ([Finlex KSL 6:12](https://www.finlex.fi/fi/laki/ajantasa/1978/19780038); [Valtioneuvosto 8.7.2022](https://valtioneuvosto.fi/-/1410853/kuluttajansuojalain-uudistus-tiukentaa-puhelinmyynnin-saantelya)). The Ministry of Justice published an evaluation of its effects on 30.12.2025 ([OM selvitys](https://api.eduskunta.fi/documents/fi/51B12635-67A9-4B3E-A9B4-41849773064A.pdf)). It mentions no extension to businesses.
- Under **KSL 1:4**, a *kuluttaja* is a natural person acquiring goods *mainly for purposes other than their business*. A sole trader buying software for the salon is therefore **not** a consumer, so 6:12 does not apply ([Finlex KSL](https://www.finlex.fi/fi/laki/ajantasa/1978/19780038)).
- **Watch out:** if a sole trader would mainly use the product privately, KSL could apply. Don't sell consumer-type products by phone without the confirmation step. In 2024–2026, no move to opt-in telemarketing was found ([search notes](https://www.verkkouutiset.fi/a/myyntipuheluiden-vastaanottamiseen-halutaan-kuluttajan-ennakkosuostumus-63915/)). **Unverified for 2026.**
- **B2B phone rules that do apply:** §200(2) opt-out, GDPR information at the first call, and Art. 21 objection ([TSV FAQ](https://tietosuoja.fi/usein-kysyttya-suoramarkkinointi)). The 1061/1978 business-practice law also applies (section 7).
- **Good practice from the B2B sales contract angle:** confirm any agreement made by phone in writing anyway. It prevents disputes.

### 3.2 DMs and contact forms (c)
- §200(1) lists *sähköpostiviestit, tekstiviestit, puheviestit, ääniviestit, kuvaviestit*. Act 917/2014 does not define "sähköpostiviesti" separately (the §3 definitions were checked) ([Finlex](https://www.finlex.fi/fi/laki/ajantasa/2014/20140917)).
- The underlying ePrivacy Directive defines "electronic mail" broadly: any text, voice, sound or image message sent over a public communications network that can be stored until the recipient collects it ([Directive 2002/58/EC Art. 2](https://eur-lex.europa.eu/eli/dir/2002/58/oj)). Since the European Electronic Communications Code, messaging in social platforms is generally an interpersonal communications service ([IAPP](https://iapp.org/news/a/new-european-electronic-communications-code-means-the-application-of-the-eprivacy-directive-to-otts)).
- **No Finnish authority guidance or decision was found on platform DMs or contact forms.** Conclusion: **treat both as electronic direct marketing** with the same recipient-type rules as email. This is an inference, flagged in section 9.
- Platform terms independently prohibit automation. LinkedIn bars bots and scraping and requires compliance with anti-spam laws ([LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement)). Instagram bars collecting information in an automated way without express permission ([Instagram Terms](https://help.instagram.com/581066165581870)).

### 3.3 SMS technical change (2026)
From **4.5.2026**, organisations sending SMS must have their sender ID verified via their operator. From **2.11.2026**, unauthorised alphanumeric senders are shown as "Roskaposti" ([Traficom](https://www.traficom.fi/en/news/measures-combat-scam-messages-further-strengthened-consumer-vigilance-still-required); [Traficom 12.1.2026](https://traficom.fi/en/news/new-measures-introduced-combat-scam-messages-sent-name-organisations)). Use an operator or SMS gateway that handles sender verification.

---

## 4. Ban registers and B2B (open question d)

| Register | What it covers | Binds B2B? |
|---|---|---|
| **ASML Puhelintarjonnan rajoituspalvelu (Puhelin-Robinson)** | Consumers restrict telemarketing by calling 0600 13404. The restriction lasts 3 years and does not stop an existing customer relationship. Over 600 companies use it ([ASML](https://asml.fi/kieltopalvelut/)). | **No.** It is a self-regulatory consumer service, made by the adult who holds the subscription. Filtering requires an ASML licence "to take consumers' restrictions into account" ([ASML](https://asml.fi/kieltopalvelut/)). If you call a toiminimi on the owner's *personal* subscription, the owner may have registered. Screening is good practice, not a legal duty. |
| **ASML Posti-Robinson** | Consumers restrict addressed postal marketing for 3 years ([ASML](https://asml.fi/kieltopalvelut/)). | No (consumer service). |
| **DVV population register ban (suoramarkkinointikielto)** | Stops DVV disclosing a person's name and address for marketing. It applies only to disclosures from the population information system. Phone marketing cannot be banned there ([KKV](https://www.kkv.fi/en/consumer-affairs/marketing-sales-and-indicating-prices/direct-marketing/prohibiting-direct-marketing-and-telemarketing/); [secondary summary](https://yotru.com/fi/blog/osoitteellinen-suoramainonta-kielto)). | **No** for business-register data. It matters only if you buy consumer address lists. |
| **PRH / YTJ** | No direct-marketing ban flag was found in the YTJ API schema ([schema](https://avoindata.prh.fi/opendata-ytj-api/v3/schema?lang=en)). | — |
| **The business's own refusal** | §200(2), §202, GDPR Art. 21. | **Yes, always.** Make it permanent in your suppression list. |

---

## 5. Scraping, database rights and platform terms (open question e)

### 5.1 Law
- **Tekijänoikeuslaki §49:** the maker of a catalogue or compilation of a large amount of data, or of a database requiring substantial investment, has exclusive rights to copy it and make it available ([Finlex 404/1961 §49](https://www.finlex.fi/fi/laki/ajantasa/1961/19610404)). This protects extraction of substantial parts, and repeated systematic extraction of insubstantial parts. Protection lasts 15 years from completion. These details come from the statute's structure and were not re-read line by line (section 9).
- **CJEU C-30/14 Ryanair (2015):** even where a database is not protected by copyright or §49, the owner can restrict use contractually through its terms ([curia C-30/14](https://curia.europa.eu/juris/liste.jsf?num=C-30/14)). So the terms matter on their own.
- GDPR applies to anything scraped about natural persons, including toiminimi.

### 5.2 Platform terms (as read 24.11.2026)
| Source | Terms on scraping and storage | Verdict |
|---|---|---|
| **Google Places API (New)**, EEA billing | General terms: "No Scraping". No pre-fetching, indexing, storing or rehosting outside the Services, and no copying and saving of business names, addresses or reviews. "No Caching" except as expressly permitted ([Google Maps Platform EEA terms §3.2.3](https://cloud.google.com/terms/maps-platform/eea)). Service terms: **place_id may be cached**. Places lat/lng may be cached for **30 days**. Content other than lat/lng/place_id may be used only as the "Places API EEA Permitted Uses" allow, and not with any map ([EEA Service Specific Terms §15](https://cloud.google.com/terms/maps-platform/eea/maps-service-terms), last modified 28.10.2026). | **Lookup only.** Store place_id. Fetch details live when the user opens a lead. Never build your lead DB from Places names, phones or websites. |
| **Fonecta / Finder.fi** | Materials may not be copied, reproduced, published or transferred without written permission. They may not be used **for direct marketing to private persons or any other commercial purpose**. Use is limited to own non-commercial use (Fonecta terms of use, updated 5.1.2026, [tuki.fonecta.com/fonectan-kayttoehdot](https://tuki.fonecta.com/fonectan-kayttoehdot)). | **Don't scrape.** Licensed route: Finder Pro or the Finder Kohderyhmätyökalu (target-group tool) ([service description](https://tuki.fonecta.com/hubfs/PDF-files/Palvelukuvaus%20Finder%20Kohderyhm%C3%A4ty%C3%B6kalu.pdf?hsLang=fi-fi); [Finder Pro](https://www.finder.fi/finderpro)). |
| **Timma** | The terms page is a JavaScript app and its text could not be retrieved. timma.fi/robots.txt returned nothing ([timma.fi/kayttoehdot](https://timma.fi/kayttoehdot)). | **Unverified.** Use manual browsing as a signal only. |
| **Varaa.com** | On 24.11.2026 the domain served a parked page stating it is **for sale** ([varaa.com/llms.txt](https://varaa.com/llms.txt)). | Not a usable source. Re-check if needed. |
| **Fresha** | Prohibits scraping content or "creat[ing] an electronic database by systematically downloading and storing" site content, and prohibits spiders, crawlers and bots (Website Terms of Use, updated 12.8.2026, [terms.fresha.com/terms-use](https://terms.fresha.com/terms-use)). | Don't scrape. Manual signal only. |
| **Wolt** | Prohibits collecting, copying or transferring information from Wolt without consent, using bots, and access other than through Wolt's interfaces ([Wolt FI User Terms](https://explore.wolt.com/en/fin/terms)). | Don't scrape. |
| **Foodora** | The terms page returned HTTP 403. | Unverified. Assume similar terms. |
| **Instagram / Facebook** | No collecting information in an automated way without express permission ([Instagram Terms](https://help.instagram.com/581066165581870); Meta [Automated Data Collection Terms](https://www.facebook.com/legal/automated_data_collection_terms)). | Manual viewing and manual DMs only. |
| **LinkedIn** | No software, scripts, robots, crawlers or browser plugins to scrape or copy; anti-spam laws apply ([User Agreement](https://www.linkedin.com/legal/user-agreement)). | Manual only. No automation tools. |
| **PRH Virre / ytj.fi web search** | Meant for individual lookups. **Search robots are not allowed**, and daily searches per IP are limited ([PRH rules, 1.6.2022](https://www.prh.fi/en/kaupparekisteri/tietopalvelupelisaannot.html)). | Use the open-data API, not the web UI. |
| **Business's own website** | Reading a published contact page is lawful, subject to GDPR (the source must go in the Art. 14 notice). Respect robots.txt and the site's terms. Fetch politely. | OK for generic and yhteisö addresses, with minimal storage. |

---

## 6. Data sources for discovering businesses

### 6.1 PRH / YTJ open data API (primary source)
- **Endpoint:** `https://avoindata.prh.fi/opendata-ytj-api/v3/companies`. The bulk download is `/all_companies` (ZIP of JSON). Code lists: `/description?code=TOIMI4&lang=fi` ([OpenAPI schema](https://avoindata.prh.fi/opendata-ytj-api/v3/schema?lang=en)).
- **Licence:** CC BY 4.0, free, updated daily ([schema](https://avoindata.prh.fi/opendata-ytj-api/v3/schema?lang=en); [ytj.fi open data](https://ytj.fi/en/index/opendata.html)). HTTP 429 is returned on too many requests. No numeric rate limit is published.
- **Filters:** `name`, `location`, `businessId`, `companyForm`, `mainBusinessLine` (TOL code or text), `registrationDateStart/End`, `postCode`, `businessIdRegistrationStart/End`, `page` (100 results per page).
- **Fields:** Y-tunnus, names (including auxiliary names), main line of business, **website**, company form, register entries (e.g. VAT), addresses, status and dates. **No phone and no email** ([ytj.fi](https://ytj.fi/en/index/opendata.html)).
- **Own test, 24.11.2026:** `mainBusinessLine=96210` (hair and barber, TOL 2025) returned 1,744 entities: 1,441 Oy, 206 Ky, 93 Ay, 3 osuuskunta, 1 branch, and **0 sole traders**. 398 (23%) had a website. `location` and `postCode` filters combined with the industry code returned surprisingly few hits (e.g. 1 restaurant Oy in Tampere). **Filter locally on the bulk file instead of relying on those parameters.**
- **Sole traders are excluded** ("except private traders", [ytj.fi](https://ytj.fi/en/index/opendata.html)). Consequence: **anything not found in PRH open data is "unknown or probably toiminimi", which means the consent-only channels apply.**
- Statistics Finland's business-register extracts (paid) **do include sole traders** (legal form "luonnollinen henkilö"), with postal address and phone for some. Email is not included ([stat.fi tietosisältö](https://stat.fi/fi/palvelut/tilaa-tilastotietoja/tietopoiminnat-yritysrekisterista/tietosisalto)). Licence terms for marketing use were not checked.

### 6.2 Industry codes: TOL 2025 is live in YTJ
YTJ switched to TOL 2025 at the start of 2026 ([Vero](https://www.vero.fi/tietoa-verohallinnosta/uutishuone/uutiset/uutiset/2025/yrityksen-toimialaluokitus-uudistuu-vuoden-2026-alussa/); [Tilastokeskus](https://stat.fi/fi/dokumentaatio/tilastoinnin-kehittaminen/toimialaluokitus-uudistuu)). API records show `typeCodeSet: TOIMI4` with registration date 2026-01-01. The schema text still says "TOL 2008". The codes below come from the YTJ code lists TOIMI4 (2025) and TOIMI3 (2008) ([API](https://avoindata.prh.fi/opendata-ytj-api/v3/description?code=TOIMI4&lang=fi)):

| Segment | TOL 2025 (use now) | TOL 2008 (legacy) | Entities in open data, 24.11.2026 |
|---|---|---|---|
| Restaurants | 56111 Ruokaravintolat; 56112 Pikaruokaravintolat ja ruokakioskit | 56101 Ravintolat; 56103 Ruokakioskit | 11,237 / 718 |
| Cafés | 56302 Kahvilat ja muu alkoholittomien juomien tarjoilu | 56302 Kahvilat ja kahvibaarit; 56102 Kahvila-ravintolat | 1,481 |
| Bars | 56301 Baarit ja muu alkoholijuomien tarjoilu | 56301 Olut- ja drinkkibaarit | 867 |
| Catering | 56210 Tapahtumien catering; 56220 Sopimusperusteiset catering | 56210 Pitopalvelu; 56290 | – |
| Food trucks | 56120 Liikkuva ravitsemistoiminta | (in 56103) | – |
| Hair and barbers | 96210 Kampaamo- ja parturipalvelut | 96021 Parturit ja kampaamot | 1,744 |
| Beauty, nails, cosmetology | 96220 Kauneudenhoitopalvelut | 96022 | 1,403 |
| Spa, sauna | 96230 Kylpylä-, sauna- ja höyrysaunapalvelut | 96040 | 348 |
| Massage, alternative therapy | 86960 Perinteisiin, täydentäviin ja vaihtoehtoisiin hoitomuotoihin perustuvat palvelut; 86950 Fysioterapia | 86909 Muu terveyspalvelu; 86901 Fysioterapia | 12 (86960) |
| Other personal services | 96999 Muu muualla luokittelematon …; 96991 Lemmikkieläinpalvelut | 96090 | 2,552 |
| Gyms | 93130 Kuntokeskusten toiminta | 93130 | – |
| Small shops (examples) | 47750 Kosmetiikka; 47761 Kukat; 47770 Kellot ja korut | same | – |

Where trained massage therapists sit in TOL 2025 (86960 vs 86990 or 96999) was not verified.

### 6.3 Other sources
| Source | Fields | Licence / cost | Contacts? | Use in radar |
|---|---|---|---|---|
| **OpenStreetMap** via [Geofabrik taginfo FI](https://taginfo.geofabrik.de/europe:finland/) or Overpass | name, address, phone, website, email, opening hours, social | ODbL: share-alike and attribution ([OSM copyright](https://www.openstreetmap.org/copyright)). Free. Public Overpass servers were overloaded (HTTP 502) on 24.11.2026, so use a Geofabrik Finland extract. | Partly. Counts on 23.11.2026: hairdresser 2,649 (phone 35%, website 30%, email 8%); cafe 3,005 (website 44%, phone 27%, email 10%); restaurant 6,100 (website 59%, phone 39%, email 15%); beauty 881; massage 466 ([taginfo](https://taginfo.geofabrik.de/europe:finland/)) | **Good discovery layer, including sole traders.** Keep ODbL attribution. If you redistribute the derived DB, share-alike applies. |
| **Google Places API (New)** | displayName, address, types (Pro); **phone and website are Enterprise SKU** ([Place Details fields](https://developers.google.com/maps/documentation/places/web-service/place-details)) | Free monthly caps per SKU since 1.3.2025 ([Google](https://developers.google.com/maps/billing-and-pricing/march-2025)). List prices: Text Search Pro $32/1000 after 5,000 free; Place Details Enterprise $20/1000 after 1,000 free; IDs-only calls unlimited ([pricing](https://developers.google.com/maps/billing-and-pricing/pricing)). EEA prices may differ. | Yes, but **not storable** | Live enrichment on screen only. Store place_id. |
| **Asiakastieto (Enento)** | Companies plus decision-makers, with titles, phones and emails, from YTJ, PRH and other sources | Paid. Data usage period 2 months. Customers are pointed to ASML B2B rules ([Asiakastieto](https://www.asiakastieto.fi/web/fi/asiakastieto-yrityksena/tietosuoja/yritys-ja-paattajatiedon-yllapito-ja-kaytto-markkinointitarkoituksiin.html)) | Yes | Compliant bought lists. You remain controller for your use. Coverage of sole traders not stated. |
| **Vainu** | Nordic company data, signals, CRM sync | From €3,500/yr plus €200 onboarding, 12-month auto-renew ([vainu.com/pricing](https://vainu.com/pricing)) | Partly | Probably oversized for micro-SaaS. |
| **Fonecta Finder Pro / Kohderyhmätyökalu** | Companies, decision-makers, contacts | Paid. Price not published. Finder Pro Luotto is €15/month (€10.50 for Yrittäjät members) ([Yrittäjät](https://www.yrittajat.fi/en/member-benefits/for-the-first-time-in-finland-unlimited-credit-reports-for-a-fixed-monthly-fee/)) | Yes | Licensed alternative to scraping Finder. |
| **Dun & Bradstreet FI, Alma Talent, Intrum, Lowell, Roaring** | YTJ-based data services ([YTJ list](https://ytj.fi/index/avoindata/muut-palveluntarjoajat.html)) | Quote-based | Varies | Pricing and GDPR handling were not researched individually. |
| **Leadfeeder (Dealfront)** | Website-visitor company identification | Not researched | – | Inbound signal only. |
| **Booking and delivery platforms** (Timma, Fresha, Wolt, Foodora) | A listing signals an active business | Terms prohibit scraping (5.2) | – | Manual signal ("has online booking: yes/no") entered by you, not scraped. |
| **Business's own website** | Generic email, phone, owner name | Public. GDPR applies. | Yes | Fetch the contact page on demand. Store only the address you will use and record its source URL. |

### 6.4 Inbound and partnership channels (no consent issues)
- **Suomen Yrittäjät:** 362 local associations, 21 regional organisations, 47 industry organisations ([Yrittäjät](https://www.yrittajat.fi/tietoa-meista/aluejarjestot-ja-paikallisyhdistykset/)). Offer a member benefit, speak at local events, or sponsor a breakfast meeting.
- **Inbound content:** a Google Business Profile for your own business, short how-to posts in local Facebook groups (follow group rules), webinars with your own consent form, partnerships with accountants (tilitoimistot), and referral credits from existing customers.
- A Finnish open-data lead tool (Liiditutka) uses the same conservative rules (generic Oy address OK; toiminimi treated like a private person) ([liiditutka.com](https://liiditutka.com/)). This is a market signal, not a legal source.

---

## 7. Content rules for the message itself
- **§203** (verified): the message must be recognisable as marketing, must not conceal the sender, and must give a valid opt-out address ([Finlex](https://www.finlex.fi/fi/lainsaadanto/2014/917)).
- **Laki sopimattomasta menettelystä elinkeinotoiminnassa (1061/1978):** the general clause against conduct contrary to good business practice, and the ban on misleading claims, apply B2B ([Finlex 1061/1978](https://www.finlex.fi/fi/laki/ajantasa/1978/19781061)). The text was not re-read in this session. Don't overstate savings, imitate invoices, or use fake urgency.
- The consumer protection act's marketing chapter does not apply B2B (KSL 1:4 definitions, [Finlex](https://www.finlex.fi/fi/laki/ajantasa/1978/19780038)).
- **ASML B2B practice:** the product must be a genuine B2B product. Put the Y-tunnus and privacy link in the footer. Tell the recipient *why* they are receiving the message, because the company name alone is not enough to identify the data source ([ASML 2018](https://asml.fi/wp-content/uploads/2023/12/ASML_B2B_Email_marketing_practice.pdf)).

---

## 8. Recommended compliant architecture

### 8.1 Ingest
1. **PRH bulk file** (`/all_companies`, daily or weekly), filtered locally by TOL 2025 codes (6.2) and municipality code. This is the authoritative "is it a yhteisö" list.
2. **OSM Finland extract** (Geofabrik) for shops and cafés, including sole traders, with ODbL attribution.
3. **On-demand only:** the business's own contact page, and Google Places place_id lookups shown live.
4. **Never:** Fonecta/Finder, Wolt, Fresha, Foodora, Instagram, LinkedIn or ytj.fi web scraping.

### 8.2 Classify each lead
| Class | How determined | Allowed channels |
|---|---|---|
| `YHTEISO_CONFIRMED` | Y-tunnus found in PRH open data with form Oy/Oyj/Ky/Ay/Osuuskunta, and status active | Generic email ✓ (opt-out); SMS to a company landline or role number ✓; phone ✓; letter ✓; visit ✓; named-person email only with a documented asemavaltuus note |
| `TOIMINIMI_LIKELY` | Not in PRH open data but present in OSM or website; or the name contains "Tmi"/"toiminimi"; or a Y-tunnus that open data does not return | Phone ✓; letter ✓; visit ✓; **email, SMS and DM ✗ until consent is recorded** |
| `UNKNOWN` | No Y-tunnus match | Same as toiminimi |
| `CONSENTED` | Consent record (who, when, channel, wording) | Channels consented to |
| `CUSTOMER` | Contract exists | Similar products under §200(3) or §202, with opt-out |
| `SUPPRESSED` | Any refusal or objection | **None**, permanently. Keep a minimal hash (business ID, domain, email, phone). |

### 8.3 Store / don't store
- **Store:** business name, Y-tunnus, form, TOL code, municipality, website, the one contact address you will use, the **source URL and fetch date for each field**, classification, allowed channels, contact log, consent and objection records.
- **Don't store:** Places content other than place_id (lat/lng up to 30 days); personal social-media profiles; home addresses; henkilötunnus; review text; staff lists; anything scraped from barred platforms.
- **Retention:** delete uncontacted leads after about 6 months (the repo's `retention_days: 180`). Delete contacted, non-responding leads after about 12 months. Keep suppression entries indefinitely in minimal form. No Finnish fixed period exists, so justify yours in the LIA ([TSV: säilytyksen rajoittaminen](https://tietosuoja.fi/sailytyksen-rajoittaminen)).

### 8.4 Required features
- A suppression check before every display or send, plus a one-click opt-out link that works without login.
- An audit log of the source for each field, sends, and refusals.
- An Art. 14 snippet auto-inserted with the real data source per lead.
- An LIA document and record of processing (see `docs/lia.md`). Privacy notice (*tietosuojaseloste*) contents per Art. 13/14: controller and Y-tunnus, purposes, legal basis and legitimate interest, categories, **sources**, recipients and processors (email provider), transfers outside the EEA, retention, rights (including objection), and the right to complain to TSV.
- Rate limits: small batches (under 50) and personal edits before sending (section 10).

### 8.5 First-contact templates

**Suomeksi (Oy, yleinen osoite):**

> Aihe: Ajanvaraus ja asiakasviestit yhdestä paikasta – [Yrityksesi]
>
> Hei [Yrityksen nimi],
>
> olen [Nimi], [Toiminimi] (Y-tunnus [1234567-8]). Teen [tuote]-palvelua pienille [kampaamoille/kahviloille], joka [yksi konkreettinen hyöty, esim. vähentää peruuttamattomia poisjääntejä tekstiviestimuistutuksilla].
>
> Löysin yrityksenne [lähde: PRH:n avoimesta datasta / verkkosivultanne osoitteesta X]. Saisinko näyttää 15 minuutissa, miten tämä toimisi teillä? Jos ei kiinnosta, vastaa vain "ei", niin en ota enää yhteyttä.
>
> Ystävällisin terveisin
> [Nimi], [Toiminimi], Y-tunnus [ ], [osoite], [puhelin], [sähköposti]
>
> *Tämä on markkinointiviesti. Käsittelemme yrityksenne yhteystietoja oikeutetun edun perusteella B2B-markkinointiin. Tiedot on saatu [lähde]. Sinulla on oikeus vastustaa käsittelyä milloin tahansa: [kieltolinkki] tai vastaa "ei". Tietosuojaseloste: [linkki].*

**In English (Oy, generic address):**

> Subject: Bookings and customer messages in one place – [Your company]
>
> Hello [Business name],
>
> I'm [Name] from [Trade name] (Business ID [1234567-8]). I build [product] for small [salons/cafés]. It [one concrete benefit].
>
> I found your business via [source: the Finnish Patent and Registration Office open data / your website at X]. Could I show you in 15 minutes how it would work for you? If you're not interested, just reply "no" and I won't contact you again.
>
> Best regards,
> [Name], [Trade name], Business ID [ ], [address], [phone], [email]
>
> *This is a marketing message. We process your business contact details for B2B marketing on the basis of legitimate interest. Source: [source]. You can object at any time: [opt-out link] or reply "no". Privacy notice: [link].*

**Phone opener for a toiminimi (no email until permission):** "Hei, [Nimi] [Toiminimestä], soitan myyntipuhelun. Löysin numeronne [lähteestä]. Sopiiko kaksi minuuttia? … Saanko lähettää lyhyen esittelyn sähköpostiin [osoite]?" Log a yes as consent with the date and exact wording. On a no, suppress immediately.

---

## 9. Confidence and what could not be verified

| Item | Status |
|---|---|
| Toiminimi email requires consent | **High.** Statute plus TSV 2020 decision. The role-relevance grey area for business-management software is **untested**. |
| Generic yhteisö address is opt-out; named employee needs asemavaltuus | **High.** TSV FAQ, read 24.11.2026. |
| A Traficom guidance page on B2B email | **Not found.** Traficom is not the supervisor (§305). |
| €7,000 fine in 2020 for SMS marketing | **Unverified.** Secondary source only. |
| TSV 2020/702 full reasoning | **Not read.** The Finlex page body did not extract. |
| DMs and contact forms count as "sähköpostiviesti" | **Inference.** No Finnish authority source. Treated conservatively. |
| No 2024–2026 move to B2B or opt-in telemarketing | **Medium.** Nothing found. The OM memo of 30.12.2025 discusses only the consumer rule. |
| ASML and DVV do not bind B2B | **High** for DVV and ASML's legal status. ASML's own page describes consumer restrictions. |
| Timma terms; Foodora terms | **Not retrieved** (JavaScript app / HTTP 403). |
| Varaa.com | Domain parked and for sale on 24.11.2026. The service's status was not investigated further. |
| §49 copyright detail (15 years, systematic extraction) | Section heading and core text read. The full subsections were not extracted. |
| 1061/1978 content | Not re-read this session. |
| Google EEA prices and the "Places API EEA Permitted Uses" text | Global price list read. The EEA permitted-uses page was not read. |
| TOL 2025 code for massage therapists | Not verified. |
| PRH `location` and `postCode` filters | Behaved unexpectedly in tests. Local filtering is recommended. |
| Vendor pricing other than Vainu, and the vendors' GDPR handling | Mostly not verified. |
| Response-rate figures | Vendor benchmarks, mainly from US and global senders. Not Finland-specific. |

---

## 10. Practical response-rate tips for Finnish small businesses (open question f)

Benchmarks (vendor data, global, 2026): average cold-email reply rates are about **2–5%** (Instantly 3.43%, with the top 10% at 10.7% or more ([Instantly](https://instantly.ai/report-page)); Saleshandy 4.5% ([Saleshandy](https://saleshandy.com/blog/cold-email-statistics/)); Apollo 2.09% ([Apollo](https://www.apollo.io/insights/what-is-a-good-benchmark-for-reply-rates-in-cold-outreach))). Lists **under 50 recipients** average about 5.8%, against about 2.1% for large lists ([Woodpecker](https://woodpecker.co/blog/cold-email-statistics/); [lemlist](https://lemlist.com/blog/cold-email-benchmarks/)). **Follow-ups** produce 42–57% of replies ([Instantly](https://instantly.ai/report-page); [Saleshandy](https://saleshandy.com/blog/cold-email-statistics/)). Strong personalisation roughly doubles replies ([lemlist](https://lemlist.com/blog/cold-email-benchmarks/)).

What follows for this radar:
1. **Write in Finnish** (Swedish in Swedish-speaking areas). Keep it short (about 80–120 words), factual, with no hype. Finnish business communication is direct and fact-based ([MyHelsinki](https://www.myhelsinki.fi/live-work/plan-your-move/7-tips-for-finnish-office-etiquette/)).
2. **Send small batches** (10–30 a day) with one specific observation per business (e.g. "your booking is phone-only").
3. **Send at most one polite follow-up** after 5–7 working days, then stop. Fewer follow-ups also means fewer complaints.
4. **Time it to the trade.** Salons are busiest evenings and Saturdays; cafés at lunch. Email Monday–Wednesday mornings. Visit mid-afternoon on a weekday.
5. **Phone or visit sole traders first**, then email with permission. That is the legal route and usually converts better.
6. **Give local proof:** a named local customer (with permission), a price in euros including VAT, and a free trial with no card required.
7. **Use Suomen Yrittäjät local associations and accountants** for warm introductions. AI and digital adoption among Finnish SMEs is rising (57% using AI in late 2025, [Yrittäjät](https://www.yrittajat.fi/ajankohtaista/tiedotteet/yrittajagallup-tekoalyn-kaytto-on-yleistynyt-nopeasti-suomen-pk-yrityksissa/)), so a practical "saves X hours a week" message lands.
8. **Protect deliverability:** a custom domain with SPF, DKIM and DMARC, a plain-text style, few links, and an immediate opt-out. If you use SMS, verify your sender ID (from 2026, Traficom).
