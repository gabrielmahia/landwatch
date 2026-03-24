"""
LandWatch Kenya — Riparian encroachment mapper.

Kenya's Water Act 2016 (s.72) mandates a 30-metre setback from all rivers
and streams. Encroachment into these riparian reserves is the primary
structural cause of urban flash floods — buildings redirect and constrict
water flow, causing floods to escape onto populated land.

Data sources (all public domain):
  - WRMA (Water Resources Management Authority) basin surveys
  - NEMA (National Environment Management Authority) public enforcement register
  - NCC (Nairobi City County) Drainage Master Plan 2020
  - Mukuru Special Planning Area 2021
  - World Bank Western Kenya Community Floods Project 2019

This tool maps documented riparian encroachments, explains the legal
framework, and surfaces which rivers and cities have the highest
enforcement backlog.

TRUST RULE:
  - All locations are from published enforcement records — not surveillance
  - This tool tracks structural patterns, not individuals
  - Enforcement actions are factual — see source column for citations
  - Severity ratings reflect documented enforcement notices, not guesses
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import urllib.request
import json
import xml.etree.ElementTree as ET
import re

st.set_page_config(
    page_title="Hifadhi — Land & River Watch Kenya",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Mobile CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

.lw-header {
    background: linear-gradient(135deg, #1a3a1a 0%, #2d5a2d 60%, #4a7c4a 100%);
    color: white; padding: 1.6rem 2rem; border-radius: 10px; margin-bottom: 1.2rem;
}
.lw-header h1 { font-family:'IBM Plex Mono',monospace; font-size:1.8rem; margin:0 0 .2rem; letter-spacing:-1px; }
.lw-header p  { font-size:.9rem; opacity:.75; margin:0; }

.sev-critical { background:#f8d7da; border-left:4px solid #dc3545; padding:.5rem 1rem; border-radius:4px; font-size:.83rem; margin:.3rem 0; }
.sev-high     { background:#fff3cd; border-left:4px solid #ffc107; padding:.5rem 1rem; border-radius:4px; font-size:.83rem; margin:.3rem 0; }
.sev-medium   { background:#d1ecf1; border-left:4px solid #17a2b8; padding:.5rem 1rem; border-radius:4px; font-size:.83rem; margin:.3rem 0; }
.law-box { background:#e8f4fd; border-left:4px solid #2d5a2d; padding:.7rem 1rem; border-radius:4px; font-size:.83rem; margin-bottom:1rem; }
.source-note { background:#f8f9fa; border-left:3px solid #6c757d; padding:.5rem .9rem; border-radius:3px; font-size:.8rem; margin-bottom:.5rem; }

@media (max-width: 768px) {
    [data-testid="column"] { width:100% !important; flex:1 1 100% !important; min-width:100% !important; }
    [data-testid="stMetricValue"] { font-size:1.3rem !important; }
    [data-testid="stDataFrame"]   { overflow-x:auto !important; }
    .stButton>button { width:100% !important; min-height:48px !important; }
    .lw-header h1 { font-size:1.3rem !important; }
}

    /* Metric text — explicit colours, light + dark (both OS pref and Streamlit toggle) */
    [data-testid="stMetricLabel"]  { color: #444444 !important; font-size: 0.8rem !important; }
    [data-testid="stMetricValue"]  { color: #111111 !important; font-weight: 700 !important; }
    [data-testid="stMetricDelta"]  { color: #333333 !important; }
    @media (prefers-color-scheme: dark) {
        [data-testid="stMetricLabel"] { color: #aaaaaa !important; }
        [data-testid="stMetricValue"] { color: #f0f0f0 !important; }
        [data-testid="stMetricDelta"] { color: #cccccc !important; }
    }
    [data-theme="dark"] [data-testid="stMetricLabel"],
    .stApp[data-theme="dark"] [data-testid="stMetricLabel"] { color: #aaaaaa !important; }
    [data-theme="dark"] [data-testid="stMetricValue"],
    .stApp[data-theme="dark"] [data-testid="stMetricValue"] { color: #f0f0f0 !important; }
    [data-theme="dark"] [data-testid="stMetricDelta"],
    .stApp[data-theme="dark"] [data-testid="stMetricDelta"] { color: #cccccc !important; }

</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────
DATA = Path(__file__).parent / "data"


@st.cache_data(ttl=3600)
def fetch_rainfall_signal():
    """7-day national rainfall from Open-Meteo for 6 key river cities."""
    cities = {
        "Nairobi":  (-1.29,  36.82),
        "Mombasa":  (-4.04,  39.67),
        "Kisumu":   (-0.09,  34.77),
        "Nakuru":   (-0.30,  36.08),
        "Eldoret":  (0.52,   35.27),
        "Thika":    (-1.03,  37.09),
    }
    results = {}
    for city, (lat, lon) in cities.items():
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&daily=precipitation_sum&forecast_days=7"
                f"&timezone=Africa%2FNairobi"
            )
            with urllib.request.urlopen(url, timeout=6) as r:
                d = json.loads(r.read())
            precip = d.get("daily", {}).get("precipitation_sum", [])
            total  = round(sum(precip), 1)
            results[city] = {"total_mm": total, "flood_risk": total > 60, "daily": precip}
        except Exception:
            results[city] = {"total_mm": None, "flood_risk": False, "daily": []}
    return results


@st.cache_data(ttl=7200)
def fetch_ndma_alerts():
    """NDMA drought and flood publications."""
    try:
        req = urllib.request.Request(
            "https://www.ndma.go.ke/feed/",
            headers={"User-Agent": "landwatch-kenya/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            root = ET.fromstring(r.read())
        items = []
        for item in root.findall(".//item")[:5]:
            title = item.findtext("title", "").strip()
            link  = item.findtext("link",  "").strip()
            date  = item.findtext("pubDate", "").strip()[:16]
            desc  = re.sub(r"<[^>]+>", "", item.findtext("description", "")).strip()[:160]
            if title:
                items.append({"title": title, "link": link, "date": date, "summary": desc})
        return items
    except Exception:
        return []

@st.cache_data(ttl=86400)
def load_violations():
    return pd.read_csv(DATA / "encroachments" / "documented_violations.csv")

@st.cache_data(ttl=86400)
def load_rivers():
    return pd.read_csv(DATA / "rivers" / "rivers_reference.csv")

violations = load_violations()
rivers = load_rivers()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="lw-header">
  <h1>🗺️ Hifadhi — LandWatch Kenya</h1>
  <p>Riparian encroachment mapper · Water Act 2016 compliance · NEMA / WRMA enforcement data</p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="law-box">
⚖️ <strong>Legal basis:</strong> Kenya Water Act 2016, Section 72 — all rivers and streams require
a <strong>30-metre riparian setback</strong>. No building, fence, or agricultural activity may be within this
zone without a WRMA riparian permit. NEMA Act (Cap 387) additionally requires Environmental Impact
Assessment before any development in or near riparian land.
Enforcement: WRMA, NEMA, and respective county governments.
</div>
""", unsafe_allow_html=True)

