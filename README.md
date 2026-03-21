# 🗺️ Hifadhi — Land & River Watch Kenya

Riparian encroachment mapper — Water Act 2016 compliance data from NEMA, WRMA, and NCC.

[![Live App](https://img.shields.io/badge/Live%20App-hifadhi.streamlit.app-FF4B4B?logo=streamlit)](https://hifadhi.streamlit.app)
[![Live Data](https://img.shields.io/badge/Live%20Data-Open-Meteo%20%C2%B7%20NDMA-00b4d8)](#landwatch)
[![CI](https://github.com/gabrielmahia/landwatch/actions/workflows/ci.yml/badge.svg)](https://github.com/gabrielmahia/landwatch/actions)
[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/License-CC_BY--NC--ND_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc-nd/4.0/)

> **Hifadhi** /hifɑːði/ — *Kiswahili*: conservation, protection, preservation.

---

Kenya's Water Act 2016 (s.72) requires a **30-metre riparian setback** from all rivers and streams.
When buildings encroach on this zone, they redirect water flow during heavy rains — causing the
floods that FloodWatch Kenya documents.

LandWatch maps where that encroachment has been formally documented, which rivers are most
exposed, and what the legal basis for enforcement is.

## What it shows

| View | What you see |
|------|-------------|
| Encroachment Map | Interactive map of documented violations by severity |
| City View | Which cities have the highest enforcement backlog |
| River Profiles | Urban exposure per river (how much flows through built-up areas) |
| Legal Framework | Water Act 2016, EMCA, PLUPA — who enforces what |
| Data Sources | Source citations, coverage limitations, download links |

## Audience

- **Journalists** — document where encroachment is formally recorded
- **NGOs and CBOs** — evidence for advocacy with county governments
- **Urban planners** — understand structural flood risk upstream
- **County assembly members** — track enforcement backlog in their area
- **FloodWatch users** — understand the structural causes behind flood events

## Connection to FloodWatch Kenya

LandWatch is the **cause** layer. FloodWatch Kenya documents the **effects** — flood events,
casualties, displacement. When FloodWatch shows flooding on the Mathare or Mukuru rivers,
the structural reason is almost always encroachment of the kind LandWatch documents.

Both tools cite public sources. Both are designed for community use, not surveillance.

## Trust principles

- **Source per record** — every violation has a NEMA, WRMA, or NCC citation
- **Patterns, not individuals** — this tool tracks structural enforcement patterns
- **Not a complete census** — only records that entered the public enforcement register
- Verify originals: [nema.go.ke](https://nema.go.ke) · [wrma.go.ke](https://wrma.go.ke)

## Local setup

```bash
git clone https://github.com/gabrielmahia/landwatch.git
cd landwatch
pip install -r requirements.txt
streamlit run app.py
```

## Data

`data/encroachments/documented_violations.csv` — 15 enforcement cases across 6 cities  
`data/rivers/rivers_reference.csv` — 10 rivers with basin, urban corridor, and threat profile  

Annual updates as NEMA and WRMA publish new enforcement registers.

## IP & Collaboration

**Owner:** Gabriel Mahia | contact@aikungfu.dev  
**License:** CC BY-NC-ND 4.0  
Not affiliated with NEMA, WRMA, or any county government.

## Security

See [SECURITY.md](SECURITY.md). Report errors to contact@aikungfu.dev.
---

## Portfolio

Part of a suite of civic and community tools built by [Gabriel Mahia](https://github.com/gabrielmahia):

| App | What it does |
|-----|-------------|
| [🌊 Mafuriko](https://floodwatch-kenya.streamlit.app) | Flood risk & policy enforcement tracker — Kenya |
| [💧 WapiMaji](https://wapimaji.streamlit.app) | Water stress & drought intelligence — 47 counties |
| [🏛️ Macho ya Wananchi](https://macho-ya-wananchi.streamlit.app) | MP voting records, CDF spending, bill tracker |
| [🌾 JuaMazao](https://juamazao.streamlit.app) | Live food price intelligence for smallholders |
| [🏦 ChaguaSacco](https://chaguasacco.streamlit.app) | Compare Kenya SACCOs on dividends & loan rates |
| [🛡️ Hesabu](https://hesabu.streamlit.app) | County budget absorption tracker |
| [🗺️ Hifadhi](https://hifadhi.streamlit.app) | Riparian encroachment & Water Act compliance map |
| [💰 Hela](https://helaismoney.streamlit.app) | Chama management for the 21st century |
| [💸 Peleka](https://tumapesa.streamlit.app) | True cost remittance comparison — diaspora to Kenya |
| [📊 Msimamo](https://easystocktrader.streamlit.app) | Macro risk & trade intelligence terminal |
| [🦁 Dagoretti](https://dagoretti-high-school-community-app.streamlit.app) | Alumni atlas & community hub for Dagoretti High |
| [⛪ Jumuia](https://jumuia.streamlit.app) | Catholic parish tools — church finder, pastoral care |

