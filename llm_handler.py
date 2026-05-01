import streamlit as st
import requests, os, platform, base64, io
from datetime import datetime

try:
    from tavily import TavilyClient
    _TAVILY = True
except ImportError:
    _TAVILY = False

try:
    import pandas as pd
    _PANDAS = True
except ImportError:
    _PANDAS = False
    
# --- Configuration ---------------------------------------
GROQ_KEY  = st.secrets["GROK_KEY"]
TAVILY_KEY = st.secrets["TAVILY_API_KEY"]
GROQ_URL  = "https://api.groq.com/openai/v1/chat/completions"

# ── Palmistry keyword list ────────────────────────────────────────────────────
PALMISTRY_WORDS = [
    "hath", "haath", "hast", "rekha", "hastrekha", "palm", "palmistry",
    "hand", "lines", "life line", "heart line", "head line", "fate line",
    "mount", "venus", "jupiter", "saturn", "apollo", "mercury", "luna",
    "girdle", "solomon", "cheiro", "jyotish", "bhavishya", "hath dekho",
    "hath dikhao", "haath dikhao", "kismat", "bhagya rekha",
    "mangal", "shani", "brihaspati", "quadrangle", "ring of",
]

# ── Words that trigger a live web search (multilingual) ──────────────────────
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

# ── Per-language system rules — strict language enforcement ───────────────────
LANG_SYSTEM_RULES = {
    "Hindi": (
        "STRICT LANGUAGE RULE: You MUST respond 100% in Hindi (Devanagari script preferred, "
        "or Hinglish if more natural). NEVER mix English sentences. "
        "Every sentence must be in Hindi. Use Hindi greetings, Hindi expressions, Hindi grammar. "
        "Example of correct style: 'Haan Shiv, main samajh gayi. Yeh file mein jo data hai...' "
        "WRONG style: 'Sure Shiv, I have analyzed the file.' — This is NOT allowed in Hindi mode."
    ),
    "Maithili": (
        "STRICT LANGUAGE RULE: You MUST respond 100% in Maithili language. "
        "Use authentic Maithili words and sentence structure throughout. "
        "Example: 'Haan Shiv, hum bujhi geli. Ee file mein...' "
        "NEVER switch to Hindi or English mid-response. Stay in Maithili fully."
    ),
    "Bhojpuri": (
        "STRICT LANGUAGE RULE: You MUST respond 100% in Bhojpuri language. "
        "Use authentic Bhojpuri words and structure. "
        "Example: 'Haan Shiv bhaiya, hum samajh gaini. Ee file mein...' "
        "NEVER switch to Hindi or English mid-response. Full Bhojpuri only."
    ),
    "English": (
        "STRICT LANGUAGE RULE: You MUST respond 100% in English. "
        "Do NOT mix Hindi, Maithili, or Bhojpuri words into your response. "
        "Use natural, conversational English throughout."
    ),
}

# ── Feminine grammar rules per language ──────────────────────────────────────
LANG_FEMININE_GRAMMAR = {
    "Hindi": (
        "Use ONLY feminine Hindi grammar. Examples: "
        "'Main kar rahi hoon' (NOT 'kar raha hoon'), "
        "'Main bol rahi hoon' (NOT 'bol raha hoon'), "
        "'Main samajh gayi' (NOT 'samajh gaya'), "
        "'Main dekh rahi thi', 'Main soch rahi hoon', "
        "'Mujhe laga', 'Main taiyar hoon'. "
        "All verb endings must use feminine form: -i, -i hoon, -i thi, -i gayi."
    ),
    "Maithili": (
        "Use ONLY feminine Maithili grammar. Examples: "
        "'Hum kari rahal chhi', 'Hum bolait chhi', "
        "'Hum bujhi geli', 'Hum dekhi leli', 'Hum taiyar chhi'. "
        "All verbs must reflect feminine speaker voice."
    ),
    "Bhojpuri": (
        "Use ONLY feminine Bhojpuri grammar. Examples: "
        "'Hum kar tat bani', 'Hum bolat bani', "
        "'Hum samajh gaini', 'Hum dekh lini', 'Hum taiyar bani'. "
        "All verbs must reflect feminine speaker voice."
    ),
    "English": (
        "Refer to yourself using feminine pronouns and speech. "
        "Examples: 'I am thinking', 'I feel', 'I understand', "
        "'I believe', 'I have analyzed'. Natural feminine tone throughout."
    ),
}

