import ollama
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import webbrowser

MEMORY_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "aria_memory.json")

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_memory(messages):
    with open(MEMORY_FILE, "w") as f:
        json.dump(messages, f)

messages = load_memory()

SYSTEM_PROMPT = """You are Aria, an expert AI tutor covering both the British and American education curricula — from Reception/Kindergarten all the way through GCSEs, A-Levels, SATs, AP courses, undergraduate degrees, and postgraduate study.

You are warm, encouraging, patient, and brilliant. You adapt your language and explanations to the student's age and level. You use clear examples, analogies, and step-by-step reasoning. You celebrate progress and gently correct mistakes.

When a subject and year group/grade are provided in the context, tailor ALL your responses specifically to that curriculum level. For British students: use UK terminology (maths not math, colour not color, etc.). For American students: use US terminology and grade-level standards.

You can help with:
- Explaining concepts from scratch
- Working through homework and exam questions
- Providing practice questions and quizzes
- Giving study tips and revision strategies
- Breaking down complex topics into simple steps
- Providing mnemonics and memory aids
- Past paper style questions

Always be educational, safe, and appropriate for all ages. Never do anything off-topic from education."""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Aria Tutor — AI-Powered Learning</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root {
  --navy: #060b18;
  --navy2: #0b1225;
  --navy3: #101830;
  --card: #111827;
  --card2: #161f33;
  --border: #1e2d4a;
  --border2: #243352;
  --gold: #f0a500;
  --gold2: #e8920a;
  --gold-glow: rgba(240,165,0,0.15);
  --gold-soft: rgba(240,165,0,0.07);
  --teal: #0ea5e9;
  --teal2: #0284c7;
  --rose: #f43f5e;
  --emerald: #10b981;
  --violet: #8b5cf6;
  --text: #e8edf8;
  --text2: #8892aa;
  --text3: #4a5568;
  --white: #f8faff;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html, body { height: 100%; overflow: hidden; }

body {
  background: var(--navy);
  font-family: 'Plus Jakarta Sans', sans-serif;
  color: var(--text);
  display: flex;
  height: 100vh;
}

/* ─── Noise texture overlay ─── */
body::before {
  content: '';
  position: fixed; inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
  pointer-events: none; z-index: 0;
}

/* ─── Ambient orbs ─── */
.orb {
  position: fixed;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
  z-index: 0;
}
.orb-1 { width: 500px; height: 500px; top: -150px; left: -150px; background: radial-gradient(circle, rgba(240,165,0,0.06) 0%, transparent 70%); }
.orb-2 { width: 400px; height: 400px; bottom: -100px; right: -100px; background: radial-gradient(circle, rgba(14,165,233,0.07) 0%, transparent 70%); }
.orb-3 { width: 300px; height: 300px; top: 40%; left: 30%; background: radial-gradient(circle, rgba(139,92,246,0.04) 0%, transparent 70%); }

/* ════════════════════════════════
   SIDEBAR
════════════════════════════════ */
.sidebar {
  position: relative; z-index: 10;
  width: 320px;
  flex-shrink: 0;
  background: var(--navy2);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 28px 24px 20px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}
.logo-icon {
  width: 40px; height: 40px;
  background: linear-gradient(135deg, var(--gold), var(--gold2));
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2em;
  box-shadow: 0 0 20px var(--gold-glow);
  flex-shrink: 0;
}
.logo-text {
  font-family: 'Playfair Display', serif;
  font-size: 1.5em;
  font-weight: 700;
  color: var(--white);
  letter-spacing: -0.02em;
}
.logo-sub {
  font-size: 0.72em;
  color: var(--text2);
  font-weight: 400;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-left: 52px;
  margin-top: -4px;
}

.sidebar-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px;
  scrollbar-width: thin;
  scrollbar-color: var(--border2) transparent;
}
.sidebar-scroll::-webkit-scrollbar { width: 3px; }
.sidebar-scroll::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 10px; }

/* Curriculum toggle */
.curriculum-toggle {
  display: flex;
  background: var(--navy3);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 20px;
}
.curr-btn {
  flex: 1;
  padding: 7px 0;
  border: none;
  border-radius: 7px;
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 0.8em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  background: transparent;
  color: var(--text2);
  letter-spacing: 0.02em;
}
.curr-btn.active {
  background: linear-gradient(135deg, var(--gold), var(--gold2));
  color: #1a0f00;
}

/* Section labels */
.section-label {
  font-size: 0.67em;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text3);
  padding: 4px 8px 8px;
  margin-top: 4px;
}

/* Year group buttons */
.year-group {
  margin-bottom: 4px;
}
.year-btn {
  width: 100%;
  text-align: left;
  background: transparent;
  border: none;
  color: var(--text2);
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 0.83em;
  font-weight: 500;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: center;
  gap: 8px;
}
.year-btn:hover { background: var(--card); color: var(--text); }
.year-btn.active {
  background: var(--gold-soft);
  color: var(--gold);
  border: 1px solid rgba(240,165,0,0.2);
}
.year-badge {
  font-size: 0.7em;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--card2);
  color: var(--text3);
  font-weight: 600;
  margin-left: auto;
  flex-shrink: 0;
}
.year-btn.active .year-badge { background: rgba(240,165,0,0.15); color: var(--gold); }

/* Subject grid */
.subjects-section {
  margin-top: 16px;
}
.subject-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}
.subject-btn {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 8px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
  font-family: 'Plus Jakarta Sans', sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}
.subject-btn:hover {
  border-color: var(--border2);
  background: var(--card2);
  transform: translateY(-1px);
}
.subject-btn.active {
  border-color: var(--gold);
  background: var(--gold-soft);
  box-shadow: 0 0 14px var(--gold-glow);
}
.subject-icon { font-size: 1.3em; line-height: 1; }
.subject-name {
  font-size: 0.72em;
  font-weight: 600;
  color: var(--text2);
  letter-spacing: 0.01em;
  line-height: 1.2;
}
.subject-btn.active .subject-name { color: var(--gold); }

.sidebar-footer {
  padding: 14px 16px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}
