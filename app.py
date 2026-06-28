"""
Monitor Mundial 2026 — Playoffs en vivo
Fuente: API pública de ESPN (gratuita, sin API key, sin límites)
  https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard
Horarios en Argentina (ART = UTC-3)
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import time

# ─── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Mundial 2026 · Playoffs",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constantes ───────────────────────────────────────────────────────────────
ART = ZoneInfo("America/Argentina/Buenos_Aires")
UTC = timezone.utc

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

# Fechas de la fase eliminatoria del Mundial 2026
PLAYOFF_START = "20260628"   # Ronda de 32 arranca el 28 de junio
PLAYOFF_END = "20260719"     # Final el 19 de julio

STAGE_ORDER = {
    "Round of 32": 1,
    "Round of 16": 2,
    "Quarter-finals": 3,
    "Semi-finals": 4,
    "Third-place playoff": 5,
    "Final": 6,
}

STAGE_LABELS = {
    "Round of 32": "Ronda de 32",
    "Round of 16": "Octavos de Final",
    "Quarter-finals": "Cuartos de Final",
    "Semi-finals": "Semifinales",
    "Third-place playoff": "3er y 4to Puesto",
    "Final": "Final",
}

EMOJI_STAGES = {
    "Round of 32": "⚽",
    "Round of 16": "🔥",
    "Quarter-finals": "💫",
    "Semi-finals": "⚡",
    "Third-place playoff": "🥉",
    "Final": "🏆",
}


def normalize_stage(text: str) -> str:
    """Mapea el texto de etapa de ESPN a nuestra clave interna."""
    t = (text or "").lower()
    if "round of 32" in t or "round-of-32" in t:
        return "Round of 32"
    if "round of 16" in t or "round-of-16" in t:
        return "Round of 16"
    if "quarter" in t:
        return "Quarter-finals"
    if "semi" in t:
        return "Semi-finals"
    if "third" in t or "3rd" in t:
        return "Third-place playoff"
    if "final" in t:
        return "Final"
    return ""


# ─── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;500;600;700&display=swap');

  :root {
    --fifa-blue: #1a3a6e;
    --fifa-gold: #c8a84b;
    --fifa-dark: #0d1b2a;
    --fifa-red: #c0392b;
    --card-bg: #1e2d42;
    --card-border: #2e4166;
  }

  .stApp { background-color: #0d1b2a !important; }

  /* Hero banner */
  .hero-banner {
    background: linear-gradient(135deg, #0d1b2a 0%, #1a3a6e 50%, #0d1b2a 100%);
    border: 1px solid #c8a84b;
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    text-align: center;
    box-shadow: 0 4px 30px rgba(200,168,75,0.15);
  }
  .hero-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.5rem;
    letter-spacing: 4px;
    color: #c8a84b;
    margin: 0;
    line-height: 1;
  }
  .hero-sub {
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    color: #8ab4d4;
    margin-top: 6px;
    letter-spacing: 2px;
    text-transform: uppercase;
  }

  /* Tarjeta de partido */
  .match-card {
    background: linear-gradient(135deg, #1e2d42 0%, #243450 100%);
    border: 1px solid #2e4166;
    border-radius: 14px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: all 0.2s ease;
    box-shadow: 0 2px 12px rgba(0,0,0,0.3);
  }
  .match-card:hover {
    border-color: #c8a84b;
    box-shadow: 0 4px 20px rgba(200,168,75,0.2);
    transform: translateY(-1px);
  }
  .match-card.live {
    border-color: #27ae60;
    box-shadow: 0 0 15px rgba(39,174,96,0.3);
    animation: pulse-border 2s infinite;
  }
  @keyframes pulse-border {
    0%, 100% { box-shadow: 0 0 15px rgba(39,174,96,0.3); }
    50%       { box-shadow: 0 0 25px rgba(39,174,96,0.5); }
  }

  .match-teams {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-family: 'Inter', sans-serif;
    font-weight: 700;
    font-size: 1.15rem;
    color: #e8f0fe;
  }
  .team-name { flex: 1; display: flex; align-items: center; gap: 8px; }
  .team-name.home { justify-content: flex-end; text-align: right; }
  .team-name.away { justify-content: flex-start; text-align: left; }

  .score-box {
    background: #0d1b2a;
    border: 1px solid #2e4166;
    border-radius: 8px;
    padding: 6px 18px;
    font-size: 1.6rem;
    font-family: 'Bebas Neue', sans-serif;
    color: #c8a84b;
    letter-spacing: 4px;
    min-width: 90px;
    text-align: center;
    margin: 0 12px;
  }
  .score-box.live { border-color: #27ae60; color: #2ecc71; }

  .match-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 10px;
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
  }
  .match-time { color: #8ab4d4; }
  .match-venue { color: #5d7a9a; }

  .stage-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.8rem;
    letter-spacing: 3px;
    color: #c8a84b;
    border-bottom: 2px solid #c8a84b33;
    padding-bottom: 6px;
    margin: 28px 0 16px 0;
  }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background-color: #111f33 !important;
    border-right: 1px solid #2e4166;
  }
  section[data-testid="stSidebar"] .stMarkdown p,
  section[data-testid="stSidebar"] label {
    color: #8ab4d4 !important;
  }

  /* Live badge */
  .live-badge {
    display: inline-block;
    background: #27ae60;
    color: white;
    font-family: 'Inter', sans-serif;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 2px 8px;
    border-radius: 20px;
    animation: blink 1.5s infinite;
  }
  @keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.5; }
  }

  .team-logo { width: 26px; height: 26px; vertical-align: middle; object-fit: contain; }

  div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1e2d42, #243450);
    border: 1px solid #2e4166;
    border-radius: 10px;
    padding: 12px !important;
  }
  div[data-testid="stMetric"] label { color: #8ab4d4 !important; }
  div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #c8a84b !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 2rem !important;
  }

  hr { border-color: #2e4166 !important; }
  h1, h2, h3 { color: #e8f0fe !important; }
  p, li { color: #8ab4d4 !important; }

  .stButton > button {
    background: linear-gradient(135deg, #1a3a6e, #2e5090) !important;
    border: 1px solid #c8a84b !important;
    color: #c8a84b !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
  }
  .stButton > button:hover {
    background: linear-gradient(135deg, #c8a84b, #e6c96a) !important;
    color: #0d1b2a !important;
  }
</style>
""", unsafe_allow_html=True)


