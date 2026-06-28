"""
Monitor Mundial 2026 — Playoffs en vivo
Consume la API de balldontlie.io / worldcupapi.com
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

STATUS_MAP = {
    "NS": ("⏳ Por jugar", "#4a90e2"),
    "1H": ("🟢 1er Tiempo", "#27ae60"),
    "HT": ("🟡 Descanso", "#f39c12"),
    "2H": ("🟢 2do Tiempo", "#27ae60"),
    "ET": ("🟢 Prórroga", "#8e44ad"),
    "P": ("🟢 Penales", "#e74c3c"),
    "FT": ("✅ Finalizado", "#7f8c8d"),
    "AET": ("✅ Fin Prórroga", "#7f8c8d"),
    "PEN": ("✅ Fin Penales", "#7f8c8d"),
}

FLAG_BASE = "https://flagcdn.com/w40"
FLAGS = {
    "Argentina": "ar", "Brazil": "br", "France": "fr", "Germany": "de",
    "Spain": "es", "England": "gb-eng", "Portugal": "pt", "Netherlands": "nl",
    "Morocco": "ma", "Japan": "jp", "USA": "us", "Mexico": "mx",
    "Canada": "ca", "Uruguay": "uy", "Colombia": "co", "Ecuador": "ec",
    "Chile": "cl", "Peru": "pe", "Australia": "au", "South Korea": "kr",
    "Saudi Arabia": "sa", "Senegal": "sn", "Cameroon": "cm", "Nigeria": "ng",
    "Ghana": "gh", "Croatia": "hr", "Belgium": "be", "Poland": "pl",
    "Switzerland": "ch", "Denmark": "dk", "Sweden": "se", "Austria": "at",
    "Italy": "it", "Turkey": "tr", "Serbia": "rs", "Ukraine": "ua",
    "Czech Republic": "cz", "Hungary": "hu", "Slovenia": "si", "Romania": "ro",
    "Iran": "ir", "Qatar": "qa", "Paraguay": "py", "Bolivia": "bo",
    "Venezuela": "ve", "Panama": "pa", "Costa Rica": "cr", "Honduras": "hn",
    "El Salvador": "sv", "Jamaica": "jm", "New Zealand": "nz", "China": "cn",
    "Indonesia": "id", "Vietnam": "vn", "Iraq": "iq", "Jordan": "jo",
    "United Arab Emirates": "ae", "Algeria": "dz", "Egypt": "eg",
    "Tunisia": "tn", "South Africa": "za", "Ivory Coast": "ci",
    "Congo DR": "cd", "Mali": "ml", "United States": "us",
    "Korea Republic": "kr",
}

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
    font-size: 1.2rem;
    color: #e8f0fe;
  }
  .team-name { flex: 1; }
  .team-name.home { text-align: right; }
  .team-name.away { text-align: left; }

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
  .match-status { font-weight: 600; }

  .stage-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.8rem;
    letter-spacing: 3px;
    color: #c8a84b;
    border-bottom: 2px solid #c8a84b33;
    padding-bottom: 6px;
    margin: 28px 0 16px 0;
  }

  /* Stats cards */
  .stat-card {
    background: linear-gradient(135deg, #1e2d42, #243450);
    border: 1px solid #2e4166;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
  }
  .stat-number {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.8rem;
    color: #c8a84b;
    line-height: 1;
  }
  .stat-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.75rem;
    color: #8ab4d4;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 4px;
  }

  /* Sidebar */
  .css-1d391kg { background-color: #0d1b2a !important; }
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

  .flag-img { width: 28px; vertical-align: middle; margin: 0 6px; }

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

  .info-chip {
    display: inline-block;
    background: #1a3a6e;
    border: 1px solid #2e5090;
    color: #8ab4d4;
    font-size: 0.72rem;
    padding: 3px 10px;
    border-radius: 20px;
    margin: 2px;
    font-family: 'Inter', sans-serif;
  }
  .gold-chip {
    background: #2a2000;
    border: 1px solid #c8a84b44;
    color: #c8a84b;
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
  .stSelectbox > div > div {
    background-color: #1e2d42 !important;
    border-color: #2e4166 !important;
    color: #e8f0fe !important;
  }
</style>
""", unsafe_allow_html=True)