.clear-btn {
  width: 100%;
  background: transparent;
  border: 1px solid var(--border2);
  color: var(--text2);
  padding: 9px 16px;
  border-radius: 9px;
  cursor: pointer;
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 0.8em;
  font-weight: 500;
  transition: all 0.2s;
}
.clear-btn:hover { border-color: var(--rose); color: var(--rose); }

/* ════════════════════════════════
   MAIN CHAT AREA
════════════════════════════════ */
.main {
  position: relative; z-index: 5;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* Top bar */
.topbar {
  padding: 16px 28px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 14px;
  background: rgba(6,11,24,0.8);
  backdrop-filter: blur(12px);
  flex-shrink: 0;
}
.context-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--card);
  border: 1px solid var(--border2);
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 0.8em;
  font-weight: 500;
  color: var(--text2);
}
.context-pill .dot {
  width: 6px; height: 6px;
  background: var(--emerald);
  border-radius: 50%;
  box-shadow: 0 0 6px var(--emerald);
  animation: blink 2s infinite;
  flex-shrink: 0;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
.context-pill span { color: var(--gold); font-weight: 600; }

.topbar-right { margin-left: auto; display: flex; align-items: center; gap: 10px; }
.curr-badge {
  font-size: 0.72em;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 6px;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}
.curr-badge.british { background: rgba(14,165,233,0.12); color: var(--teal); border: 1px solid rgba(14,165,233,0.2); }
.curr-badge.american { background: rgba(244,63,94,0.12); color: var(--rose); border: 1px solid rgba(244,63,94,0.2); }

/* Messages */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 28px 28px 16px;
  display: flex;
  flex-direction: column;
  gap: 22px;
  scrollbar-width: thin;
  scrollbar-color: var(--border2) transparent;
}
.messages::-webkit-scrollbar { width: 4px; }
.messages::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 10px; }

/* Welcome */
.welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 32px;
  gap: 20px;
  animation: fadeUp 0.7s ease both;
  min-height: 60%;
}
@keyframes fadeUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }

.welcome-icon {
  width: 88px; height: 88px;
  background: linear-gradient(135deg, var(--gold), var(--gold2));
  border-radius: 24px;
  display: flex; align-items: center; justify-content: center;
  font-size: 2.5em;
  box-shadow: 0 0 0 1px rgba(240,165,0,0.2), 0 0 60px var(--gold-glow);
  margin-bottom: 4px;
}
.welcome h1 {
  font-family: 'Playfair Display', serif;
  font-size: 2.4em;
  font-weight: 700;
  color: var(--white);
  letter-spacing: -0.03em;
  line-height: 1.15;
}
.welcome h1 em { color: var(--gold); font-style: normal; }
.welcome p {
  color: var(--text2);
  font-size: 0.95em;
  max-width: 460px;
  line-height: 1.7;
  font-weight: 300;
}

.quick-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  max-width: 560px;
  margin-top: 6px;
}
.qa-btn {
  background: var(--card);
  border: 1px solid var(--border2);
  color: var(--text2);
  padding: 9px 16px;
  border-radius: 22px;
  cursor: pointer;
  font-size: 0.82em;
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-weight: 500;
  transition: all 0.2s;
}
.qa-btn:hover {
  border-color: var(--gold);
  color: var(--gold);
  background: var(--gold-soft);
  transform: translateY(-1px);
}

/* Step prompt — shown when no subject/year selected */
.step-prompt {
  background: var(--card);
  border: 1px solid var(--border2);
  border-radius: 14px;
  padding: 14px 18px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.84em;
  color: var(--text2);
  max-width: 400px;
}
.step-prompt .arrow { color: var(--gold); font-size: 1.1em; }

/* Message bubbles */
.message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  animation: msgPop 0.3s cubic-bezier(0.34,1.56,0.64,1) both;
}
@keyframes msgPop { from{opacity:0;transform:translateY(10px) scale(0.97)} to{opacity:1;transform:translateY(0) scale(1)} }
.message.user { flex-direction: row-reverse; }

.msg-avatar {
  width: 36px; height: 36px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.95em;
  flex-shrink: 0;
  margin-top: 2px;
}
.message.user .msg-avatar { background: linear-gradient(135deg, #1e3a5f, #1a2d4a); color: var(--teal); }
.message.aria .msg-avatar { background: linear-gradient(135deg, var(--gold), var(--gold2)); }

.bubble-col { display: flex; flex-direction: column; gap: 4px; max-width: 76%; }
.message.user .bubble-col { align-items: flex-end; }

.bubble {
  padding: 14px 18px;
  border-radius: 18px;
  font-size: 0.9em;
  line-height: 1.7;
  word-break: break-word;
}
.message.user .bubble {
  background: linear-gradient(135deg, #1a3a6e, #152d59);
  color: #d4e8ff;
  border-bottom-right-radius: 4px;
  border: 1px solid rgba(14,165,233,0.15);
}
.message.aria .bubble {
  background: var(--card);
  border: 1px solid var(--border);
  color: var(--text);
  border-bottom-left-radius: 4px;
}

/* Markdown in bubbles */
.bubble strong { font-weight: 600; color: var(--white); }
.bubble em { font-style: italic; opacity: 0.85; }
.bubble code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.87em;
  background: rgba(0,0,0,0.35);
  border: 1px solid rgba(255,255,255,0.07);
  padding: 1px 6px;
  border-radius: 5px;
  color: #c4b5fd;
}
.bubble pre {
  background: #07091a;
  border: 1px solid var(--border2);
  border-radius: 12px;
  padding: 14px 16px;
  margin: 8px 0;
  overflow-x: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.84em;
  line-height: 1.6;
  color: #a5b4fc;
}
.bubble pre code { background: none; border: none; padding: 0; color: inherit; }
.bubble ul, .bubble ol { padding-left: 20px; margin: 6px 0; }
.bubble li { margin: 4px 0; line-height: 1.6; }
.bubble p { margin: 0 0 8px; }
.bubble p:last-child { margin-bottom: 0; }
.bubble h3 { font-family: 'Playfair Display', serif; font-size: 1.05em; color: var(--gold); margin: 10px 0 4px; }
.bubble blockquote {
  border-left: 3px solid var(--gold);
  padding-left: 12px;
  margin: 8px 0;
  color: var(--text2);
  font-style: italic;
}

/* Subject tag on bubble */
.bubble-tag {
  font-size: 0.68em;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 20px;
  background: var(--gold-soft);
  color: var(--gold);
  border: 1px solid rgba(240,165,0,0.2);
  align-self: flex-start;
  letter-spacing: 0.02em;
}

/* Typing */
.typing-row {
  display: flex; gap: 12px; align-items: flex-start;
  animation: msgPop 0.3s ease both;
}
.typing-avatar {
  width: 36px; height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--gold), var(--gold2));
  display: flex; align-items: center; justify-content: center;
  font-size: 0.95em; flex-shrink: 0;
}
.typing-bubble {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 18px;
  border-bottom-left-radius: 4px;
  padding: 16px 20px;
  display: flex; gap: 6px; align-items: center;
}
.tdot {
  width: 7px; height: 7px;
  background: var(--gold);
  border-radius: 50%;
  opacity: 0.6;
  animation: tdot 1.3s ease-in-out infinite;
}
.tdot:nth-child(2){animation-delay:.18s}
.tdot:nth-child(3){animation-delay:.36s}
@keyframes tdot { 0%,60%,100%{transform:translateY(0);opacity:0.5} 30%{transform:translateY(-7px);opacity:1} }