# ─── Funciones de API (ESPN) ───────────────────────────────────────────────────

@st.cache_data(ttl=60)
def fetch_espn(date_range: str) -> dict | None:
    """Consulta el scoreboard de ESPN para el rango de fechas dado (YYYYMMDD-YYYYMMDD)."""
    try:
        r = requests.get(
            ESPN_URL,
            params={"dates": date_range},
            headers={"User-Agent": "Mozilla/5.0 (MonitorMundial2026)"},
            timeout=15,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Sin conexión a ESPN. Verificá tu internet.")
    except Exception as e:
        st.error(f"Error consultando ESPN: {e}")
    return None


def utc_to_art(dt_str: str) -> datetime | None:
    """Convierte string ISO UTC (ej '2026-06-28T19:00Z') a datetime en ART."""
    if not dt_str:
        return None
    try:
        s = dt_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(ART)
    except Exception:
        return None


def format_art_time(dt: datetime | None) -> str:
    if dt is None:
        return "Horario a confirmar"
    dias = {0: "Lun", 1: "Mar", 2: "Mié", 3: "Jue", 4: "Vie", 5: "Sáb", 6: "Dom"}
    return f"{dias[dt.weekday()]} {dt.strftime('%d/%m · %H:%M')} ART"


# ─── Transformador de datos ───────────────────────────────────────────────────

def parse_espn(data: dict) -> list[dict]:
    """Normaliza los eventos de ESPN al formato interno (solo playoffs)."""
    matches = []
    if not data or "events" not in data:
        return matches

    for ev in data["events"]:
        comps = ev.get("competitions", [])
        if not comps:
            continue
        comp = comps[0]

        # Etapa: priorizar altGameNote, luego season.slug
        stage_text = comp.get("altGameNote") or ev.get("season", {}).get("slug", "")
        stage = normalize_stage(stage_text)
        if not stage:  # no es fase eliminatoria
            continue

        # Equipos
        competitors = comp.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), {})
        away = next((c for c in competitors if c.get("homeAway") == "away"), {})

        home_team = home.get("team", {})
        away_team = away.get("team", {})

        def score_val(c):
            s = c.get("score")
            try:
                return int(s) if s not in (None, "") else None
            except (ValueError, TypeError):
                return None

        # Estado
        status = comp.get("status", ev.get("status", {}))
        stype = status.get("type", {})
        state = stype.get("state", "pre")        # pre / in / post
        detail = stype.get("shortDetail", "")
        completed = stype.get("completed", False)

        is_live = state == "in"
        if state == "pre":
            status_label, status_color = "⏳ Por jugar", "#4a90e2"
            home_score = away_score = None
        elif is_live:
            status_label = f"🟢 {detail}" if detail else "🟢 En vivo"
            status_color = "#27ae60"
            home_score = score_val(home)
            away_score = score_val(away)
        else:  # post
            status_label, status_color = "✅ Finalizado", "#7f8c8d"
            home_score = score_val(home)
            away_score = score_val(away)

        venue = comp.get("venue", {})
        city = venue.get("address", {}).get("city", "")

        matches.append({
            "id": ev.get("id"),
            "stage": stage,
            "stage_label": STAGE_LABELS.get(stage, stage),
            "home_team": home_team.get("displayName", "Por definir"),
            "away_team": away_team.get("displayName", "Por definir"),
            "home_logo": home_team.get("logo", ""),
            "away_logo": away_team.get("logo", ""),
            "home_score": home_score,
            "away_score": away_score,
            "datetime_art": utc_to_art(ev.get("date", "")),
            "venue": venue.get("fullName", ""),
            "city": city,
            "state": state,
            "status_label": status_label,
            "status_color": status_color,
            "is_live": is_live,
            "completed": completed,
        })

    matches.sort(key=lambda x: (
        STAGE_ORDER.get(x["stage"], 99),
        x["datetime_art"] or datetime.max.replace(tzinfo=ART),
    ))
    return matches


