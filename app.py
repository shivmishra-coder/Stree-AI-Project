import streamlit as st
from llm_handler import LLMHandler
import base64, os, json, re, datetime

try:
    import pandas as pd
    _PANDAS = True
except ImportError:
    _PANDAS = False

try:
    from streamlit_mic_recorder import speech_to_text
    MIC_OK = True
except ImportError:
    MIC_OK = False

st.set_page_config(page_title="SHIV CORE | Laboratory", page_icon="🔱", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&display=swap');

:root {
    --cyan:   #00e5ff;
    --cyan-d: rgba(0, 229, 255, 0.18);
    --cyan-f: rgba(0, 229, 255, 0.06);
    --bg1:    #00050a;
    --bg2:    #001220;
    --glass:  rgba(0, 18, 32, 0.55);
    --red:    #ff2d55;
    --green:  #00ff88;
    --yellow: #ffd700;
}

*, *::before, *::after {
    font-family: 'JetBrains Mono', 'Courier New', monospace !important;
    box-sizing: border-box;
}

html, body, .stApp {
    background:
        radial-gradient(ellipse at 10% 10%, rgba(0,229,255,0.04) 0%, transparent 55%),
        radial-gradient(ellipse at 90% 80%, rgba(0,100,180,0.06) 0%, transparent 55%),
        linear-gradient(160deg, var(--bg1) 0%, #000b16 45%, var(--bg2) 100%) !important;
    color: var(--cyan) !important;
    min-height: 100vh;
}

section[data-testid="stSidebar"] {
    background:
        radial-gradient(ellipse at 50% 0%, rgba(0,229,255,0.05) 0%, transparent 60%),
        linear-gradient(180deg, #00040c 0%, #000e1c 100%) !important;
    border-right: 1px solid var(--cyan-d) !important;
    backdrop-filter: blur(12px);
}
section[data-testid="stSidebar"] * { color: var(--cyan) !important; }

.stChatMessage {
    background: var(--glass) !important;
    border: 1px solid var(--cyan-d) !important;
    border-radius: 14px !important;
    margin-bottom: 10px !important;
    backdrop-filter: blur(12px) saturate(1.4) !important;
    -webkit-backdrop-filter: blur(12px) saturate(1.4) !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(0,229,255,0.08) !important;
    transition: border-color 0.25s, box-shadow 0.25s;
}
.stChatMessage:hover {
    border-color: rgba(0,229,255,0.38) !important;
    box-shadow: 0 4px 32px rgba(0,229,255,0.1), inset 0 1px 0 rgba(0,229,255,0.12) !important;
}

.stChatInputContainer textarea {
    background: rgba(0, 14, 26, 0.7) !important;
    border: 1px solid var(--cyan-d) !important;
    color: var(--cyan) !important;
    border-radius: 10px !important;
    backdrop-filter: blur(8px) !important;
    caret-color: var(--cyan);
    transition: border-color 0.2s, box-shadow 0.2s;
}
.stChatInputContainer textarea:focus {
    border-color: var(--cyan) !important;
    box-shadow: 0 0 0 2px rgba(0,229,255,0.15), 0 0 20px rgba(0,229,255,0.1) !important;
    outline: none !important;
}

.stButton > button {
    width: 100%;
    border: 1px solid var(--cyan-d) !important;
    background: rgba(0,229,255,0.04) !important;
    color: var(--cyan) !important;
    letter-spacing: 1.5px;
    border-radius: 8px !important;
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    padding: 6px 10px !important;
    transition: all 0.18s ease;
}
.stButton > button:hover {
    background: rgba(0,229,255,0.12) !important;
    border-color: var(--cyan) !important;
    box-shadow: 0 0 18px rgba(0,229,255,0.3) !important;
    transform: translateY(-1px);
}
.stButton > button:active { transform: translateY(0); }

.stSelectbox > div > div {
    background: rgba(0,14,26,0.7) !important;
    border-color: var(--cyan-d) !important;
    color: var(--cyan) !important;
    border-radius: 8px !important;
}

.stSelectbox label, .stRadio label, .stToggle label,
.stFileUploader label, p, span {
    color: var(--cyan) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.8px !important;
}

.stRadio > div { gap: 5px !important; }
.stRadio > div > label {
    background: rgba(0,229,255,0.03) !important;
    border: 1px solid var(--cyan-d) !important;
    border-radius: 7px !important;
    padding: 5px 10px !important;
    transition: all 0.15s;
}
.stRadio > div > label:hover {
    background: rgba(0,229,255,0.08) !important;
    border-color: var(--cyan) !important;
}

.stSlider > div > div > div { background: var(--cyan) !important; }
.stSlider > div > div       { background: var(--cyan-d) !important; }

.avatar-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px 0 12px;
    position: relative;
}
.aura-ring {
    position: absolute; top: 10px;
    width: 185px; height: 185px;
    border-radius: 50%;
    border: 1px solid rgba(0,229,255,0.15);
    animation: breathe 4s ease-in-out infinite;
    pointer-events: none;
}
.aura-ring-2 {
    position: absolute; top: 18px;
    width: 169px; height: 169px;
    border-radius: 50%;
    border: 1px solid rgba(0,229,255,0.25);
    animation: breathe 4s ease-in-out infinite 0.6s;
    pointer-events: none;
}
.avatar-img {
    width: 155px; height: 155px;
    border-radius: 50%;
    border: 2px solid var(--cyan);
    box-shadow: 0 0 0 3px rgba(0,229,255,0.12), 0 0 30px rgba(0,229,255,0.5),
                0 0 60px rgba(0,229,255,0.2), inset 0 0 20px rgba(0,229,255,0.05);
    object-fit: cover;
    position: relative; z-index: 1;
    animation: core-glow 4s ease-in-out infinite;
}
@keyframes breathe {
    0%, 100% { transform: scale(1);   opacity: 0.5; }
    50%       { transform: scale(1.1); opacity: 1;   }
}
@keyframes core-glow {
    0%, 100% { box-shadow: 0 0 25px rgba(0,229,255,0.45), 0 0 50px rgba(0,229,255,0.15); }
    50%       { box-shadow: 0 0 50px rgba(0,229,255,0.75), 0 0 100px rgba(0,229,255,0.3); }
}

.avatar-name { margin-top: 14px; font-weight: 700; font-size: 1.05rem; letter-spacing: 4.5px; text-transform: uppercase; text-shadow: 0 0 16px var(--cyan), 0 0 32px rgba(0,229,255,0.4); }
.avatar-sub  { font-size: 0.58rem; opacity: 0.4; letter-spacing: 3px; margin-top: 3px; }
.avatar-stat { font-size: 0.56rem; letter-spacing: 2px; margin-top: 2px; color: var(--green) !important; }

.panel-title {
    font-size: 0.62rem; letter-spacing: 2.5px; opacity: 0.35;
    border-bottom: 1px solid var(--cyan-d); padding-bottom: 5px;
    margin: 10px 0 11px; text-transform: uppercase;
}
.kill-box {
    border: 1px solid var(--red) !important;
    background: rgba(255,45,85,0.07) !important;
    border-radius: 9px; padding: 9px 12px; margin: 5px 0 6px;
}
.kill-box * { color: var(--red) !important; font-size: 0.7rem !important; letter-spacing: 1px !important; }

.voice-box {
    border: 1px solid var(--cyan-d);
    background: rgba(0,229,255,0.025);
    border-radius: 9px; padding: 10px 12px; margin: 6px 0;
}

.file-badge {
    display: inline-flex; align-items: center; gap: 6px;
    border: 1px solid var(--cyan-d);
    background: rgba(0,229,255,0.05);
    border-radius: 7px; padding: 5px 10px;
    font-size: 0.65rem; letter-spacing: 1px;
    margin: 4px 0; color: var(--cyan);
}
.file-badge.image { border-color: rgba(255,215,0,0.3); background: rgba(255,215,0,0.05); color: var(--yellow) !important; }
.file-badge.code  { border-color: rgba(0,229,255,0.3); }
.file-badge.data  { border-color: rgba(0,255,136,0.3); background: rgba(0,255,136,0.05); color: var(--green) !important; }

.speaking-indicator {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 0.6rem; letter-spacing: 2px;
    color: var(--green); opacity: 0; transition: opacity 0.3s; margin-top: 4px;
}
.speaking-indicator.active { opacity: 1; }
.speaking-indicator span {
    width: 3px; height: 10px; background: var(--green);
    border-radius: 2px; animation: bar 0.8s ease-in-out infinite; display: inline-block;
}
.speaking-indicator span:nth-child(2) { animation-delay: 0.15s; height: 16px; }
.speaking-indicator span:nth-child(3) { animation-delay: 0.30s; height: 12px; }
.speaking-indicator span:nth-child(4) { animation-delay: 0.45s; height: 18px; }
.speaking-indicator span:nth-child(5) { animation-delay: 0.60s; height: 10px; }
@keyframes bar {
    0%, 100% { transform: scaleY(0.4); opacity: 0.5; }
    50%       { transform: scaleY(1.0); opacity: 1.0; }
}

.chat-bar {
    font-size: 0.58rem; letter-spacing: 3px; opacity: 0.2;
    text-align: center; text-transform: uppercase; margin-bottom: 10px;
}

::-webkit-scrollbar       { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--cyan-d); border-radius: 3px; }
hr { border-color: var(--cyan-d) !important; opacity: 0.5; }
</style>
""", unsafe_allow_html=True)


# ── Session state init ──────────────────────────────────────────────────────
if "bot"         not in st.session_state: st.session_state.bot         = LLMHandler()
if "history"     not in st.session_state: st.session_state.history     = []
if "sid"         not in st.session_state: st.session_state.sid         = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
if "voice_test"  not in st.session_state: st.session_state.voice_test  = False
if "file_cache"  not in st.session_state: st.session_state.file_cache  = {}   # name → {type, data/b64}
if "emergency_active" not in st.session_state: st.session_state.emergency_active = False

ARCHIVES = "lab_archives"
os.makedirs(ARCHIVES, exist_ok=True)

LANG_CODE = {"Hindi": "hi-IN", "Maithili": "hi-IN", "Bhojpuri": "hi-IN", "English": "en-US"}

FEMALE_VOICE_HINTS = {
    "hi-IN": ["lekha", "aditi", "sunita", "priya", "divya", "google hindi female",
              "hindi female", "google hindi", "female", "woman"],
    "en-US": ["samantha", "zira", "aria", "jenny", "sonia", "google us english female",
              "microsoft zira", "google us english", "female", "woman"],
}

# Per-language voice presets — tuned to sound cheerful, fresh, NOT sad
# pitch: 1.55-1.65 = bright & sweet | rate: 0.95-1.0 = energetic but clear
VOICE_PRESETS = {
    "Hindi":    {"pitch": 1.6,  "rate": 0.95},
    "Maithili": {"pitch": 1.55, "rate": 0.95},
    "Bhojpuri": {"pitch": 1.55, "rate": 0.95},
    "English":  {"pitch": 1.5,  "rate": 1.0},
}

TEST_PHRASES = {
    "Hindi":    "Haan Shiv bhai! Main yahan hun, bilkul ready. Batao, kya karna hai aaj?",
    "Maithili": "Haan Shiv! Hum taiyar chhi. Ki kaam ache aaj?",
    "Bhojpuri": "Haan Shiv bhaiya! Hum taiyar bani. Ka kaam ba aaj?",
    "English":  "Hey Shiv! All systems go. What are we working on today?",
}

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
CODE_EXTS  = {".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".yaml", ".sh"}
DATA_EXTS  = {".csv", ".txt", ".md", ".log"}
EXCEL_EXTS = {".xlsx", ".xls"}


def get_file_type(filename: str) -> str:
    ext = os.path.splitext(filename.lower())[1]
    if ext in IMAGE_EXTS:  return "image"
    if ext in CODE_EXTS:   return "code"
    if ext in DATA_EXTS:   return "data"
    if ext in EXCEL_EXTS:  return "data"
    return "text"


def get_avatar():
    if os.path.exists("assets"):
        for f in sorted(os.listdir("assets")):
            if f.lower().endswith((".png", ".jpg", ".jpeg")):
                with open(f"assets/{f}", "rb") as fh:
                    return base64.b64encode(fh.read()).decode()
    return None


def save_session(history, sid):
    with open(f"{ARCHIVES}/session_{sid}.json", "w", encoding="utf-8") as f:
        json.dump({
            "sid": sid,
            "saved_at": datetime.datetime.now().isoformat(),
            "messages": len(history),
            "history": history,
        }, f, ensure_ascii=False, indent=2)


def load_session(filename):
    with open(f"{ARCHIVES}/{filename}", "r", encoding="utf-8") as f:
        return json.load(f).get("history", [])


def get_sessions():
    if not os.path.exists(ARCHIVES):
        return []
    return sorted([f for f in os.listdir(ARCHIVES) if f.endswith(".json")], reverse=True)


def clean_for_speech(text: str) -> str:
    t = re.sub(r'```[\s\S]*?```', ' code block. ', text)
    t = re.sub(r'`[^`]+`', '', t)
    t = re.sub(r'[*#_~\[\]<>|\\]', '', t)
    t = re.sub(r'https?://\S+', ' link. ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    t = t.replace('"', ' ').replace("'", ' ')
    return t[:1400]


def build_tts(text: str, lang_code: str, pitch: float, rate: float, volume: float) -> str:
    clean      = clean_for_speech(text)
    hints_json = json.dumps(FEMALE_VOICE_HINTS.get(lang_code, FEMALE_VOICE_HINTS["en-US"]))

    return f"""<script>
(function() {{
    window.speechSynthesis.cancel();

    var fullText = "{clean}";
    var langCode = "{lang_code}";
    var hints    = {hints_json};

    // Split on sentence boundaries incl. Hindi danda
    var parts = fullText.match(/[^।\\.!?]+[।\\.!?]+/g);
    if (!parts || parts.length === 0) parts = [fullText];
    parts = parts.map(function(s) {{ return s.trim(); }}).filter(function(s) {{ return s.length > 1; }});

    function pickVoice(voices) {{
        var langVoices = voices.filter(function(v) {{
            return v.lang.toLowerCase().startsWith(langCode.split('-')[0]);
        }});
        // Try hint keywords in order
        for (var i = 0; i < hints.length; i++) {{
            for (var j = 0; j < langVoices.length; j++) {{
                if (langVoices[j].name.toLowerCase().indexOf(hints[i]) !== -1) {{
                    return langVoices[j];
                }}
            }}
        }}
        // Fallback: any female voice in that language
        for (var k = 0; k < langVoices.length; k++) {{
            var n = langVoices[k].name.toLowerCase();
            if (n.indexOf('female') !== -1 || n.indexOf('woman') !== -1) return langVoices[k];
        }}
        if (langVoices.length > 0) return langVoices[0];
        return voices[0] || null;
    }}

    function speakQueue(voices) {{
        var chosen = pickVoice(voices);
        var idx    = 0;

        // Chrome long-speech keepalive fix
        var keepAlive = setInterval(function() {{
            if (window.speechSynthesis.speaking) {{
                window.speechSynthesis.pause();
                window.speechSynthesis.resume();
            }} else {{ clearInterval(keepAlive); }}
        }}, 8000);

        function next() {{
            if (idx >= parts.length) {{
                clearInterval(keepAlive);
                var ind = document.getElementById('shiv-speaking');
                if (ind) ind.classList.remove('active');
                return;
            }}
            var u    = new SpeechSynthesisUtterance(parts[idx++]);
            u.lang   = langCode;
            u.pitch  = {pitch};
            u.rate   = {rate};
            u.volume = {volume};
            if (chosen) u.voice = chosen;
            u.onend  = next;
            u.onerror = next;
            window.speechSynthesis.speak(u);
        }}

        var ind = document.getElementById('shiv-speaking');
        if (ind) ind.classList.add('active');
        next();
    }}

    var v = window.speechSynthesis.getVoices();
    if (v.length > 0) {{
        speakQueue(v);
    }} else {{
        window.speechSynthesis.addEventListener('voiceschanged', function handler() {{
            window.speechSynthesis.removeEventListener('voiceschanged', handler);
            speakQueue(window.speechSynthesis.getVoices());
        }});
    }}
}})();
</script>"""


# ── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    avatar = get_avatar()
    av_html = (
        f'<img src="data:image/jpeg;base64,{avatar}" class="avatar-img">'
        if avatar else
        '<div style="font-size:3.6rem;filter:drop-shadow(0 0 22px #00e5ff);z-index:1;position:relative">🔱</div>'
    )
    st.markdown(
        f'<div class="avatar-wrap">'
        f'<div class="aura-ring"></div><div class="aura-ring-2"></div>'
        f'{av_html}'
        f'<div class="avatar-name">🔱 Shiv AI</div>'
        f'<div class="avatar-sub">STREE · LABORATORY CORE</div>'
        f'<div class="avatar-stat">● ONLINE · SHIVNANDAN KUMAR</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="panel-title">⚡ Control Panel</div>', unsafe_allow_html=True)

    mood = st.selectbox("NEURAL MOOD:", [
        "Sweet Ariana ❤️", "Professional Scientist", "Emotional Support", "Funny Friend"
    ])

    st.markdown('<div class="kill-box">', unsafe_allow_html=True)
    emergency_silent = st.toggle("🔴 EMERGENCY SILENT — KILL ALL AUDIO", value=False)
    st.markdown('</div>', unsafe_allow_html=True)

    talk_mode = st.toggle("🔊 TALK MODE — Auto Speak Responses", value=True)

    # Voice engine panel
    st.markdown('<div class="voice-box">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title" style="border:none;margin-bottom:6px;opacity:0.5">🎙️ Voice Engine</div>', unsafe_allow_html=True)

    lang_for_preset = st.session_state.get("_lang_preview", "Hindi")
    preset = VOICE_PRESETS.get(lang_for_preset, VOICE_PRESETS["Hindi"])

    voice_pitch  = st.slider("Pitch",  min_value=0.8, max_value=2.0, value=preset["pitch"], step=0.05, key="vpitch")
    voice_rate   = st.slider("Speed",  min_value=0.5, max_value=1.6, value=preset["rate"],  step=0.05, key="vrate")
    voice_volume = st.slider("Volume", min_value=0.1, max_value=1.0, value=1.0,             step=0.05, key="vvol")

    if st.button("🔔 Test Voice"):
        st.session_state.voice_test = True

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

    lang = st.selectbox("COMM PROTOCOL:", ["Hindi", "English", "Maithili", "Bhojpuri"])
    st.session_state["_lang_preview"] = lang

    mode = st.radio("UI LEVEL:", ["Normal Mode 🗣️", "Talk to Talk 💬", "Career/Engineer Mode 💻"])

    st.markdown("---")
    ufile = st.file_uploader(
        "INJECT DATA STREAM",
        type=["png", "jpg", "jpeg", "webp", "gif", "txt", "py", "js", "ts",
              "html", "css", "csv", "json", "xml", "md", "log",
              "xlsx", "xls", "pdf", "doc", "docx"],
        help="Images, code, CSV, Excel, PDF, text — Shiv AI reads all of it."
    )

    st.markdown("---")
    ca, cb = st.columns(2)
    with ca:
        if st.button("💾 SAVE LOG"):
            save_session(st.session_state.history, st.session_state.sid)
            st.success("Archived!")
    with cb:
        if st.button("🔴 PURGE ALL"):
            st.session_state.history     = []
            st.session_state.file_cache  = {}
            st.session_state.sid = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            st.rerun()

    sessions = get_sessions()
    if sessions:
        st.markdown('<div class="panel-title" style="margin-top:12px">📂 Lab Archives</div>', unsafe_allow_html=True)
        pick = st.selectbox("Load Session:", ["— Select —"] + sessions, label_visibility="collapsed")
        if pick != "— Select —" and st.button("⬆️ LOAD SESSION"):
            st.session_state.history = load_session(pick)
            st.rerun()


# ── AUDIO KILL ───────────────────────────────────────────────────────────────
if emergency_silent:
    st.session_state.emergency_active = True
    st.components.v1.html("<script>window.speechSynthesis.cancel();</script>", height=0)
else:
    st.session_state.emergency_active = False

# ── VOICE TEST ───────────────────────────────────────────────────────────────
if st.session_state.voice_test and not emergency_silent:
    phrase = TEST_PHRASES.get(lang, TEST_PHRASES["English"])
    lc     = LANG_CODE.get(lang, "hi-IN")
    st.components.v1.html(
        build_tts(phrase, lc, voice_pitch, voice_rate, voice_volume),
        height=0
    )
    st.session_state.voice_test = False

# ── PROCESS UPLOADED FILE ────────────────────────────────────────────────────
fdata   = ""
imgb64  = None
ftype   = ""
fname   = ""

if ufile:
    fname = ufile.name
    ftype = get_file_type(fname)
    file_ext = os.path.splitext(fname.lower())[1].lstrip(".")

    # Cache so we don't re-read on every Streamlit rerun
    if fname not in st.session_state.file_cache:
        raw = ufile.getvalue()
        if ftype == "image":
            st.session_state.file_cache[fname] = {
                "type": "image",
                "b64": base64.b64encode(raw).decode(),
            }
        elif file_ext in ["xlsx", "xls"]:
            # EXCEL PROCESSOR: Read with pandas and convert to readable string
            try:
                import io
                if _PANDAS:
                    df = pd.read_excel(io.BytesIO(raw), engine='openpyxl')
                    text_content = f"Excel Data:\n{df.to_string()}"
                else:
                    text_content = "[Excel file detected — install pandas & openpyxl to read it]"
            except Exception as e:
                text_content = f"[Excel read error: {e}]"
            st.session_state.file_cache[fname] = {
                "type": "data",
                "text": text_content[:4000],
            }
        else:
            try:
                text_content = raw.decode("utf-8", errors="ignore")
            except Exception:
                text_content = ""
            st.session_state.file_cache[fname] = {
                "type": ftype,
                "text": text_content[:4000],   # Increased limit for better context
            }

    cached = st.session_state.file_cache.get(fname, {})
    if cached.get("type") == "image":
        imgb64 = cached["b64"]
    else:
        fdata = cached.get("text", "")

# ── HEADER + SPEAKING INDICATOR ──────────────────────────────────────────────
st.markdown(
    '<div class="chat-bar">SHIV CORE · LABORATORY v7.0 · ARCHITECT: SHIVNANDAN KUMAR</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div id="shiv-speaking" class="speaking-indicator">'
    '<span></span><span></span><span></span><span></span><span></span>'
    '&nbsp;SPEAKING...</div>',
    unsafe_allow_html=True,
)

# File active badge — shows user what file is loaded
if ufile and fname:
    badge_class = ftype
    icon = {"image": "🖼️", "code": "💻", "data": "📊"}.get(ftype, "📄")
    st.markdown(
        f'<div class="file-badge {badge_class}">'
        f'{icon} &nbsp; {fname} &nbsp;·&nbsp; {ftype.upper()} LOADED — Ask me anything about it'
        f'</div>',
        unsafe_allow_html=True,
    )

# Show image preview if it's an image file
if imgb64 and ufile:
    ext = os.path.splitext(ufile.name.lower())[1].lstrip(".")
    mime_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif", "webp": "webp"}
    mime = mime_map.get(ext, "jpeg")
    with st.expander("🖼️ Image Preview", expanded=False):
        st.markdown(
            f'<img src="data:image/{mime};base64,{imgb64}" '
            f'style="max-width:100%;border-radius:8px;border:1px solid rgba(0,229,255,0.2)">',
            unsafe_allow_html=True,
        )

# ── CHAT HISTORY ─────────────────────────────────────────────────────────────
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── INPUT ────────────────────────────────────────────────────────────────────
v_in = None
if MIC_OK:
    col1, col2 = st.columns([1, 10])
    with col1:
        v_in = speech_to_text(
            language=LANG_CODE.get(lang, "hi-IN"),
            start_prompt="🎙️",
            key="stt"
        )
    with col2:
        t_in = st.chat_input("Command Sequence...")
else:
    t_in = st.chat_input("Command Sequence...")

query = t_in if t_in else v_in

# ── CHAT LOGIC ───────────────────────────────────────────────────────────────
if query:
    st.session_state.history.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner(""):
            reply = st.session_state.bot.chat(
                user_input=query,
                mode=mode,
                mood=mood,
                lang=lang,
                file_data=fdata,
                img_b64=imgb64,
                file_type=ftype,
                history=st.session_state.history[:-1],
            )
        if not st.session_state.emergency_active:
            st.markdown(reply)
        else:
            st.markdown("🔴 *Silent protocol active — output suppressed.*")

        if not emergency_silent and talk_mode:
            lc = LANG_CODE.get(lang, "hi-IN")
            st.components.v1.html(
                build_tts(reply, lc, voice_pitch, voice_rate, voice_volume),
                height=0
            )

    st.session_state.history.append({"role": "assistant", "content": reply})
    save_session(st.session_state.history, st.session_state.sid)