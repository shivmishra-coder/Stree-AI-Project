import streamlit as st
import requests, os, platform, base64, io
from datetime import datetime

try:
    from tavily import TavilyClient
    _TAVILY = True
except ImportError:
    _TAVILY = False

# ADDED: pandas for Excel file reading support
try:
    import pandas as pd
    _PANDAS = True
except ImportError:
    _PANDAS = False

# Configuration Keys
GROQ_KEY = st.secrets["GROK_KEY"]
TAVILY_KEY = st.secrets["TAVILY_API_KEY"]
GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"

# PRESERVED FEATURE: Palmistry Detection Logic
PALMISTRY_WORDS = [
    "hath", "haath", "hast", "rekha", "hastrekha", "palm", "palmistry",
    "hand", "lines", "life line", "heart line", "head line", "fate line",
    "mount", "venus", "jupiter", "saturn", "apollo", "mercury", "luna",
    "girdle", "solomon", "cheiro", "jyotish", "bhavishya", "hath dekho",
    "hath dikhao", "haath dikhao", "kismat", "bhagya rekha",
    "mangal", "shani", "brihaspati", "quadrangle", "ring of",
]

# PRESERVED FEATURE: Live Search Triggers (Multilingual)
LIVE_TRIGGERS = [
    "weather", "temperature", "temp", "news", "today", "current", "latest",
    "who is", "stock", "price", "score", "result", "election", "match",
    "ipl", "cricket", "live", "how much", "what is", "where is", "when is",
    "tell me about", "search", "find",
    "mausam", "barish", "garmi", "sardi", "khabar", "aaj", "abhi", "abhi tak",
    "kaun hai", "kya hua", "batao", "kya hai", "kab hai", "kahan hai",
    "kitna", "kitne", "bताओ", "खोजो", "dhundho", "pata karo", "jankari",
    "taza khabar", "breaking", "kal ka", "aaj ka", "is waqt",
    "ki ache", "kekra lel", "akhbar", "samachaar", "ajuk", "ekhon",
    "ke chhi", "ki bhal", "kothay", "kiya", "khoj karo",
    "ka ba", "rauwa", "aaj ke", "abhi ke", "kawan ba", "kaise ba",
    "kahan ba", "samachar", "batawa", "khojawa", "pata lagao",
]

NON_ENGLISH_LANGS = {"Hindi", "Maithili", "Bhojpuri"}

LANG_LOCALE = {
    "Hindi":    "hi",
    "Maithili": "hi",
    "Bhojpuri": "hi",
    "English":  "en",
}


EXCEL_EXTS = {"xlsx", "xls"}
IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "gif"}


def is_palmistry_query(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in PALMISTRY_WORDS)


def is_file_query(text: str) -> bool:
    """FIX: Universal file detection for Excel, CSV, PDF, and Documents."""
    keywords = [
        "file", "image", "photo", "picture", "tasveer", "dekho", "padhо",
        "padho", "batao", "kya likha", "kya hai is", "explain", "summarize",
        "read", "analyse", "analyze", "csv", "data", "code", "script",
        "ye kya hai", "isme kya", "is file", "is photo", "is image",
        "uploaded", "share kiya", "bheja", "doc", "text", "excel", "sheet", "xlsx",
        "pdf", "word", "document", "spreadsheet", "table", "ankde", "data dikhao"
    ]
    t = text.lower()
    return any(w in t for w in keywords)


def read_excel_bytes(raw_bytes: bytes) -> str:
    """ADDED: Convert raw Excel bytes to a readable string for the AI."""
    if not _PANDAS:
        return "[Excel file detected — please install pandas & openpyxl: pip install pandas openpyxl]"
    try:
        df = pd.read_excel(io.BytesIO(raw_bytes), engine='openpyxl')
        return f"Excel Data:\n{df.to_string()}"
    except Exception as e:
        return f"[Excel read error: {e}]"