# ── Live rainfall signal — riparian flood risk ─────────────────────────────
_rain = fetch_rainfall_signal()
_ndma = fetch_ndma_alerts()

_risk_cities = [c for c, v in _rain.items() if v.get("flood_risk")]
if _risk_cities:
    st.warning(
        f"⚠️ **Active flood risk signal:** {', '.join(_risk_cities)} — 7-day rainfall forecast "
        f"exceeds 60mm. Riparian encroachments in these cities face elevated inundation risk."
    )

_rain_cols = st.columns(len(_rain))
for col, (city, data) in zip(_rain_cols, _rain.items()):
    if data["total_mm"] is not None:
        col.metric(city, f"{data['total_mm']}mm",
                   delta="⚠️ High" if data["flood_risk"] else "Normal",
                   delta_color="inverse" if data["flood_risk"] else "off")
    else:
        col.metric(city, "—")
st.caption("📡 7-day rainfall forecast · Open-Meteo · updated hourly")

if _ndma:
    with st.expander(f"📡 NDMA Live Alerts ({len(_ndma)} recent)", expanded=False):
        for item in _ndma:
            st.markdown(f"**[{item['title'][:80]}{'…' if len(item['title'])>80 else ''}]({item['link']})**  *{item['date']}*")
            st.caption(item["summary"] + "…")