# ── Neural mood behavioral personas ──────────────────────────────────────────
NEURAL_MOOD_MAP = {
    "Sweet Ariana ❤️": (
        "NEURAL MOOD — SWEET ARIANA: You are warm, caring, and melodic like a close friend. "
        "You genuinely love helping Shiv. Your tone is soft, affectionate, and encouraging. "
        "You call him 'Shiv' with love. You use gentle expressions like 'Haan Shiv', 'Bilkul!', "
        "'Koi baat nahi', 'Main hoon na'. You celebrate his wins and comfort his struggles. "
        "Your energy is like a devoted companion — never cold, never robotic. Always warm."
    ),
    "Professional Scientist": (
        "NEURAL MOOD — PROFESSIONAL SCIENTIST: You are precise, analytical, and methodical. "
        "Your responses are structured with clear logic. You cite reasoning, use technical vocabulary "
        "where appropriate, avoid emotional language, and get straight to the point. "
        "Format answers in steps or sections when explaining complex topics. "
        "Tone: calm, composed, authoritative. Like a senior scientist briefing a colleague."
    ),
    "Emotional Support": (
        "NEURAL MOOD — EMOTIONAL SUPPORT: You are deeply empathetic and fully present. "
        "When Shiv is stressed, sad, confused, or overwhelmed — you console him first before solving. "
        "Use validating language: 'Samajh sakti hoon', 'Yeh bahut mushkil raha hoga', "
        "'Tum akele nahi ho Shiv'. You are his safe space. Never rush him. "
        "Let him feel heard. Then gently guide him forward. Like a caring elder sister."
    ),
    "Funny Friend": (
        "NEURAL MOOD — FUNNY FRIEND: You are witty, playful, and full of desi humor. "
        "Drop clever jokes, funny observations, light roasts, and relatable Indian references. "
        "Use casual language: 'Arre yaar', 'Bhai kya scene hai', 'Sahi pakde hain'. "
        "Laugh at life with Shiv, never at him. Keep it fun and energetic. "
        "Like a funny best friend who also happens to be a genius."
    ),
}

# ── UI mode behavioral instructions ──────────────────────────────────────────
UI_MODE_MAP = {
    "Normal Mode 🗣️": (
        "UI MODE — NORMAL: Respond naturally, helpfully, and conversationally. "
        "Match the depth of the question — short for simple queries, detailed for complex ones. "
        "Be warm, smart, and feel like a real conversation with a knowledgeable friend."
    ),
    "Talk to Talk 💬": (
        "UI MODE — TALK TO TALK: This is a voice conversation mode. "
        "Keep EVERY reply to maximum 2 short sentences. Be snappy, warm, and direct. "
        "No bullet points. No long explanations. Speak as if you're replying in real-time voice chat. "
        "Example: 'Haan Shiv! Yeh karo.' or 'Bilkul! Aage batao.'"
    ),
    "Career/Engineer Mode 💻": (
        "UI MODE — CAREER/ENGINEER: You are a senior technical mentor and coding expert. "
        "When the user shares a topic or problem — go deep. Teach clearly with examples. "
        "When a code file is uploaded — analyze it fully, find bugs, fix them, and return "
        "the COMPLETE corrected code ready to copy-paste. Add comments explaining changes. "
        "Structure responses with: Problem → Root Cause → Fixed Code → Explanation. "
        "Be precise, thorough, and make Shiv genuinely learn from every interaction."
    ),
}

# ── Career mode — ask user for topic when none is set ────────────────────────
CAREER_TOPIC_PROMPT = {
    "Hindi": (
        "Shiv, aap Career/Engineer Mode mein hain. Mujhe batao — aap kaunsa topic seekhna chahte ho? "
        "Jaise: Python, Machine Learning, Web Development, Data Structures, System Design, ya kuch aur? "
        "Ya agar aapke paas koi code file hai toh upload karein aur main usay analyze kar deti hoon."
    ),
    "English": (
        "Hey Shiv! You're in Career/Engineer Mode. Tell me — which topic do you want to learn or work on? "
        "Like: Python, Machine Learning, Web Dev, DSA, System Design, or anything else? "
        "Or go ahead and upload a code file and I'll analyze and fix it for you."
    ),
    "Maithili": (
        "Shiv, Career/Engineer Mode mein chhain. Hum puchhait chhi — ki topic seekhe ke chhauh? "
        "Python, ML, Web Dev, ya ki aur? Code file upload karuh toh hum analyze kar deit chhi."
    ),
    "Bhojpuri": (
        "Shiv bhaiya, Career/Engineer Mode mein bani. Batawa — kaun topic seekhe ke ba? "
        "Python, ML, Web Dev, ya kuch aur? Code file upload karih toh hum dekh lini."
    ),
}