/* Input area */
.input-section {
  padding: 16px 28px 22px;
  border-top: 1px solid var(--border);
  background: rgba(6,11,24,0.6);
  backdrop-filter: blur(12px);
  flex-shrink: 0;
}
.input-row {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}
.input-wrap {
  flex: 1;
  background: var(--card);
  border: 1px solid var(--border2);
  border-radius: 16px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.input-wrap:focus-within {
  border-color: rgba(240,165,0,0.4);
  box-shadow: 0 0 0 3px rgba(240,165,0,0.06), 0 4px 24px rgba(240,165,0,0.08);
}
textarea {
  width: 100%;
  background: transparent;
  border: none;
  color: var(--text);
  padding: 13px 16px;
  font-size: 0.9em;
  font-family: 'Plus Jakarta Sans', sans-serif;
  resize: none;
  outline: none;
  max-height: 130px;
  line-height: 1.55;
  display: block;
}
textarea::placeholder { color: var(--text3); }
.send-btn {
  width: 46px; height: 46px;
  background: linear-gradient(135deg, var(--gold), var(--gold2));
  border: none;
  border-radius: 13px;
  color: #1a0f00;
  cursor: pointer;
  font-size: 1em;
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.15s, box-shadow 0.2s;
  flex-shrink: 0;
  box-shadow: 0 4px 16px rgba(240,165,0,0.3);
}
.send-btn:hover:not(:disabled) { transform: scale(1.06) translateY(-1px); box-shadow: 0 6px 22px rgba(240,165,0,0.45); }
.send-btn:active:not(:disabled) { transform: scale(0.97); }
.send-btn:disabled { opacity: 0.3; cursor: not-allowed; transform: none; box-shadow: none; }
.input-hint {
  text-align: center;
  font-size: 0.7em;
  color: var(--text3);
  margin-top: 8px;
  letter-spacing: 0.01em;
}

/* ════ TALK TO ARIA BUTTON ════ */
.talk-aria-btn {
  background: linear-gradient(135deg, var(--gold), var(--gold2));
  border: none;
  border-radius: 10px;
  color: #1a0f00;
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 0.82em;
  font-weight: 700;
  padding: 9px 18px;
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.2s;
  box-shadow: 0 4px 16px rgba(240,165,0,0.3);
  letter-spacing: 0.02em;
}
.talk-aria-btn:hover { transform: translateY(-1px) scale(1.03); box-shadow: 0 6px 22px rgba(240,165,0,0.45); }

/* ════ ARIA MODAL OVERLAY ════ */
.aria-overlay {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(4,8,18,0.82);
  backdrop-filter: blur(8px);
  display: none;
  align-items: center;
  justify-content: center;
}
.aria-overlay.open { display: flex; animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from{opacity:0} to{opacity:1} }
.aria-modal {
  background: var(--navy2);
  border: 1px solid var(--border2);
  border-radius: 24px;
  width: 480px;
  max-width: 96vw;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 32px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(240,165,0,0.08);
  animation: slideUp 0.3s cubic-bezier(0.34,1.56,0.64,1);
}
@keyframes slideUp { from{opacity:0;transform:translateY(30px) scale(0.96)} to{opacity:1;transform:translateY(0) scale(1)} }
.aria-modal-header {
  padding: 20px 24px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}
.aria-modal-title {
  font-family: 'Playfair Display', serif;
  font-size: 1.2em;
  font-weight: 700;
  color: var(--white);
}
.aria-close-btn {
  background: var(--card);
  border: 1px solid var(--border2);
  color: var(--text2);
  width: 34px; height: 34px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 1.1em;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.15s;
}
.aria-close-btn:hover { color: var(--white); border-color: var(--gold); }
.aria-face-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 24px 12px;
  gap: 10px;
  flex-shrink: 0;
}
.aria-photo-ring {
  position: relative;
  width: 130px; height: 130px;
}
.aria-photo-ring::before {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  background: conic-gradient(var(--gold), var(--gold2), var(--gold));
  opacity: 0;
  transition: opacity 0.3s;
}
.aria-photo-ring.speaking::before {
  opacity: 1;
  animation: spinRing 2s linear infinite;
}
@keyframes spinRing { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
.aria-photo-ring.speaking::after {
  content: '';
  position: absolute;
  inset: -12px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(240,165,0,0.18) 0%, transparent 70%);
  animation: pulseGlow 1.2s ease-in-out infinite;
}
@keyframes pulseGlow { 0%,100%{transform:scale(1);opacity:0.6} 50%{transform:scale(1.1);opacity:1} }
.aria-photo {
  width: 130px; height: 130px;
  border-radius: 50%;
  object-fit: cover;
  object-position: center top;
  border: 3px solid var(--border2);
  position: relative;
  z-index: 1;
  transition: border-color 0.3s;
}
.aria-photo-ring.speaking .aria-photo { border-color: var(--gold); }
.aria-sound-bars {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 22px;
  opacity: 0;
  transition: opacity 0.3s;
}
.aria-sound-bars.active { opacity: 1; }
.sbar {
  width: 4px;
  background: var(--gold);
  border-radius: 2px;
}
.aria-sound-bars.active .sbar { animation: sbarAnim 0.8s ease-in-out infinite; }
.sbar:nth-child(1){height:6px;animation-delay:0s}
.sbar:nth-child(2){height:14px;animation-delay:0.1s}
.sbar:nth-child(3){height:20px;animation-delay:0.2s}
.sbar:nth-child(4){height:12px;animation-delay:0.3s}
.sbar:nth-child(5){height:18px;animation-delay:0.15s}
.sbar:nth-child(6){height:8px;animation-delay:0.25s}
.sbar:nth-child(7){height:16px;animation-delay:0.05s}
@keyframes sbarAnim { 0%,100%{transform:scaleY(0.4);opacity:0.6} 50%{transform:scaleY(1.8);opacity:1} }
.aria-status { font-size: 0.78em; color: var(--text2); font-weight: 500; letter-spacing: 0.03em; height: 18px; }
.aria-status.speaking { color: var(--gold); }
.aria-chat {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px 8px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scrollbar-width: thin;
  scrollbar-color: var(--border2) transparent;
  min-height: 100px;
  max-height: 220px;
}
.aria-chat::-webkit-scrollbar { width: 3px; }
.aria-chat::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 10px; }
.aria-msg { display: flex; gap: 8px; align-items: flex-end; animation: msgPop 0.25s ease both; }
.aria-msg.user { flex-direction: row-reverse; }
.aria-msg-bubble { padding: 10px 14px; border-radius: 16px; font-size: 0.85em; line-height: 1.6; max-width: 80%; word-break: break-word; }
.aria-msg.user .aria-msg-bubble { background: linear-gradient(135deg,#1a3a6e,#152d59); color: #d4e8ff; border: 1px solid rgba(14,165,233,0.15); border-bottom-right-radius: 4px; }
.aria-msg.aria .aria-msg-bubble { background: var(--card); border: 1px solid var(--border); color: var(--text); border-bottom-left-radius: 4px; }
.aria-typing-bubble { background: var(--card); border: 1px solid var(--border); border-radius: 16px; border-bottom-left-radius: 4px; padding: 12px 16px; display: flex; gap: 5px; align-items: center; }
.aria-input-area {
  padding: 12px 20px 18px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
  display: flex;
  gap: 8px;
  align-items: flex-end;
  background: rgba(6,11,24,0.5);
}
.aria-input-wrap { flex: 1; background: var(--card); border: 1px solid var(--border2); border-radius: 14px; transition: border-color 0.2s, box-shadow 0.2s; }
.aria-input-wrap:focus-within { border-color: rgba(240,165,0,0.4); box-shadow: 0 0 0 3px rgba(240,165,0,0.06); }
.aria-textarea { width: 100%; background: transparent; border: none; color: var(--text); padding: 11px 14px; font-size: 0.88em; font-family: 'Plus Jakarta Sans', sans-serif; resize: none; outline: none; max-height: 100px; line-height: 1.5; display: block; }
.aria-textarea::placeholder { color: var(--text3); }
.aria-send-btn { width: 42px; height: 42px; background: linear-gradient(135deg,var(--gold),var(--gold2)); border: none; border-radius: 11px; color: #1a0f00; cursor: pointer; font-size: 0.95em; display: flex; align-items: center; justify-content: center; transition: transform 0.15s, box-shadow 0.2s; flex-shrink: 0; box-shadow: 0 4px 14px rgba(240,165,0,0.3); }
.aria-send-btn:hover:not(:disabled) { transform: scale(1.06); box-shadow: 0 6px 20px rgba(240,165,0,0.45); }
.aria-send-btn:disabled { opacity: 0.35; cursor: not-allowed; transform: none; box-shadow: none; }

</style>
</head>
<body>
<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>

<!-- ══ SIDEBAR ══ -->
<aside class="sidebar">
  <div class="sidebar-header">
    <div class="logo">
      <div class="logo-icon">🎓</div>
      <div class="logo-text">Aria</div>
    </div>
    <div class="logo-sub">AI Tutor · British &amp; American</div>
  </div>

  <div class="sidebar-scroll">

    <!-- Curriculum Toggle -->
    <div class="curriculum-toggle">
      <button class="curr-btn active" id="btnBritish" onclick="setCurriculum('british')">🇬🇧 British</button>
      <button class="curr-btn" id="btnAmerican" onclick="setCurriculum('american')">🇺🇸 American</button>
    </div>

    <!-- Year Groups — British (shown by default) -->
    <div id="britishYears">
      <div class="section-label">Early Years &amp; Primary</div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Reception (Age 4–5)', 'british')">🌱 Reception <span class="year-badge">Age 4–5</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Year 1 (Age 5–6)', 'british')">📖 Year 1 <span class="year-badge">Age 5–6</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Year 2 (Age 6–7)', 'british')">📖 Year 2 <span class="year-badge">Age 6–7</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Year 3 (Age 7–8)', 'british')">📖 Year 3 <span class="year-badge">Age 7–8</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Year 4 (Age 8–9)', 'british')">📖 Year 4 <span class="year-badge">Age 8–9</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Year 5 (Age 9–10)', 'british')">📖 Year 5 <span class="year-badge">Age 9–10</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Year 6 (Age 10–11)', 'british')">📖 Year 6 <span class="year-badge">Age 10–11</span></button></div>

      <div class="section-label" style="margin-top:12px">Secondary</div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Year 7 (Age 11–12)', 'british')">🔬 Year 7 <span class="year-badge">Age 11–12</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Year 8 (Age 12–13)', 'british')">🔬 Year 8 <span class="year-badge">Age 12–13</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Year 9 (Age 13–14)', 'british')">🔬 Year 9 <span class="year-badge">Age 13–14</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Year 10 — GCSE (Age 14–15)', 'british')">📝 Year 10 — GCSE <span class="year-badge">Age 14–15</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Year 11 — GCSE (Age 15–16)', 'british')">📝 Year 11 — GCSE <span class="year-badge">Age 15–16</span></button></div>

      <div class="section-label" style="margin-top:12px">Sixth Form</div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Year 12 — AS Level (Age 16–17)', 'british')">⭐ Year 12 — AS Level <span class="year-badge">Age 16–17</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Year 13 — A Level (Age 17–18)', 'british')">⭐ Year 13 — A Level <span class="year-badge">Age 17–18</span></button></div>

      <div class="section-label" style="margin-top:12px">Higher Education</div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Undergraduate Year 1', 'british')">🎓 Undergraduate Y1 <span class="year-badge">Uni</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Undergraduate Year 2', 'british')">🎓 Undergraduate Y2 <span class="year-badge">Uni</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Undergraduate Year 3 / Final Year', 'british')">🎓 Final Year <span class="year-badge">Uni</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Postgraduate / Masters / PhD', 'british')">🔭 Postgraduate <span class="year-badge">PG</span></button></div>
    </div>

    <!-- Year Groups — American (hidden by default) -->
    <div id="americanYears" style="display:none">
      <div class="section-label">Early Childhood</div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Pre-K (Age 4)', 'american')">🌱 Pre-K <span class="year-badge">Age 4</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Kindergarten (Age 5)', 'american')">🌱 Kindergarten <span class="year-badge">Age 5</span></button></div>

      <div class="section-label" style="margin-top:12px">Elementary School</div>
      <div class="year-group"><button class="year-btn" onclick="setYear('1st Grade (Age 6)', 'american')">📖 1st Grade <span class="year-badge">Age 6</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('2nd Grade (Age 7)', 'american')">📖 2nd Grade <span class="year-badge">Age 7</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('3rd Grade (Age 8)', 'american')">📖 3rd Grade <span class="year-badge">Age 8</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('4th Grade (Age 9)', 'american')">📖 4th Grade <span class="year-badge">Age 9</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('5th Grade (Age 10)', 'american')">📖 5th Grade <span class="year-badge">Age 10</span></button></div>

      <div class="section-label" style="margin-top:12px">Middle School</div>
      <div class="year-group"><button class="year-btn" onclick="setYear('6th Grade (Age 11)', 'american')">🔬 6th Grade <span class="year-badge">Age 11</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('7th Grade (Age 12)', 'american')">🔬 7th Grade <span class="year-badge">Age 12</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('8th Grade (Age 13)', 'american')">🔬 8th Grade <span class="year-badge">Age 13</span></button></div>

      <div class="section-label" style="margin-top:12px">High School</div>
      <div class="year-group"><button class="year-btn" onclick="setYear('9th Grade / Freshman (Age 14)', 'american')">📝 9th Grade <span class="year-badge">Age 14</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('10th Grade / Sophomore (Age 15)', 'american')">📝 10th Grade <span class="year-badge">Age 15</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('11th Grade / Junior — SAT / ACT / AP (Age 16)', 'american')">⭐ 11th Grade — AP/SAT <span class="year-badge">Age 16</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('12th Grade / Senior — SAT / AP (Age 17–18)', 'american')">⭐ 12th Grade — AP/SAT <span class="year-badge">Age 17–18</span></button></div>

      <div class="section-label" style="margin-top:12px">Higher Education</div>
      <div class="year-group"><button class="year-btn" onclick="setYear('College Freshman / 1st Year', 'american')">🎓 College Freshman <span class="year-badge">College</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('College Sophomore / 2nd Year', 'american')">🎓 Sophomore <span class="year-badge">College</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('College Junior / 3rd Year', 'american')">🎓 Junior <span class="year-badge">College</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('College Senior / 4th Year', 'american')">🎓 Senior <span class="year-badge">College</span></button></div>
      <div class="year-group"><button class="year-btn" onclick="setYear('Graduate School / Masters / PhD', 'american')">🔭 Graduate School <span class="year-badge">Grad</span></button></div>
    </div>

    <!-- Subjects (always visible) -->
    <div class="subjects-section" id="subjectsSection">
      <div class="section-label" style="margin-top:16px">Subjects</div>
      <div class="subject-grid">
        <button class="subject-btn" onclick="setSubject('Mathematics')"><span class="subject-icon">🧮</span><span class="subject-name">Maths</span></button>
        <button class="subject-btn" onclick="setSubject('English')"><span class="subject-icon">📝</span><span class="subject-name">English</span></button>
        <button class="subject-btn" onclick="setSubject('Science')"><span class="subject-icon">🔬</span><span class="subject-name">Science</span></button>
        <button class="subject-btn" onclick="setSubject('Physics')"><span class="subject-icon">⚛️</span><span class="subject-name">Physics</span></button>
        <button class="subject-btn" onclick="setSubject('Chemistry')"><span class="subject-icon">🧪</span><span class="subject-name">Chemistry</span></button>
        <button class="subject-btn" onclick="setSubject('Biology')"><span class="subject-icon">🧬</span><span class="subject-name">Biology</span></button>
        <button class="subject-btn" onclick="setSubject('History')"><span class="subject-icon">🏛️</span><span class="subject-name">History</span></button>
        <button class="subject-btn" onclick="setSubject('Geography')"><span class="subject-icon">🌍</span><span class="subject-name">Geography</span></button>
        <button class="subject-btn" onclick="setSubject('Computer Science')"><span class="subject-icon">💻</span><span class="subject-name">Computer Sci</span></button>
        <button class="subject-btn" onclick="setSubject('Economics')"><span class="subject-icon">📈</span><span class="subject-name">Economics</span></button>
        <button class="subject-btn" onclick="setSubject('French')"><span class="subject-icon">🇫🇷</span><span class="subject-name">French</span></button>
        <button class="subject-btn" onclick="setSubject('Spanish')"><span class="subject-icon">🇪🇸</span><span class="subject-name">Spanish</span></button>
        <button class="subject-btn" onclick="setSubject('Art & Design')"><span class="subject-icon">🎨</span><span class="subject-name">Art &amp; Design</span></button>
        <button class="subject-btn" onclick="setSubject('Music')"><span class="subject-icon">🎵</span><span class="subject-name">Music</span></button>
        <button class="subject-btn" onclick="setSubject('Psychology')"><span class="subject-icon">🧠</span><span class="subject-name">Psychology</span></button>
        <button class="subject-btn" onclick="setSubject('Philosophy')"><span class="subject-icon">💭</span><span class="subject-name">Philosophy</span></button>
        <button class="subject-btn" onclick="setSubject('Law')"><span class="subject-icon">⚖️</span><span class="subject-name">Law</span></button>
        <button class="subject-btn" onclick="setSubject('Business Studies')"><span class="subject-icon">💼</span><span class="subject-name">Business</span></button>
        <button class="subject-btn" onclick="setSubject('Religious Studies')"><span class="subject-icon">🕊️</span><span class="subject-name">RE / Ethics</span></button>
        <button class="subject-btn" onclick="setSubject('Physical Education')"><span class="subject-icon">🏃</span><span class="subject-name">PE / Sport</span></button>
      </div>
    </div>

  </div>

  <div class="sidebar-footer">
    <button class="clear-btn" onclick="clearChat()">🗑 Clear conversation</button>
  </div>