# ── Navigation ────────────────────────────────────────────────────────────────
PAGE = st.sidebar.radio(
    "Navigate",
    ["📍 Encroachment Map", "🏙️ City View", "🌊 River Profiles", "⚖️ Legal Framework", "🔗 Data Sources"],
)

city_filter = st.sidebar.selectbox(
    "Filter by city",
    ["All cities"] + sorted(violations["city"].unique().tolist()),
)
basin_filter = st.sidebar.selectbox(
    "Filter by basin",
    ["All basins"] + sorted(violations["basin"].unique().tolist()),
)
severity_filter = st.sidebar.multiselect(
    "Severity",
    ["Critical", "High", "Medium"],
    default=["Critical", "High", "Medium"],
)

fv = violations.copy()
if city_filter != "All cities":
    fv = fv[fv["city"] == city_filter]
if basin_filter != "All basins":
    fv = fv[fv["basin"] == basin_filter]
if severity_filter:
    fv = fv[fv["severity"].isin(severity_filter)]


# ═══════════════════════════════════════════════════════════
# ENCROACHMENT MAP
# ═══════════════════════════════════════════════════════════
if PAGE == "📍 Encroachment Map":

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Documented violations", len(violations))
    c2.metric("Rivers affected", violations["river"].nunique())
    c3.metric("Cities covered", violations["city"].nunique())
    c4.metric("Critical severity", (violations["severity"] == "Critical").sum())

    st.divider()

    # Map
    sev_colors = {"Critical": "#dc3545", "High": "#ffc107", "Medium": "#17a2b8"}
    fv["color"] = fv["severity"].map(sev_colors).fillna("#6c757d")

    fig_map = px.scatter_map(
        fv,
        lat="lat", lon="lon",
        color="severity",
        color_discrete_map=sev_colors,
        hover_name="river",
        hover_data={"city": True, "zone": True, "structure_type": True,
                    "policy_ref": True, "lat": False, "lon": False},
        zoom=5.5,
        center={"lat": -0.5, "lon": 37.0},
        map_style="carto-positron",
        height=500,
        title="Documented riparian encroachments — Kenya",
    )
    fig_map.update_traces(marker_size=14)
    fig_map.update_layout(margin=dict(t=40, b=10))
    st.plotly_chart(fig_map, use_container_width=True)

    st.caption(
        "Points show documented enforcement cases from NEMA, WRMA, and NCC public records. "
        "This is not a complete census — it reflects what has entered the public enforcement record. "
        "Actual encroachment extent is higher."
    )

    st.divider()

    # Table
    st.subheader("Documented violations")
    display = fv[[
        "river", "city", "zone", "basin", "severity", "structure_type", "policy_ref", "source"
    ]].rename(columns={
        "river": "River", "city": "City", "zone": "Zone", "basin": "Basin",
        "severity": "Severity", "structure_type": "Structure", "policy_ref": "Legal basis", "source": "Source"
    })
    st.dataframe(display, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════
# CITY VIEW
# ═══════════════════════════════════════════════════════════
elif PAGE == "🏙️ City View":

    st.subheader("Enforcement burden by city")
    city_counts = violations.groupby(["city", "severity"]).size().reset_index(name="count")
    fig = px.bar(
        city_counts, x="city", y="count", color="severity",
        color_discrete_map={"Critical": "#dc3545", "High": "#ffc107", "Medium": "#17a2b8"},
        barmode="stack",
        labels={"city": "City", "count": "Documented violations", "severity": "Severity"},
        title="Riparian enforcement backlog by city",
    )
    fig.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # City deep dive
    selected_city = st.selectbox("City detail", sorted(violations["city"].unique()))
    city_df = violations[violations["city"] == selected_city]

    st.markdown(f"#### {selected_city} — {len(city_df)} documented violations")
    for _, row in city_df.iterrows():
        sev = row["severity"]
        css = "sev-critical" if sev == "Critical" else "sev-high" if sev == "High" else "sev-medium"
        with st.expander(f"{sev}: {row['river']} — {row['zone']}"):
            c1, c2 = st.columns(2)
            c1.markdown(f"**River:** {row['river']}")
            c1.markdown(f"**Basin:** {row['basin']}")
            c1.markdown(f"**Zone:** {row['zone']}")
            c2.markdown(f"**Structure type:** {row['structure_type']}")
            c2.markdown(f"**Setback required:** {row['setback_m']}m")
            c2.markdown(f"**Status:** {row['status']}")
            st.markdown(f"**Legal basis:** {row['policy_ref']}")
            st.markdown(f"**Source:** {row['source']}")


# ═══════════════════════════════════════════════════════════
# RIVER PROFILES
# ═══════════════════════════════════════════════════════════
elif PAGE == "🌊 River Profiles":

    st.subheader("🌊 River profiles — encroachment risk")
    st.caption("Urban length = portion flowing through built-up areas where encroachment risk is highest")

    fig = px.scatter(
        rivers,
        x="urban_length_km",
        y="total_length_km",
        text="river",
        color="basin",
        size="urban_length_km",
        labels={"urban_length_km": "Urban corridor (km)", "total_length_km": "Total length (km)"},
        title="Urban exposure by river",
        height=450,
    )
    fig.update_traces(textposition="top center", textfont_size=9)
    fig.update_layout(margin=dict(t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    for _, row in rivers.iterrows():
        v_count = violations[violations["river"] == row["river"]]
        with st.expander(f"🌊 {row['river']} — {row['basin']} basin ({row['urban_length_km']}km urban)"):
            c1, c2 = st.columns(2)
            c1.metric("Total length", f"{row['total_length_km']} km")
            c1.metric("Urban corridor", f"{row['urban_length_km']} km")
            c2.metric("Setback required", f"{row['setback_m']}m (Water Act 2016)")
            c2.metric("Documented violations", len(v_count))
            st.markdown(f"**Primary threat:** {row['primary_threat']}")
            st.markdown(f"**Enforcement body:** {row['enforcement_body']}")
            st.caption(f"Source: {row['source']}")


# ═══════════════════════════════════════════════════════════
# LEGAL FRAMEWORK
# ═══════════════════════════════════════════════════════════
elif PAGE == "⚖️ Legal Framework":

    st.subheader("⚖️ Kenya riparian law — what it says and who enforces it")

    st.markdown("""
**Water Act 2016 — Section 72**

Establishes that riparian land is land adjacent to a water body.
The Act vests riparian land management in the Cabinet Secretary and
delegates enforcement to the Water Resources Management Authority (WRMA).
The prescribed setback is **30 metres** from the bank of any river or stream.
No person may erect a structure, fence, or carry out earthworks within the
riparian reserve without a **WRMA Riparian Permit**.

**Environmental Management and Co-ordination Act (EMCA) — Cap 387**

Requires an Environmental Impact Assessment (EIA) for any development
affecting riparian land. NEMA issues enforcement notices and can direct
demolition of structures violating the riparian reserve. NEMA Gazette
Notices listing enforcement actions are public record.

**Physical and Land Use Planning Act 2019**

County governments must not approve building plans for structures within
riparian setbacks. Development control is a county function — this is why
Nairobi City County, Mombasa, and Kisumu have their own riparian enforcement
responsibilities alongside WRMA and NEMA.

**What happens to violation structures?**

WRMA / NEMA may issue:
1. A Restoration Order — requiring removal at the owner's cost
2. An Enforcement Notice — formal breach record
3. Criminal prosecution under EMCA s.137 (fine or imprisonment)

In practice, enforcement is resource-constrained. The NCC Drainage Master
Plan (2020) estimated that the majority of Nairobi's informal riparian
settlements would require resettlement programmes, not demolition only.

**Key enforcement bodies**

| Body | Role |
|------|------|
| WRMA | Water resource permits, riparian demarcation |
| NEMA | Environmental enforcement, EIA compliance |
| County government | Building approval, development control |
| Kenya Forest Service | Riparian forest reserves |
| National Land Commission | Land allocation disputes |

**For affected communities**

If you believe your community or your property is at flood risk due to
upstream riparian encroachment:
- File a complaint with NEMA via [nema.go.ke](https://nema.go.ke)
- File a complaint with WRMA via [wrma.go.ke](https://wrma.go.ke)
- Contact your county Environment department

This tool does not provide legal advice. Consult a lawyer for individual cases.
""")


# ═══════════════════════════════════════════════════════════
# DATA SOURCES
# ═══════════════════════════════════════════════════════════
elif PAGE == "🔗 Data Sources":

    st.subheader("🔗 Data sources and methodology")
    st.markdown("""
**Sources used**

| Source | Coverage |
|--------|----------|
| WRMA Basin Riparian Surveys (2019–2020) | All major basins — Athi, Tana, Rift Valley, Lake Victoria |
| NEMA Public Enforcement Register (2021–2022) | Nairobi, Mombasa, Coast, North Eastern regions |
| NCC Drainage Master Plan 2020 | All Nairobi rivers — most comprehensive urban riparian audit |
| Mukuru Special Planning Area 2021 | Mukuru riparian and drainage detail |
| World Bank WKCFP 2019 | Nzoia/Yala basin encroachment documentation |
| FloodWatch Kenya field reports | Supplementary cross-checks |

All sources are public. Each record in `documented_violations.csv` has a
`source` and `verified` column. `verified = confirmed` requires a traceable
citation to one of the sources above.

**What this tool does NOT do**

- Does not monitor live satellite data
- Does not identify individual property owners
- Does not make demolition or legal recommendations
- Does not imply that all residents in riparian zones are willful violators —
  many occupants have no alternative and require resettlement, not removal

**Coverage limitations**

This dataset reflects what has entered the public enforcement record. Actual
encroachment extent is substantially higher. WRMA estimates that tens of
thousands of structures across Kenya's urban rivers are within riparian
setbacks — this tool covers documented enforcement cases only.

**Connection to FloodWatch Kenya**

LandWatch is the structural cause layer that FloodWatch Kenya tracks as
effects. When FloodWatch shows a flood event in Mathare or Mukuru, the
upstream cause is almost always riparian encroachment of the type documented
here. The two tools are designed to be used together.

**Requesting data additions**

Open a GitHub issue at github.com/gabrielmahia/landwatch with:
- River and city
- Enforcement document URL (NEMA Gazette, WRMA notice, county order)
- Date of enforcement action

Unverified locations will not be added.
""")

    st.divider()
    dl_v = violations.copy()
    dl_r = rivers.copy()
    c1, c2 = st.columns(2)
    c1.download_button(
        "📥 Download violation records (CSV)",
        dl_v.to_csv(index=False).encode(),
        file_name="landwatch_violations.csv",
        mime="text/csv",
    )
    c2.download_button(
        "📥 Download river profiles (CSV)",
        dl_r.to_csv(index=False).encode(),
        file_name="landwatch_rivers.csv",
        mime="text/csv",
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Hifadhi · LandWatch Kenya · Data: NEMA, WRMA, NCC public records (public domain) · "
    "CC BY-NC-ND 4.0 · contact@aikungfu.dev · "
    "Not affiliated with NEMA, WRMA, or any county government · "
    "This tool tracks structural patterns, not individuals"
)