# ─── Componentes visuales ─────────────────────────────────────────────────────

def logo_html(url: str) -> str:
    if url:
        return f'<img src="{url}" class="team-logo" onerror="this.style.display=\'none\'">'
    return "🏳️"


def render_match_card(m: dict):
    live_class = "live" if m["is_live"] else ""
    h, a = m["home_team"], m["away_team"]

    if m["home_score"] is not None or m["away_score"] is not None:
        hs = m["home_score"] if m["home_score"] is not None else 0
        as_ = m["away_score"] if m["away_score"] is not None else 0
        score_text = f"{hs} - {as_}"
    else:
        score_text = "vs"

    score_class = "live" if m["is_live"] else ""
    live_badge = '<span class="live-badge">EN VIVO</span>' if m["is_live"] else ""
    venue_text = f"📍 {m['venue']}" + (f", {m['city']}" if m["city"] else "") if m["venue"] else ""
    status_html = f'<span style="color:{m["status_color"]};font-weight:600">{m["status_label"]}</span>'

    st.markdown(f"""
    <div class="match-card {live_class}">
      <div class="match-teams">
        <div class="team-name home">{h} {logo_html(m["home_logo"])}</div>
        <div class="score-box {score_class}">{score_text}</div>
        <div class="team-name away">{logo_html(m["away_logo"])} {a}</div>
      </div>
      <div class="match-meta">
        <span class="match-time">🕐 {format_art_time(m["datetime_art"])}</span>
        <span>{live_badge} {status_html}</span>
        <span class="match-venue">{venue_text}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_stats(matches: list[dict]):
    total = len(matches)
    live = sum(1 for m in matches if m["is_live"])
    finished = sum(1 for m in matches if m["state"] == "post")
    pending = sum(1 for m in matches if m["state"] == "pre")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Partidos", total)
    c2.metric("🟢 En Vivo", live)
    c3.metric("✅ Finalizados", finished)
    c4.metric("⏳ Por Jugar", pending)


def render_table(matches: list[dict]):
    rows = []
    for m in matches:
        if m["state"] == "pre":
            resultado = "Por jugar"
        else:
            hs = m["home_score"] if m["home_score"] is not None else "-"
            as_ = m["away_score"] if m["away_score"] is not None else "-"
            resultado = f"{hs} - {as_}"
        ganador = ""
        if m["state"] == "post" and m["home_score"] is not None and m["away_score"] is not None:
            if m["home_score"] > m["away_score"]:
                ganador = m["home_team"]
            elif m["away_score"] > m["home_score"]:
                ganador = m["away_team"]
            else:
                ganador = "Empate / Penales"
        rows.append({
            "Etapa": m["stage_label"],
            "Local": m["home_team"],
            "Resultado": resultado,
            "Visitante": m["away_team"],
            "Ganador": ganador,
            "Fecha ART": format_art_time(m["datetime_art"]),
            "Estadio": m["venue"] or "—",
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


# ─── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 20px">
      <div style="font-family:'Bebas Neue',sans-serif; font-size:1.6rem; color:#c8a84b; letter-spacing:3px">
        ⚙️ CONFIGURACIÓN
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#0d2818;border:1px solid #27ae6044;border-radius:8px;
         padding:10px;font-family:Inter,sans-serif;font-size:0.78rem;color:#2ecc71">
      ✅ Fuente: <strong>ESPN API</strong><br>
      <span style="color:#5d7a9a">Gratuita · sin API key · sin límites</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    auto_refresh = st.toggle("🔄 Auto-actualizar (60s)", value=False)

    stage_filter = st.multiselect(
        "Filtrar etapas",
        options=list(STAGE_LABELS.values()),
        default=list(STAGE_LABELS.values()),
    )

    view_mode = st.radio("Vista", ["🃏 Tarjetas", "📊 Tabla", "🏆 Ambas"], index=2)

    st.divider()
    st.markdown("""
    <div style="font-family:Inter,sans-serif; font-size:0.7rem; color:#3d5a7a; text-align:center">
      Mundial 2026 · USA / CAN / MEX<br>
      11 Jun – 19 Jul 2026<br>
      Horarios en ART (UTC-3)
    </div>
    """, unsafe_allow_html=True)


# ─── Header principal ──────────────────────────────────────────────────────────

now_art = datetime.now(ART)
meses = {1:"Enero",2:"Febrero",3:"Marzo",4:"Abril",5:"Mayo",6:"Junio",
         7:"Julio",8:"Agosto",9:"Septiembre",10:"Octubre",11:"Noviembre",12:"Diciembre"}
fecha_hdr = f"{now_art.day} de {meses[now_art.month]} {now_art.year} · {now_art.strftime('%H:%M')} ART"

st.markdown(f"""
<div class="hero-banner">
  <div class="hero-title">🏆 MUNDIAL 2026 · PLAYOFFS 🏆</div>
  <div class="hero-sub">Fase Eliminatoria · USA / Canadá / México · {fecha_hdr}</div>
</div>
""", unsafe_allow_html=True)


# ─── Botón de refresco ────────────────────────────────────────────────────────

col_a, col_b = st.columns([1, 4])
with col_a:
    if st.button("🔄 Actualizar datos"):
        st.cache_data.clear()
        st.rerun()


# ─── Carga de datos ───────────────────────────────────────────────────────────

with st.spinner("Cargando partidos del Mundial desde ESPN..."):
    data = fetch_espn(f"{PLAYOFF_START}-{PLAYOFF_END}")
    matches_raw = parse_espn(data) if data else []

if not matches_raw:
    st.warning(
        "Todavía no hay partidos de playoffs disponibles. "
        "La fase eliminatoria arranca el 28 de junio de 2026. "
        "Si ya empezó y no ves datos, probá 🔄 Actualizar."
    )

# Filtrar etapas
filtered = [m for m in matches_raw if m["stage_label"] in stage_filter]

# Stats
if filtered:
    render_stats(filtered)
    st.markdown("<br>", unsafe_allow_html=True)

# Partidos en vivo destacados
live_matches = [m for m in filtered if m["is_live"]]
if live_matches:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
      <span class="live-badge">EN VIVO</span>
      <span style="font-family:'Bebas Neue',sans-serif;font-size:1.4rem;color:#2ecc71;letter-spacing:2px">
        PARTIDOS EN CURSO
      </span>
    </div>
    """, unsafe_allow_html=True)
    for m in live_matches:
        render_match_card(m)
    st.divider()