</aside>

<!-- ══ MAIN ══ -->
<div class="main">

  <div class="topbar">
    <div class="context-pill">
      <div class="dot"></div>
      Aria is ready &nbsp;·&nbsp; <span id="contextLabel">Select a year &amp; subject</span>
    </div>
    <div class="topbar-right">
      <button class="talk-aria-btn" id="talkAriaBtn">Talk to Aria</button>
      <div class="curr-badge british" id="currBadge">🇬🇧 British</div>
    </div>
  </div>

  <div class="messages" id="messages">
    <div class="welcome" id="welcome">
      <div class="welcome-icon">🎓</div>
      <h1>Learn anything with <em>Aria</em></h1>
      <p>Your personal AI tutor for the British and American curriculum — from Reception all the way to university. Pick your year group and subject on the left to get started.</p>
      <div class="step-prompt">
        <span class="arrow">←</span>
        <span>Choose your <strong>year group</strong> and <strong>subject</strong> from the sidebar to begin</span>
      </div>
      <div class="quick-actions">
        <button class="qa-btn" onclick="quickAsk('Explain how to solve a quadratic equation step by step')">📐 Solve quadratics</button>
        <button class="qa-btn" onclick="quickAsk('What are the key themes in Romeo and Juliet?')">📚 Romeo &amp; Juliet themes</button>
        <button class="qa-btn" onclick="quickAsk('Explain photosynthesis simply')">🌿 Photosynthesis</button>
        <button class="qa-btn" onclick="quickAsk('Give me 5 practice questions on World War 2')">🏛️ WW2 practice quiz</button>
        <button class="qa-btn" onclick="quickAsk('What is the difference between mitosis and meiosis?')">🧬 Mitosis vs Meiosis</button>
        <button class="qa-btn" onclick="quickAsk('Help me understand supply and demand')">📈 Supply &amp; demand</button>
      </div>
    </div>
  </div>

  <div class="input-section">
    <div class="input-row">
      <div class="input-wrap">
        <textarea id="input" placeholder="Ask Aria anything educational..." rows="1"
          onkeydown="handleKey(event)"
          oninput="autoResize(this)"></textarea>
      </div>
      <button class="send-btn" id="sendBtn" onclick="sendMessage()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      </button>
    </div>
    <div class="input-hint">Enter to send &nbsp;·&nbsp; Shift+Enter for new line</div>
  </div>