# ─── Funciones de API ──────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def fetch_balldontlie(endpoint: str, api_key: str, params: dict = None) -> dict | None:
    """Consulta la API de balldontlie.io para FIFA World Cup."""
    base = "https://api.balldontlie.io/fifa/worldcup/v1"
    headers = {"Authorization": api_key}
    try:
        r = requests.get(f"{base}/{endpoint}", headers=headers, params=params or {}, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            st.error("❌ API Key inválida. Verificá tu clave de balldontlie.io")
        elif e.response.status_code == 429:
            st.warning("⚠️ Límite de requests alcanzado. Esperá un momento.")
        else:
            st.error(f"Error API: {e.response.status_code}")
    except Exception as e:
        st.error(f"Error de conexión: {e}")
    return None


@st.cache_data(ttl=60)
def fetch_worldcupapi(endpoint: str, api_key: str) -> dict | None:
    """Consulta la API de worldcupapi.com."""
    base = "https://worldcupapi.com/api"
    headers = {"x-rapidapi-key": api_key, "Accept": "application/json"}
    try:
        r = requests.get(f"{base}/{endpoint}", headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Error worldcupapi: {e}")
    return None


def utc_to_art(dt_str: str) -> datetime | None:
    """Convierte string ISO UTC a datetime en ART (UTC-3)."""
    if not dt_str:
        return None
    try:
        # Intentar varios formatos
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S+00:00",
                    "%Y-%m-%dT%H:%M:%S.000Z", "%Y-%m-%d %H:%M:%S"):
            try:
                dt = datetime.strptime(dt_str.replace("+00:00", "Z").rstrip("Z"), fmt.rstrip("Z"))
                dt = dt.replace(tzinfo=UTC)
                return dt.astimezone(ART)
            except ValueError:
                continue
    except Exception:
        pass
    return None


def format_art_time(dt: datetime | None) -> str:
    if dt is None:
        return "Horario a confirmar"
    return dt.strftime("%a %d/%m · %H:%M ART")


def get_flag_url(team_name: str) -> str:
    code = FLAGS.get(team_name, "")
    if code:
        return f"{FLAG_BASE}/{code}.png"
    return ""


def flag_html(team_name: str) -> str:
    url = get_flag_url(team_name)
    if url:
        return f'<img src="{url}" class="flag-img" onerror="this.style.display=\'none\'">'
    return "🏳️"


# ─── Transformadores de datos ─────────────────────────────────────────────────

def parse_balldontlie_matches(data: dict) -> list[dict]:
    """Normaliza partidos de balldontlie al formato interno."""
    matches = []
    if not data or "data" not in data:
        return matches
    for m in data["data"]:
        stage_raw = m.get("round", {}).get("name", "") if isinstance(m.get("round"), dict) else m.get("round", "")
        # Filtrar sólo fases eliminatorias
        knockout_keywords = ["Round of 32", "Round of 16", "Quarter", "Semi", "Final", "Third"]
        if not any(k.lower() in stage_raw.lower() for k in knockout_keywords):
            continue

        home = m.get("home_team", {})
        away = m.get("away_team", {})
        score = m.get("score", {})
        status_raw = m.get("status", "NS")

        dt_art = utc_to_art(m.get("date") or m.get("datetime") or "")
        status_label, status_color = STATUS_MAP.get(status_raw, ("⏳ Por jugar", "#4a90e2"))

        home_score = score.get("home") if score else None
        away_score = score.get("away") if score else None

        # Resolver nombre de etapa
        stage = stage_raw
        for k in STAGE_ORDER:
            if k.lower() in stage_raw.lower():
                stage = k
                break

        matches.append({
            "id": m.get("id"),
            "stage": stage,
            "stage_label": STAGE_LABELS.get(stage, stage),
            "home_team": home.get("name", home.get("full_name", "?")) if isinstance(home, dict) else str(home),
            "away_team": away.get("name", away.get("full_name", "?")) if isinstance(away, dict) else str(away),
            "home_score": home_score,
            "away_score": away_score,
            "datetime_art": dt_art,
            "venue": m.get("venue", {}).get("name", "") if isinstance(m.get("venue"), dict) else m.get("venue", ""),
            "city": m.get("venue", {}).get("city", "") if isinstance(m.get("venue"), dict) else "",
            "status": status_raw,
            "status_label": status_label,
            "status_color": status_color,
            "is_live": status_raw in ("1H", "HT", "2H", "ET", "P"),
        })

    matches.sort(key=lambda x: (
        STAGE_ORDER.get(x["stage"], 99),
        x["datetime_art"] or datetime.max.replace(tzinfo=ART)
    ))
    return matches


# ─── Componentes visuales ─────────────────────────────────────────────────────

def render_match_card(match: dict):
    live_class = "live" if match["is_live"] else ""
    home = match["home_team"]
    away = match["away_team"]

    h_score = match["home_score"] if match["home_score"] is not None else ""
    a_score = match["away_score"] if match["away_score"] is not None else ""
    score_text = f"{h_score} - {a_score}" if (h_score != "" or a_score != "") else "vs"

    score_class = "live" if match["is_live"] else ""
    live_badge = '<span class="live-badge">EN VIVO</span>' if match["is_live"] else ""

    venue_text = f"📍 {match['venue']}" + (f", {match['city']}" if match["city"] else "") if match["venue"] else ""
    time_text = format_art_time(match["datetime_art"])

    status_html = f'<span style="color:{match["status_color"]};font-weight:600">{match["status_label"]}</span>'

    st.markdown(f"""
    <div class="match-card {live_class}">
      <div class="match-teams">
        <div class="team-name home">
          {flag_html(home)} {home}
        </div>
        <div class="score-box {score_class}">{score_text}</div>
        <div class="team-name away">
          {away} {flag_html(away)}
        </div>
      </div>
      <div class="match-meta">
        <span class="match-time">🕐 {time_text}</span>
        <span>{live_badge} {status_html}</span>
        <span class="match-venue">{venue_text}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_stats(matches: list[dict]):
    total = len(matches)
    live = sum(1 for m in matches if m["is_live"])
    finished = sum(1 for m in matches if m["status"] in ("FT", "AET", "PEN"))
    pending = sum(1 for m in matches if m["status"] == "NS")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Partidos", total)
    with c2:
        st.metric("🟢 En Vivo", live)
    with c3:
        st.metric("✅ Finalizados", finished)
    with c4:
        st.metric("⏳ Por Jugar", pending)


def render_bracket_table(matches: list[dict]):
    """Tabla visual del bracket en formato DataFrame."""
    rows = []
    for m in matches:
        h_score = m["home_score"] if m["home_score"] is not None else "-"
        a_score = m["away_score"] if m["away_score"] is not None else "-"
        resultado = f"{h_score} - {a_score}" if m["status"] != "NS" else "Por jugar"
        ganador = ""
        if m["status"] in ("FT", "AET", "PEN"):
            if m["home_score"] is not None and m["away_score"] is not None:
                if m["home_score"] > m["away_score"]:
                    ganador = m["home_team"]
                elif m["away_score"] > m["home_score"]:
                    ganador = m["away_team"]
                else:
                    ganador = "Penales"

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
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Etapa": st.column_config.TextColumn(width="medium"),
                "Local": st.column_config.TextColumn(width="medium"),
                "Resultado": st.column_config.TextColumn(width="small"),
                "Visitante": st.column_config.TextColumn(width="medium"),
                "Ganador": st.column_config.TextColumn(width="medium"),
                "Fecha ART": st.column_config.TextColumn(width="large"),
                "Estadio": st.column_config.TextColumn(width="large"),
            }
        )


# ─── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 20px">
      <div style="font-family:'Bebas Neue',sans-serif; font-size:1.6rem; color:#c8a84b; letter-spacing:3px">
        ⚙️ CONFIGURACIÓN
      </div>
    </div>
    """, unsafe_allow_html=True)

    api_source = st.selectbox(
        "Fuente de datos",
        ["balldontlie.io", "worldcupapi.com"],
        help="Seleccioná el proveedor de API"
    )

    if api_source == "balldontlie.io":
        api_key = st.text_input(
            "API Key (balldontlie.io)",
            type="password",
            placeholder="Ingresá tu API key",
            help="Registrate gratis en balldontlie.io para obtener tu key"
        )
        st.markdown("""
        <div style="font-family:Inter,sans-serif; font-size:0.72rem; color:#5d7a9a; margin-top:4px">
          🔗 Registrate gratis en <a href="https://www.balldontlie.io" target="_blank" style="color:#4a90e2">balldontlie.io</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        api_key = st.text_input(
            "API Key (worldcupapi.com)",
            type="password",
            placeholder="Ingresá tu API key",
            help="Registrate en worldcupapi.com"
        )
        st.markdown("""
        <div style="font-family:Inter,sans-serif; font-size:0.72rem; color:#5d7a9a; margin-top:4px">
          🔗 Registrate en <a href="https://worldcupapi.com" target="_blank" style="color:#4a90e2">worldcupapi.com</a>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    auto_refresh = st.toggle("🔄 Auto-actualizar (60s)", value=False)
    stage_filter = st.multiselect(
        "Filtrar etapas",
        options=list(STAGE_LABELS.values()),
        default=list(STAGE_LABELS.values()),
        help="Seleccioná las etapas a mostrar"
    )

    view_mode = st.radio(
        "Vista",
        ["🃏 Tarjetas", "📊 Tabla", "🏆 Ambas"],
        index=2
    )

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
st.markdown(f"""
<div class="hero-banner">
  <div class="hero-title">🏆 MUNDIAL 2026 · PLAYOFFS 🏆</div>
  <div class="hero-sub">
    Fase Eliminatoria · USA / Canadá / México ·
    {now_art.strftime('%d de %B %Y · %H:%M ART')}
  </div>
</div>
""", unsafe_allow_html=True)


# ─── Botón de refresco ────────────────────────────────────────────────────────

col_refresh, col_info = st.columns([1, 4])
with col_refresh:
    refresh = st.button("🔄 Actualizar datos")
with col_info:
    if not api_key:
        st.info("👈 Ingresá tu API key en la barra lateral para cargar datos en vivo.")


# ─── Carga de datos ───────────────────────────────────────────────────────────

matches_raw = []

if api_key:
    if refresh:
        st.cache_data.clear()

    with st.spinner("Cargando partidos del Mundial..."):
        if api_source == "balldontlie.io":
            # Traemos todos los partidos de la edición 2026
            data = fetch_balldontlie("matches", api_key, {"seasons[]": "2026", "per_page": 200})
            if data:
                matches_raw = parse_balldontlie_matches(data)

                # Si hay paginación, traer resto
                meta = data.get("meta", {})
                total_pages = meta.get("total_pages", 1)
                if total_pages and int(total_pages) > 1:
                    for page in range(2, int(total_pages) + 1):
                        extra = fetch_balldontlie("matches", api_key,
                            {"seasons[]": "2026", "per_page": 200, "page": page})
                        if extra:
                            matches_raw += parse_balldontlie_matches(extra)

        else:  # worldcupapi.com
            data = fetch_worldcupapi("matches?stage=knockout", api_key)
            if data:
                # worldcupapi retorna lista directa o {data: [...]}
                raw_list = data if isinstance(data, list) else data.get("data", [])
                for m in raw_list:
                    stage_raw = m.get("stage_name", m.get("round", ""))
                    knockout_kws = ["Round of 32", "Round of 16", "Quarter", "Semi", "Final", "Third"]
                    if not any(k.lower() in stage_raw.lower() for k in knockout_kws):
                        continue
                    status_raw = m.get("status", "NS")
                    status_label, status_color = STATUS_MAP.get(status_raw, ("⏳ Por jugar", "#4a90e2"))
                    stage = stage_raw
                    for k in STAGE_ORDER:
                        if k.lower() in stage_raw.lower():
                            stage = k
                            break
                    dt_art = utc_to_art(m.get("utc_date") or m.get("date") or "")
                    matches_raw.append({
                        "id": m.get("id"),
                        "stage": stage,
                        "stage_label": STAGE_LABELS.get(stage, stage),
                        "home_team": m.get("home_team", {}).get("name", "?") if isinstance(m.get("home_team"), dict) else str(m.get("home_team", "?")),
                        "away_team": m.get("away_team", {}).get("name", "?") if isinstance(m.get("away_team"), dict) else str(m.get("away_team", "?")),
                        "home_score": m.get("score", {}).get("home") if isinstance(m.get("score"), dict) else None,
                        "away_score": m.get("score", {}).get("away") if isinstance(m.get("score"), dict) else None,
                        "datetime_art": dt_art,
                        "venue": m.get("stadium", m.get("venue", "")),
                        "city": m.get("city", ""),
                        "status": status_raw,
                        "status_label": status_label,
                        "status_color": status_color,
                        "is_live": status_raw in ("1H", "HT", "2H", "ET", "P"),
                    })

    if not matches_raw:
        st.warning("No se encontraron partidos de playoffs. Verificá tu API key o intentá más tarde.")
else:
    # Modo demo sin API key
    st.markdown("""
    <div style="background:linear-gradient(135deg,#1a2035,#1e2d42);border:1px dashed #2e4166;
         border-radius:12px;padding:20px;text-align:center;font-family:Inter,sans-serif">
      <div style="font-size:2rem">⚽</div>
      <div style="color:#c8a84b;font-size:1rem;font-weight:600;margin:8px 0">
        Modo Demo — Sin conexión a API
      </div>
      <div style="color:#5d7a9a;font-size:0.85rem">
        Ingresá tu API key en la barra lateral para ver datos en vivo.<br>
        La app soporta <strong style="color:#8ab4d4">balldontlie.io</strong> y
        <strong style="color:#8ab4d4">worldcupapi.com</strong>
      </div>
    </div>
    """, unsafe_allow_html=True)
    # Demo data para visualizar el diseño
    from datetime import timedelta
    now = datetime.now(ART)
    matches_raw = [
        {"id": 1, "stage": "Semi-finals", "stage_label": "Semifinales",
         "home_team": "Argentina", "away_team": "Spain",
         "home_score": 2, "away_score": 1,
         "datetime_art": now - timedelta(hours=3),
         "venue": "MetLife Stadium", "city": "Nueva York",
         "status": "FT", "status_label": "✅ Finalizado", "status_color": "#7f8c8d", "is_live": False},
        {"id": 2, "stage": "Semi-finals", "stage_label": "Semifinales",
         "home_team": "France", "away_team": "Brazil",
         "home_score": 1, "away_score": 1,
         "datetime_art": now + timedelta(hours=2),
         "venue": "Rose Bowl", "city": "Los Ángeles",
         "status": "1H", "status_label": "🟢 1er Tiempo", "status_color": "#27ae60", "is_live": True},
        {"id": 3, "stage": "Final", "stage_label": "Final",
         "home_team": "Argentina", "away_team": "Por definir",
         "home_score": None, "away_score": None,
         "datetime_art": now + timedelta(days=4, hours=5),
         "venue": "MetLife Stadium", "city": "Nueva York",
         "status": "NS", "status_label": "⏳ Por jugar", "status_color": "#4a90e2", "is_live": False},
        {"id": 4, "stage": "Quarter-finals", "stage_label": "Cuartos de Final",
         "home_team": "Germany", "away_team": "Netherlands",
         "home_score": 3, "away_score": 2,
         "datetime_art": now - timedelta(days=2),
         "venue": "AT&T Stadium", "city": "Dallas",
         "status": "FT", "status_label": "✅ Finalizado", "status_color": "#7f8c8d", "is_live": False},
        {"id": 5, "stage": "Quarter-finals", "stage_label": "Cuartos de Final",
         "home_team": "Morocco", "away_team": "England",
         "home_score": 1, "away_score": 0,
         "datetime_art": now - timedelta(days=2, hours=4),
         "venue": "Levi's Stadium", "city": "San Francisco",
         "status": "FT", "status_label": "✅ Finalizado", "status_color": "#7f8c8d", "is_live": False},
        {"id": 6, "stage": "Third-place playoff", "stage_label": "3er y 4to Puesto",
         "home_team": "Spain", "away_team": "Brazil",
         "home_score": None, "away_score": None,
         "datetime_art": now + timedelta(days=3),
         "venue": "Hard Rock Stadium", "city": "Miami",
         "status": "NS", "status_label": "⏳ Por jugar", "status_color": "#4a90e2", "is_live": False},
    ]


# ─── Filtrar etapas ───────────────────────────────────────────────────────────

filtered = [m for m in matches_raw if m["stage_label"] in stage_filter]


# ─── Estadísticas globales ────────────────────────────────────────────────────

if filtered:
    render_stats(filtered)
    st.markdown("<br>", unsafe_allow_html=True)


# ─── Partido en vivo destacado ────────────────────────────────────────────────

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


# ─── Partidos por etapa ───────────────────────────────────────────────────────

non_live = [m for m in filtered if not m["is_live"]]

# Agrupar por etapa
stages_present = sorted(
    set(m["stage"] for m in non_live),
    key=lambda s: STAGE_ORDER.get(s, 99)
)

show_cards = view_mode in ("🃏 Tarjetas", "🏆 Ambas")
show_table = view_mode in ("📊 Tabla", "🏆 Ambas")

if show_table and filtered:
    st.markdown('<div class="stage-header">📊 TABLA COMPLETA DE PLAYOFFS</div>', unsafe_allow_html=True)
    render_bracket_table(filtered)
    st.markdown("<br>", unsafe_allow_html=True)

if show_cards:
    for stage in stages_present:
        stage_matches = [m for m in non_live if m["stage"] == stage]
        if not stage_matches:
            continue
        emoji = EMOJI_STAGES.get(stage, "⚽")
        label = STAGE_LABELS.get(stage, stage)
        st.markdown(
            f'<div class="stage-header">{emoji} {label.upper()}</div>',
            unsafe_allow_html=True
        )
        for m in stage_matches:
            render_match_card(m)


# ─── Footer ───────────────────────────────────────────────────────────────────

st.divider()
st.markdown(f"""
<div style="text-align:center;font-family:Inter,sans-serif;font-size:0.72rem;color:#3d5a7a;padding:10px">
  Datos provistos por balldontlie.io / worldcupapi.com ·
  Última actualización: {now_art.strftime('%H:%M:%S ART')} ·
  Horarios en Argentina (UTC-3)
</div>
""", unsafe_allow_html=True)


# ─── Auto-refresh ─────────────────────────────────────────────────────────────

if auto_refresh and api_key:
    time.sleep(60)
    st.rerun()