# Vista tabla / tarjetas
show_cards = view_mode in ("🃏 Tarjetas", "🏆 Ambas")
show_table = view_mode in ("📊 Tabla", "🏆 Ambas")

if show_table and filtered:
    st.markdown('<div class="stage-header">📊 TABLA COMPLETA DE PLAYOFFS</div>', unsafe_allow_html=True)
    render_table(filtered)
    st.markdown("<br>", unsafe_allow_html=True)

if show_cards:
    non_live = [m for m in filtered if not m["is_live"]]
    stages_present = sorted(set(m["stage"] for m in non_live), key=lambda s: STAGE_ORDER.get(s, 99))
    for stage in stages_present:
        stage_matches = [m for m in non_live if m["stage"] == stage]
        if not stage_matches:
            continue
        emoji = EMOJI_STAGES.get(stage, "⚽")
        label = STAGE_LABELS.get(stage, stage)
        st.markdown(f'<div class="stage-header">{emoji} {label.upper()}</div>', unsafe_allow_html=True)
        for m in stage_matches:
            render_match_card(m)


# ─── Footer ───────────────────────────────────────────────────────────────────

st.divider()
st.markdown(f"""
<div style="text-align:center;font-family:Inter,sans-serif;font-size:0.72rem;color:#3d5a7a;padding:10px">
  Datos: ESPN API (pública) · Última actualización: {now_art.strftime('%H:%M:%S ART')} ·
  Horarios en Argentina (UTC-3)
</div>
""", unsafe_allow_html=True)


# ─── Auto-refresh ─────────────────────────────────────────────────────────────

if auto_refresh:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()