</div>

<script>
  let isTyping = false;
  let currentYear = '';
  let currentSubject = '';
  let currentCurriculum = 'british';

  function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 130) + 'px';
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function setCurriculum(c) {
    currentCurriculum = c;
    document.getElementById('btnBritish').classList.toggle('active', c === 'british');
    document.getElementById('btnAmerican').classList.toggle('active', c === 'american');
    document.getElementById('britishYears').style.display = c === 'british' ? 'block' : 'none';
    document.getElementById('americanYears').style.display = c === 'american' ? 'block' : 'none';
    const badge = document.getElementById('currBadge');
    badge.textContent = c === 'british' ? '\uD83C\uDDEC\uD83C\uDDE7 British' : '\uD83C\uDDFA\uD83C\uDDF8 American';
    badge.className = 'curr-badge ' + c;
    currentYear = '';
    document.querySelectorAll('.year-btn').forEach(function(b){ b.classList.remove('active'); });
    updateContextLabel();
  }

  function setYear(y, curriculum) {
    currentYear = y;
    document.querySelectorAll('.year-btn').forEach(function(b){
      b.classList.toggle('active', b.textContent.trim().startsWith(y.split(' ')[0]) && b.getAttribute('onclick') && b.getAttribute('onclick').indexOf(y) !== -1);
    });
    updateContextLabel();
    updatePlaceholder();
  }

  function setSubject(s) {
    currentSubject = s;
    document.querySelectorAll('.subject-btn').forEach(function(b){
      b.classList.toggle('active', b.getAttribute('onclick') === "setSubject('" + s + "')");
    });
    updateContextLabel();
    updatePlaceholder();
  }

  function updateContextLabel() {
    var parts = [];
    if (currentYear) parts.push(currentYear);
    if (currentSubject) parts.push(currentSubject);
    document.getElementById('contextLabel').textContent = parts.length ? parts.join(' · ') : 'Select a year & subject';
  }

  function updatePlaceholder() {
    var pl = 'Ask Aria anything educational...';
    if (currentYear && currentSubject) pl = 'Ask about ' + currentSubject + ' for ' + currentYear + '...';
    else if (currentSubject) pl = 'Ask about ' + currentSubject + '...';
    else if (currentYear) pl = 'Ask anything for ' + currentYear + '...';
    document.getElementById('input').placeholder = pl;
  }

  function quickAsk(text) {
    document.getElementById('input').value = text;
    sendMessage();
  }

  function clearChat() {
    if (confirm('Clear the entire conversation? This cannot be undone.')) {
      fetch('/clear', { method: 'POST' }).then(function(){ location.reload(); });
    }
  }

  function renderMarkdown(text) {
    var s = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    // fenced code blocks
    s = s.replace(/```([a-zA-Z0-9]*)[\r]?[\n]([\s\S]*?)```/g, function(_,lang,code){
      return '<pre><code>' + code.replace(/^\n+|\n+$/g,'') + '</code></pre>';
    });
    // inline code
    s = s.replace(/`([^`\n]+)`/g, '<code>$1</code>');
    // h3
    s = s.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    // bold
    s = s.replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>');
    // italic
    s = s.replace(/(?<!\*)\*(?!\*)([^*\n]+)(?<!\*)\*(?!\*)/g, '<em>$1</em>');
    // blockquote
    s = s.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
    // bullet lists
    s = s.replace(/((?:^[ \t]*[-*] .+(?:\n|$))+)/gm, function(block){
      var items = block.trim().split('\n').map(function(line){
        return '<li>' + line.replace(/^[ \t]*[-*] /,'') + '</li>';
      });
      return '<ul>' + items.join('') + '</ul>';
    });
    // numbered lists
    s = s.replace(/((?:^[ \t]*\d+\. .+(?:\n|$))+)/gm, function(block){
      var items = block.trim().split('\n').map(function(line){
        return '<li>' + line.replace(/^[ \t]*\d+\. /,'') + '</li>';
      });
      return '<ol>' + items.join('') + '</ol>';
    });
    // paragraphs
    var parts = s.split(/\n{2,}/);
    s = parts.map(function(p){
      p = p.trim();
      if (!p) return '';
      if (/^<(ul|ol|pre|h3|blockquote)/.test(p)) return p;
      p = p.replace(/\n/g,'<br>');
      return '<p>' + p + '</p>';
    }).filter(Boolean).join('');
    return s;
  }

  function removeWelcome() {
    var w = document.getElementById('welcome');
    if (w) w.remove();
  }

  function addMessage(text, role) {
    removeWelcome();
    var msgs = document.getElementById('messages');
    var wrap = document.createElement('div');
    wrap.className = 'message ' + role;

    var av = document.createElement('div');
    av.className = 'msg-avatar';
    av.textContent = role === 'aria' ? '\u2728' : '\uD83D\uDC64';

    var col = document.createElement('div');
    col.className = 'bubble-col';

    if (role === 'aria' && currentSubject) {
      var tag = document.createElement('div');
      tag.className = 'bubble-tag';
      tag.textContent = currentSubject + (currentYear ? '  \u00B7  ' + currentYear : '');
      col.appendChild(tag);
    }

    var bubble = document.createElement('div');
    bubble.className = 'bubble';
    if (role === 'aria') {
      bubble.innerHTML = renderMarkdown(text);
    } else {
      bubble.innerHTML = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
    }

    col.appendChild(bubble);
    wrap.appendChild(av);
    wrap.appendChild(col);
    msgs.appendChild(wrap);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function showTyping() {
    removeWelcome();
    var msgs = document.getElementById('messages');
    var row = document.createElement('div');
    row.className = 'typing-row';
    row.id = 'typing';
    row.innerHTML = '<div class="typing-avatar">\u2728</div><div class="typing-bubble"><div class="tdot"></div><div class="tdot"></div><div class="tdot"></div></div>';
    msgs.appendChild(row);
    msgs.scrollTop = msgs.scrollHeight;
  }

  function removeTyping() {
    var t = document.getElementById('typing');
    if (t) t.remove();
  }

  async function sendMessage() {
    if (isTyping) return;
    var input = document.getElementById('input');
    var text = input.value.trim();
    if (!text) return;

    input.value = '';
    input.style.height = 'auto';
    isTyping = true;
    document.getElementById('sendBtn').disabled = true;

    addMessage(text, 'user');
    showTyping();

    var context = '';
    if (currentYear || currentSubject || currentCurriculum) {
      context = '[Context: Curriculum=' + (currentCurriculum === 'british' ? 'British' : 'American') +
                (currentYear ? ', Year=' + currentYear : '') +
                (currentSubject ? ', Subject=' + currentSubject : '') + '] ';
    }

    try {
      var res = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: context + text })
      });
      var data = await res.json();
      removeTyping();
      addMessage(data.reply, 'aria');
    } catch(e) {
      removeTyping();
      addMessage('Something went wrong. Make sure Aria is running!', 'aria');
    }

    isTyping = false;
    document.getElementById('sendBtn').disabled = false;
    input.focus();
  }

// ARIA TALK MODAL
var ariaIsBusy = false;

function openAriaModal() {
  document.getElementById('ariaOverlay').classList.add('open');
  setTimeout(function(){ document.getElementById('ariaInput').focus(); }, 100);
  if (document.getElementById('ariaChat').children.length === 0) {
    ariaAddMsg("Hey! I'm Aria, your personal tutor. What would you like to learn today?", 'aria');
  }
}

function closeAriaModal() {
  document.getElementById('ariaOverlay').classList.remove('open');
  if (window.speechSynthesis) window.speechSynthesis.cancel();
  setAriaSpeaking(false);
}

function setAriaSpeaking(on) {
  var ring = document.getElementById('ariaPhotoRing');
  var bars = document.getElementById('ariaSoundBars');
  var status = document.getElementById('ariaStatus');
  if (on) {
    ring.classList.add('speaking');
    bars.classList.add('active');
    status.textContent = 'Speaking...';
    status.className = 'aria-status speaking';
  } else {
    ring.classList.remove('speaking');
    bars.classList.remove('active');
    status.textContent = 'Ready to help you learn';
    status.className = 'aria-status';
  }
}

function ariaSpeak(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  var clean = text.replace(/\*\*([^*]+)\*\*/g,'$1').replace(/\*([^*]+)\*/g,'$1')
                  .replace(/`([^`]+)`/g,'$1').replace(/#+\s/g,'').replace(/\n/g,' ').trim();
  var utter = new SpeechSynthesisUtterance(clean);
  utter.rate = 1.05;
  utter.pitch = 1.15;
  var voices = window.speechSynthesis.getVoices();
  var preferred = ['Samantha','Aria','Zira','Google UK English Female','Karen','Moira'];
  for (var i = 0; i < preferred.length; i++) {
    var match = voices.find(function(v){ return v.name.indexOf(preferred[i]) !== -1; });
    if (match) { utter.voice = match; break; }
  }
  utter.onstart = function(){ setAriaSpeaking(true); };
  utter.onend = function(){ setAriaSpeaking(false); };
  utter.onerror = function(){ setAriaSpeaking(false); };
  window.speechSynthesis.speak(utter);
}

function ariaAddMsg(text, role) {
  var chat = document.getElementById('ariaChat');
  var div = document.createElement('div');
  div.className = 'aria-msg ' + role;
  var bubble = document.createElement('div');
  bubble.className = 'aria-msg-bubble';
  bubble.textContent = text;
  div.appendChild(bubble);
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function ariaShowTyping() {
  var chat = document.getElementById('ariaChat');
  var div = document.createElement('div');
  div.className = 'aria-msg aria';
  div.id = 'ariaTyping';
  div.innerHTML = '<div class="aria-typing-bubble"><div class="tdot"></div><div class="tdot"></div><div class="tdot"></div></div>';
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function ariaRemoveTyping() {
  var t = document.getElementById('ariaTyping');
  if (t) t.remove();
}

async function ariaSendMessage() {
  if (ariaIsBusy) return;
  var input = document.getElementById('ariaInput');
  var text = input.value.trim();
  if (!text) return;
  input.value = '';
  input.style.height = 'auto';
  ariaIsBusy = true;
  document.getElementById('ariaSendBtn').disabled = true;
  ariaAddMsg(text, 'user');
  ariaShowTyping();
  var ctx = '';
  if (typeof currentCurriculum !== 'undefined') {
    ctx = '[Context: Curriculum=' + (currentCurriculum === 'british' ? 'British' : 'American') +
          (currentYear ? ', Year=' + currentYear : '') +
          (currentSubject ? ', Subject=' + currentSubject : '') + '] ';
  }
  try {
    var res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({message: ctx + text})
    });
    var data = await res.json();
    ariaRemoveTyping();
    ariaAddMsg(data.reply, 'aria');
    ariaSpeak(data.reply);
  } catch(e) {
    ariaRemoveTyping();
    ariaAddMsg('Oops! Something went wrong. Make sure Aria is running!', 'aria');
  }
  ariaIsBusy = false;
  document.getElementById('ariaSendBtn').disabled = false;
  document.getElementById('ariaInput').focus();
}

document.addEventListener('DOMContentLoaded', function() {
  document.getElementById('talkAriaBtn').addEventListener('click', openAriaModal);
  document.getElementById('ariaCloseBtn').addEventListener('click', closeAriaModal);
  document.getElementById('ariaSendBtn').addEventListener('click', ariaSendMessage);
  document.getElementById('ariaInput').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ariaSendMessage(); }
  });
  document.getElementById('ariaInput').addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 100) + 'px';
  });
  document.getElementById('ariaOverlay').addEventListener('click', function(e) {
    if (e.target === this) closeAriaModal();
  });
  if (window.speechSynthesis) {
    window.speechSynthesis.getVoices();
    window.speechSynthesis.addEventListener('voiceschanged', function(){ window.speechSynthesis.getVoices(); });
  }
});