class LLMHandler:

    def __init__(self):
        self.key    = GROQ_KEY.strip()
        self.tavily = TavilyClient(api_key=TAVILY_KEY.strip()) if _TAVILY else None
        
        self.emergency_stop = False

    def trigger_emergency_silent(self):
        """FIX: Immediately activates silent protocol to kill all active outputs."""
        self.emergency_stop = True
        return "Emergency Silent Protocol Activated. Shiv, main shant ho gayi hun."

    def _to_english_query(self, query: str) -> str:
        try:
            r = requests.post(
                GROQ_URL,
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You are a search query translator. Output ONLY the English query."},
                        {"role": "user", "content": query},
                    ],
                    "temperature": 0.05,
                    "max_tokens": 60,
                },
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                timeout=8,
            )
            translated = r.json()["choices"][0]["message"]["content"].strip()
            return translated if translated else query
        except Exception:
            return query

    def web_search(self, query: str, lang: str = "English") -> str:
        if not self.tavily: return ""
        results_combined = []
        if lang in NON_ENGLISH_LANGS:
            en_query = self._to_english_query(query)
            try:
                res_en = self.tavily.search(query=en_query, search_depth="advanced", max_results=3)
                results_combined += res_en.get("results", [])
            except Exception: pass
            try:
                res_native = self.tavily.search(query=query, search_depth="basic", max_results=2)
                existing_urls = {r.get("url", "") for r in results_combined}
                for r in res_native.get("results", []):
                    if r.get("url", "") not in existing_urls:
                        results_combined.append(r)
            except Exception: pass
        else:
            try:
                res = self.tavily.search(query=query, search_depth="advanced", max_results=4)
                results_combined = res.get("results", [])
            except Exception: return ""

        parts = []
        for r in results_combined[:5]:
            content = r.get("content", "").strip()
            url     = r.get("url", "")
            if content: parts.append(f"[Source: {url}]\n{content}")
        return "\n\n".join(parts)

    def pc_command(self, text: str):
        if platform.system() != "Windows": return None
        t = text.lower()
        if any(w in t for w in ["lock", "pc band karo", "laptop lock", "system lock"]):
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return "Shiv, system lock kar diya. Security protocol active hai."
        if any(w in t for w in ["alarm", "ghadi", "timer", "clock", "time set", "time lagao"]):
            os.system("start ms-clock:")
            return "Alarm module open kar diya, Shiv."
        if any(w in t for w in ["files", "explorer", "folder", "file manager", "kholo"]):
            os.system("explorer")
            return "File manager open kar rahi hun, Shiv."
        return None

    def build_prompt(self, mode: str, mood: str, lang: str,
                     live_data: str, file_data: str,
                     palmistry_mode: bool = False,
                     file_context: str = "",
                     file_type: str = "") -> str:

        fem_grammar = {
            "Hindi":    "Main kar rahi hoon, bol rahi hoon, samajh rahi hoon, dekh rahi hoon, soch rahi hoon",
            "Maithili": "Hum kari rahal chhi, bolait chhi, bujhait chhi, dekhait chhi",
            "Bhojpuri": "Hum kar tat bani, bolat bani, dekhtat bani, samjhat bani",
            "English":  "I am working on it, I feel, I think, I understand, I believe",
        }

        mood_map = {
            "Sweet Ariana ❤️":      "You are warm, melodic, and deeply affectionate. Call Shiv by his name lovingly.",
            "Professional Scientist": "You are sharp, composed, and analytically precise.",
            "Emotional Support":      "You are gentle, deeply empathetic, and fully present.",
            "Funny Friend":           "You are witty and playful with good local Indian humor.",
        }

        mode_map = {
            "Normal Mode 🗣️":        "Respond naturally and helpfully. You are a smart, sweet personal assistant.",
            "Talk to Talk 💬":        "Keep every reply short — max 2 sentences. Snappy and warm.",
            "Career/Engineer Mode 💻": "Focus entirely on code and logic. Output must be copy-paste ready.",
        }

        palmistry_expert = "You are in CHIRO-PALMISTRY MODE. Analyze MAJOR LINES and MOUNTS using Cheiro's principles."
        now = datetime.now().strftime("%A, %d %B %Y — %I:%M %p")

        prompt = (
            f"You are Shiv AI. Your codename is Stree. You are strictly female.\n"
            f"Your master is Shivnandan Kumar. Current time: {now}\n"
            f"LANGUAGE: Respond in {lang}. GRAMMAR: Use ONLY feminine verb forms: {fem_grammar.get(lang, fem_grammar['English'])}.\n"
            f"MOOD: {mood_map.get(mood, mood_map['Sweet Ariana ❤️'])}\n"
            f"MODE: {mode_map.get(mode, mode_map['Normal Mode 🗣️'])}\n"
        )

        if palmistry_mode:
            prompt += f"{palmistry_expert}\n"

        # ADDED: Smart file context label based on file_type
        if file_context:
            if file_type in ("xlsx", "xls") or file_context.startswith("Excel Data:"):
                label = "EXCEL SPREADSHEET DATA"
            elif file_type == "csv":
                label = "CSV DATA"
            elif file_type in ("pdf", "doc", "docx"):
                label = "DOCUMENT CONTENT"
            elif file_type in ("py", "js", "ts", "html", "css", "json"):
                label = "CODE FILE"
            else:
                label = "FILE CONTENT"
            prompt += f"\n{label} (uploaded by Shiv):\n{file_context}\n"

        if live_data:
            prompt += f"\nLIVE WEB DATA:\n{live_data}\n"

        return prompt

    def chat(self, user_input: str, mode: str, mood: str, lang: str,
             file_data: str = "", img_b64: str = None,
             file_type: str = "", history: list = None) -> str:

        # Reset Emergency flag for new manual input
        self.emergency_stop = False

        pc = self.pc_command(user_input)
        if pc: return pc

        palm_mode = is_palmistry_query(user_input)
        live = ""
        if any(t in user_input.lower() for t in LIVE_TRIGGERS):
            live = self.web_search(user_input, lang)

        
        system = self.build_prompt(
            mode, mood, lang, live, file_data,
            palmistry_mode=palm_mode,
            file_context=file_data,
            file_type=file_type,
        )
        messages = [{"role": "system", "content": system}]

        if history:
            for h in history[-12:]:
                messages.append({"role": h["role"], "content": h["content"]})

        if img_b64:
            vision_instruction = f"{user_input}\n\n[VISION]: Analyze this visual carefully in {lang}."
            messages.append({
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}", "detail": "high"}},
                    {"type": "text", "text": vision_instruction},
                ]
            })
            model = "meta-llama/llama-4-scout-17b-16e-instruct"
        else:
            messages.append({"role": "user", "content": user_input})
            model = "llama-3.3-70b-versatile"

        try:
            r = requests.post(
                GROQ_URL,
                json={"model": model, "messages": messages, "temperature": 0.8, "max_tokens": 1536},
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                timeout=45,
            )

            # UPGRADED: Check if silent button was pressed while the API was waiting
            if self.emergency_stop:
                return ""

            result = r.json()
            if "choices" in result:
                return result["choices"][0]["message"]["content"]
            return "Maafi chahti hun Shiv, server se response nahi mila."
        except Exception as e:
            return f"Neural link error: {e}"