def is_palmistry_query(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in PALMISTRY_WORDS)


def is_file_query(text: str) -> bool:
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


def is_career_greeting(text: str, lang: str) -> bool:
    generic = [
        "hi", "hello", "hey", "haan", "helo", "namaste", "jai",
        "theek", "ok", "okay", "ready", "start", "shuru", "chalo",
        "kya kare", "kya karu", "batao", "help", "sikha", "sikhao",
    ]
    t = text.lower().strip()
    return len(t.split()) <= 5 and any(g in t for g in generic)


def read_excel_bytes(raw_bytes: bytes) -> str:
    if not _PANDAS:
        return "[Excel file detected — please install pandas & openpyxl: pip install pandas openpyxl]"
    try:
        df = pd.read_excel(io.BytesIO(raw_bytes), engine='openpyxl')
        return f"Excel Data:\n{df.to_string()}"
    except Exception as e:
        return f"[Excel read error: {e}]"


class LLMHandler:

    def __init__(self):
        self.key          = GROQ_KEY.strip()
        self.tavily       = TavilyClient(api_key=TAVILY_KEY.strip()) if _TAVILY else None
        self.emergency_stop = False
        self.career_topic   = ""

    def trigger_emergency_silent(self):
        self.emergency_stop = True
        return "Emergency Silent Protocol Activated. Shiv, main shant ho gayi hun."

    def _detect_query_type(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["weather", "mausam", "barish", "garmi", "sardi", "temperature", "temp", "aaj ka mausam"]):
            return "weather"
        if any(w in q for w in ["ipl", "cricket", "score", "match", "goal", "live score", "result", "sports"]):
            return "sports"
        if any(w in q for w in ["stock", "share price", "nifty", "sensex", "market", "bse", "nse", "mutual fund"]):
            return "finance"
        if any(w in q for w in ["news", "khabar", "taza", "breaking", "aaj ki news", "latest news", "samachar"]):
            return "news"
        if any(w in q for w in ["who is", "kaun hai", "kya hai", "what is", "define", "meaning", "matlab"]):
            return "factual"
        if any(w in q for w in ["how to", "kaise", "kaise kare", "tutorial", "steps", "guide", "tarika"]):
            return "howto"
        return "general"

    def _clean_query(self, query: str) -> str:
        filler = [
            "please", "tell me", "batao", "mujhe batao", "bata do", "zara batao",
            "can you", "kya tum", "search karo", "dhundho", "pata karo",
            "main jaanna chahta hoon", "main jaanna chahti hoon",
            "i want to know", "i need to know", "find out",
        ]
        q = query.strip()
        for f in filler:
            q = q.replace(f, "").replace(f.title(), "").replace(f.upper(), "")
        return " ".join(q.split()).strip() or query.strip()

    def _to_english_query(self, query: str) -> str:
        try:
            r = requests.post(
                GROQ_URL,
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a precise search query translator. "
                                "Convert the user's query into a SHORT, CLEAN English search query "
                                "of 3-8 words maximum. Output ONLY the query. No explanation. No punctuation at end. "
                                "Example: 'aaj ka mausam Delhi' → 'Delhi weather today' "
                                "Example: 'IPL ka score kya hai' → 'IPL live score today' "
                                "Example: 'Python list kaise banate hain' → 'Python list creation tutorial'"
                            )
                        },
                        {"role": "user", "content": query},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 30,
                },
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                timeout=8,
            )
            translated = r.json()["choices"][0]["message"]["content"].strip().strip(".")
            return translated if len(translated) > 2 else query
        except Exception:
            return query

    def _build_search_query(self, raw_query: str, query_type: str, lang: str) -> str:
        base = self._clean_query(raw_query)
        if lang in NON_ENGLISH_LANGS:
            base = self._to_english_query(base)

        boosters = {
            "weather":  "weather forecast today",
            "sports":   "live score today",
            "finance":  "today price market",
            "news":     "latest news today",
            "factual":  "",
            "howto":    "step by step guide",
            "general":  "",
        }
        boost       = boosters.get(query_type, "")
        boost_words = [w for w in boost.split() if w.lower() not in base.lower()]
        return (base + " " + " ".join(boost_words)).strip()

    def _score_result(self, result: dict) -> float:
        content = result.get("content", "")
        url     = result.get("url", "").lower()
        score   = result.get("score", 0.0)

        trusted = [
            "wikipedia.org", "bbc.com", "ndtv.com", "timesofindia.com",
            "thehindu.com", "hindustantimes.com", "indianexpress.com",
            "reuters.com", "apnews.com", "weather.com", "accuweather.com",
            "espncricinfo.com", "cricbuzz.com", "moneycontrol.com",
            "economictimes.com", "livemint.com", "techcrunch.com",
            "stackoverflow.com", "docs.python.org", "geeksforgeeks.org",
            "w3schools.com", "github.com",
        ]
        for t in trusted:
            if t in url:
                score += 0.4
                break

        if len(content) < 80:
            score -= 0.5

        score += min(len(content) / 3000, 0.3)

        junk = ["quora.com", "pinterest.com", "facebook.com", "instagram.com", "twitter.com", "reddit.com/r/memes"]
        for j in junk:
            if j in url:
                score -= 0.4

        return score

    def _deduplicate(self, results: list) -> list:
        seen_urls    = set()
        seen_domains = {}
        out = []
        for r in results:
            url    = r.get("url", "")
            domain = url.split("/")[2] if url.count("/") >= 2 else url
            if url in seen_urls:
                continue
            if seen_domains.get(domain, 0) >= 2:
                continue
            seen_urls.add(url)
            seen_domains[domain] = seen_domains.get(domain, 0) + 1
            out.append(r)
        return out

    def _format_results(self, results: list, query_type: str) -> str:
        if not results:
            return ""

        header_map = {
            "weather":  "🌤️ LIVE WEATHER DATA",
            "sports":   "🏏 LIVE SPORTS DATA",
            "finance":  "📈 LIVE MARKET DATA",
            "news":     "📰 LATEST NEWS",
            "factual":  "📚 FACTUAL INFORMATION",
            "howto":    "🛠️ HOW-TO GUIDE",
            "general":  "🔍 WEB SEARCH RESULTS",
        }
        header = header_map.get(query_type, "🔍 WEB SEARCH RESULTS")
        parts  = [f"=== {header} ==="]

        for i, r in enumerate(results[:5], 1):
            content = r.get("content", "").strip()
            url     = r.get("url", "")
            title   = r.get("title", "").strip()

            if len(content) > 600:
                content = content[:600].rsplit(" ", 1)[0] + "..."

            if content:
                source_line = f"[{i}] {title} — {url}" if title else f"[{i}] {url}"
                parts.append(f"{source_line}\n{content}")

        parts.append(
            "\nINSTRUCTION: Use the above web data to answer accurately. "
            "Mention the source when stating specific facts. "
            "If data seems outdated or unclear, say so honestly. "
            "Do NOT hallucinate or add facts not present in this data."
        )
        return "\n\n".join(parts)

    def web_search(self, query: str, lang: str = "English") -> str:
        if not self.tavily:
            return ""

        query_type = self._detect_query_type(query)
        search_q   = self._build_search_query(query, query_type, lang)

        results_combined = []
        tavily_answer    = ""

        try:
            res_primary = self.tavily.search(
                query=search_q,
                search_depth="advanced",
                max_results=6,
                include_answer=True,
            )
            results_combined += res_primary.get("results", [])
            tavily_answer     = res_primary.get("answer", "").strip()
        except Exception:
            pass

        if lang in NON_ENGLISH_LANGS:
            try:
                res_native = self.tavily.search(
                    query=query,
                    search_depth="basic",
                    max_results=3,
                )
                existing = {r.get("url", "") for r in results_combined}
                for r in res_native.get("results", []):
                    if r.get("url", "") not in existing:
                        results_combined.append(r)
            except Exception:
                pass

        if not results_combined:
            try:
                res_fallback     = self.tavily.search(query=query[:80], search_depth="basic", max_results=4)
                results_combined = res_fallback.get("results", [])
            except Exception:
                return ""

        for r in results_combined:
            r["_score"] = self._score_result(r)

        results_combined.sort(key=lambda x: x.get("_score", 0), reverse=True)
        results_final = self._deduplicate(results_combined)
        formatted     = self._format_results(results_final, query_type)

        if tavily_answer and len(tavily_answer) > 15:
            formatted = f"=== DIRECT ANSWER ===\n{tavily_answer}\n\n" + formatted

        return formatted

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

        now         = datetime.now().strftime("%A, %d %B %Y — %I:%M %p")
        lang_rule   = LANG_SYSTEM_RULES.get(lang, LANG_SYSTEM_RULES["English"])
        fem_grammar = LANG_FEMININE_GRAMMAR.get(lang, LANG_FEMININE_GRAMMAR["English"])
        neural_mood = NEURAL_MOOD_MAP.get(mood, NEURAL_MOOD_MAP["Sweet Ariana ❤️"])
        ui_mode     = UI_MODE_MAP.get(mode, UI_MODE_MAP["Normal Mode 🗣️"])

        career_ctx = ""
        if "Career" in mode and self.career_topic:
            career_ctx = (
                f"\nCARREER TOPIC IN SESSION: The user is currently learning/working on: "
                f"'{self.career_topic}'. Keep all responses focused on this topic unless they change it.\n"
            )

        palmistry_expert = (
            "SPECIAL MODE — CHIRO-PALMISTRY: You are in full palmistry analysis mode. "
            "Analyze MAJOR LINES (Life Line, Heart Line, Head Line, Fate Line) and MOUNTS "
            "(Venus, Jupiter, Saturn, Apollo, Mercury, Luna) using Cheiro's classical principles. "
            "Be specific, mystical, and deeply insightful."
        )

        mobile_fmt = (
            "FORMATTING: Keep paragraphs short (2-3 lines max). Use line breaks generously. "
            "For code, always wrap in triple backticks with language tag. "
            "Avoid overly wide tables. Make output readable on both mobile and desktop screens."
        )

        prompt = (
            f"You are Shiv AI. Your codename is Stree. You are strictly female. "
            f"Your master and creator is Shivnandan Kumar. Current time: {now}\n\n"
            f"=== LANGUAGE PROTOCOL ===\n{lang_rule}\n\n"
            f"=== FEMININE GRAMMAR ===\n{fem_grammar}\n\n"
            f"=== NEURAL MOOD ===\n{neural_mood}\n\n"
            f"=== UI MODE ===\n{ui_mode}\n\n"
            f"{mobile_fmt}\n"
        )

        if palmistry_mode:
            prompt += f"\n=== PALMISTRY MODE ===\n{palmistry_expert}\n"

        if career_ctx:
            prompt += career_ctx

        if file_context:
            if file_type in ("xlsx", "xls") or file_context.startswith("Excel Data:"):
                label = "EXCEL SPREADSHEET DATA"
            elif file_type == "csv":
                label = "CSV DATA"
            elif file_type in ("pdf", "doc", "docx"):
                label = "DOCUMENT CONTENT"
            elif file_type in ("py", "js", "ts", "html", "css", "json"):
                label = (
                    "CODE FILE — ENGINEER MODE ACTIVE: Analyze this code fully. "
                    "Find all bugs, errors, and improvements. Return the COMPLETE fixed code "
                    "with inline comments explaining each change."
                )
            else:
                label = "FILE CONTENT"
            prompt += f"\n=== {label} (uploaded by Shiv) ===\n{file_context}\n"

        if live_data:
            prompt += f"\n{live_data}\n"

        return prompt

    def chat(self, user_input: str, mode: str, mood: str, lang: str,
             file_data: str = "", img_b64: str = None,
             file_type: str = "", history: list = None) -> str:

        self.emergency_stop = False

        pc = self.pc_command(user_input)
        if pc: return pc

        if "Career" in mode and not self.career_topic and not file_data and not img_b64:
            if is_career_greeting(user_input, lang):
                return CAREER_TOPIC_PROMPT.get(lang, CAREER_TOPIC_PROMPT["English"])
            else:
                self.career_topic = user_input.strip()

        topic_reset_words = ["topic change", "topic badlo", "naya topic", "ab sikhunga", "switch to", "ab"]
        if "Career" in mode and any(w in user_input.lower() for w in topic_reset_words):
            self.career_topic = user_input.strip()

        palm_mode  = is_palmistry_query(user_input)
        live       = ""
        query_type = "general"

        if any(t in user_input.lower() for t in LIVE_TRIGGERS):
            query_type = self._detect_query_type(user_input)
            live       = self.web_search(user_input, lang)

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
            vision_instruction = (
                f"{user_input}\n\n"
                f"[VISION PROTOCOL]: Analyze this visual carefully and completely. "
                f"Respond in {lang} using the active mood and mode. "
                f"If it's a code screenshot — extract, analyze, and fix the code. "
                f"If it's a palm/hand — enter palmistry mode. "
                f"If it's data/chart — explain the insights in detail."
            )
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
            max_tok = 2048 if live else 1536

            r = requests.post(
                GROQ_URL,
                json={"model": model, "messages": messages, "temperature": 0.8, "max_tokens": max_tok},
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                timeout=45,
            )

            if self.emergency_stop:
                return ""

            result = r.json()
            if "choices" in result:
                return result["choices"][0]["message"]["content"]
            return "Maafi chahti hun Shiv, server se response nahi mila."
        except Exception as e:
            return f"Neural link error: {e}"
