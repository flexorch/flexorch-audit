"""
Generates assets/demo.svg — a terminal-style screenshot of the audit() demo.
Run: python demo/generate_svg.py
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ── Output lines (hardcoded from running demo.py) ────────────────────────────

PROMPT = "$ python demo/demo.py"

LINES = [
    ("prompt",  "$ python demo/demo.py"),
    ("blank",   ""),
    ("kv",      "  Grade  : ", "A", "   (score: 0.86)"),
    ("kv",      "  PII    : ", "4 finding(s)", ""),
    ("pii",     "           email                  ×1"),
    ("pii",     "           iban                   ×1"),
    ("pii",     "           name                   ×1"),
    ("pii",     "           national_id_tr         ×1"),
    ("blank",   ""),
    ("label",   "  Masked output:"),
    ("text",    "  Contract #1042  —  Employment Agreement"),
    ("blank",   ""),
    ("text",    "  Full Name: [REDACTED_NAME]"),
    ("text",    "  TC Kimlik: [REDACTED_NATIONAL_ID_TR]"),
    ("text",    "  E-mail: [REDACTED_EMAIL]"),
    ("text",    "  IBAN: [REDACTED_IBAN]"),
    ("blank",   ""),
    ("text",    "  This agreement governs the employment relationship between"),
    ("text",    "  Flexorch Technology and the employee named above, including"),
    ("text",    "  confidentiality obligations and IP assignment clauses."),
    ("blank",   ""),
]

# ── Dracula palette ──────────────────────────────────────────────────────────

BG        = "#282a36"
FG        = "#f8f8f2"
GREEN     = "#50fa7b"
YELLOW    = "#f1fa8c"
CYAN      = "#8be9fd"
PURPLE    = "#bd93f9"
PINK      = "#ff79c6"
COMMENT   = "#6272a4"
REDACTED  = "#ff5555"

# ── Layout ───────────────────────────────────────────────────────────────────

FONT      = "Consolas, 'Courier New', monospace"
FONT_SIZE = 14
LINE_H    = 22
PAD_X     = 24
PAD_Y     = 20
TITLE_H   = 38
WIDTH     = 720

def line_color(kind):
    return {
        "prompt": GREEN,
        "label":  CYAN,
        "pii":    YELLOW,
        "blank":  FG,
        "kv":     FG,
        "text":   FG,
    }.get(kind, FG)

def escape(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def render_line(kind, *parts):
    if kind in ("blank",):
        return ""
    if kind == "kv":
        label, value, rest = parts
        color_v = GREEN if value[0].isalpha() else CYAN
        return (
            f'<tspan fill="{FG}">{escape(label)}</tspan>'
            f'<tspan fill="{color_v}">{escape(value)}</tspan>'
            f'<tspan fill="{COMMENT}">{escape(rest)}</tspan>'
        )
    text = parts[0]
    color = line_color(kind)
    # Highlight [REDACTED_*] tokens
    if "[REDACTED" in text:
        before, _, after = text.partition("[REDACTED")
        tag, _, after2 = after.partition("]")
        return (
            f'<tspan fill="{FG}">{escape(before)}</tspan>'
            f'<tspan fill="{REDACTED}">[REDACTED{escape(tag)}]</tspan>'
            f'<tspan fill="{FG}">{escape(after2)}</tspan>'
        )
    return f'<tspan fill="{color}">{escape(text)}</tspan>'

# ── Build SVG ────────────────────────────────────────────────────────────────

content_h = PAD_Y + len(LINES) * LINE_H + PAD_Y
HEIGHT    = TITLE_H + content_h

svg_lines = []
svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
                 f'style="font-family:{FONT};font-size:{FONT_SIZE}px;">')

# Window chrome
svg_lines.append(f'  <rect width="{WIDTH}" height="{HEIGHT}" rx="8" fill="{BG}"/>')
svg_lines.append(f'  <rect width="{WIDTH}" height="{TITLE_H}" rx="8" fill="#44475a"/>')
svg_lines.append(f'  <rect y="{TITLE_H - 4}" width="{WIDTH}" height="4" fill="#44475a"/>')
# Dots
for i, col in enumerate(["#ff5555", "#f1fa8c", "#50fa7b"]):
    cx = 16 + i * 20
    svg_lines.append(f'  <circle cx="{cx}" cy="{TITLE_H // 2}" r="6" fill="{col}"/>')
# Title
svg_lines.append(f'  <text x="{WIDTH // 2}" y="{TITLE_H // 2 + 5}" '
                 f'text-anchor="middle" fill="{COMMENT}" font-size="13">flexorch-audit</text>')

# Code lines
base_y = TITLE_H + PAD_Y
for i, entry in enumerate(LINES):
    kind = entry[0]
    parts = entry[1:]
    y = base_y + i * LINE_H
    inner = render_line(kind, *parts)
    if inner == "":
        continue
    svg_lines.append(f'  <text x="{PAD_X}" y="{y + FONT_SIZE}">{inner}</text>')

svg_lines.append("</svg>")

# ── Write ────────────────────────────────────────────────────────────────────

out_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "demo.svg")

with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(svg_lines))

print(f"Written: {os.path.abspath(out_path)}")