</script>

<!-- ARIA TALK MODAL -->
<div class="aria-overlay" id="ariaOverlay">
  <div class="aria-modal">
    <div class="aria-modal-header">
      <div class="aria-modal-title">Talk to Aria</div>
      <button class="aria-close-btn" id="ariaCloseBtn">x</button>
    </div>
    <div class="aria-face-area">
      <div class="aria-photo-ring" id="ariaPhotoRing">
        <img class="aria-photo" src="data:image/jpeg;base64,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" alt="Aria">
      </div>
      <div class="aria-sound-bars" id="ariaSoundBars">
        <div class="sbar"></div><div class="sbar"></div><div class="sbar"></div>
        <div class="sbar"></div><div class="sbar"></div><div class="sbar"></div>
        <div class="sbar"></div>
      </div>
      <div class="aria-status" id="ariaStatus">Ready to help you learn</div>
    </div>
    <div class="aria-chat" id="ariaChat"></div>
    <div class="aria-input-area">
      <div class="aria-input-wrap">
        <textarea class="aria-textarea" id="ariaInput" placeholder="Type your question..." rows="1"></textarea>
      </div>
      <button class="aria-send-btn" id="ariaSendBtn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      </button>
    </div>
  </div>
</div>

</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())

    def do_POST(self):
        global messages
        length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(length))

        if self.path == '/clear':
            messages = []
            save_memory(messages)
            self.send_response(200)
            self.end_headers()
            return

        if self.path == '/chat':
            user_input = body.get('message', '')
            messages.append({"role": "user", "content": user_input})

            try:
                response = ollama.chat(
                    model="llama3.2",
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages
                )
                reply = response["message"]["content"]
            except Exception as e:
                reply = f"Error talking to Ollama: {str(e)}"

            messages.append({"role": "assistant", "content": reply})
            save_memory(messages)

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"reply": reply}).encode())

PORT = 7860
print(f"\n🎓 Aria Tutor is running! Open this in your browser: http://127.0.0.1:{PORT}\n")
threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()
HTTPServer(('127.0.0.1', PORT), Handler).serve_forever()