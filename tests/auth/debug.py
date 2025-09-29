#!/usr/bin/env python3
"""
Simple E2E: register -> get email -> extract token -> verify

ENV (défauts entre crochets):
  BASE_URL                [http://localhost:8000]
  EP_REGISTER             [/auth/register]
  EP_VERIFY               [/auth/verify-email]           # GET ?token=... ou POST {"token": "..."}
  EP_DEV_TOKEN            [/auth/dev/verification-token] # mode DEV: GET ?email=...
  EMAIL_MODE              [dev]   # dev | imap

# Mode DEV (plus simple, pas d'IMAP) :
  # rien d'autre à configurer

# Mode IMAP (lire un vrai email) :
  IMAP_HOST               (ex: imap.gmail.com)
  IMAP_PORT               [993]
  IMAP_USER               (ex: test@example.com)
  IMAP_PASS               (mot de passe/app password)
  IMAP_FOLDER             [INBOX]
  IMAP_SUBJECT_FILTER     [Verify|Verification|Confirm]   # regex pour filtrer
  IMAP_FROM_FILTER        []                              # optionnel, regex sur expéditeur

Notes:
- Gmail: activer un "App password" si 2FA.
- Le script essaye d'abord GET /verify-email?token=..., puis POST JSON si besoin.
"""

import os, re, time, uuid, json, email, imaplib, requests
from email.header import decode_header

BASE_URL   = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
EP_REGISTER= os.getenv("EP_REGISTER", "/auth/register")
EP_VERIFY  = os.getenv("EP_VERIFY", "/auth/verify-email")
EP_DEV_TOK = os.getenv("EP_DEV_TOKEN", "/auth/verification-token")
EMAIL_MODE = os.getenv("EMAIL_MODE", "dev").lower()

HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

def U(p): return f"{BASE_URL}{p}"

def jprint(resp):
    try: print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except: print(resp.text)

def register(email_addr, password):
    payload = {
        "email": email_addr, "password": password,
        "first_name": "John", "last_name": "Doe", "phone": "+1226667890"
    }
    r = requests.post(U(EP_REGISTER), json=payload, headers=HEADERS, timeout=15)
    if r.status_code in (200,201,202):
        print("✅ Registered")
    elif r.status_code in (400,409) and "exist" in r.text.lower():
        print("ℹ️ Already registered, continue.")
    else:
        print("❌ Register failed:", r.status_code); jprint(r); raise SystemExit(1)
    return r

# ====== MODE DEV: endpoint qui retourne le token ======
def get_token_dev(email_addr):
    r = requests.get(U(EP_DEV_TOK), params={"email": email_addr}, timeout=15)
    if r.status_code != 200:
        print("❌ Dev token endpoint failed:", r.status_code); jprint(r); return None
    try:
        data = r.json()
        tok = data.get("token")
        if not tok:
            m = re.search(r'"token"\s*:\s*"([^"]+)"', r.text)
            tok = m.group(1) if m else None
        print("✅ Token (dev) récupéré")
        return tok
    except Exception:
        print("❌ Dev token parse error"); return None

# ====== MODE IMAP: lire le mail et extraire le token ======
def _decode(s):
    parts = decode_header(s)
    out = ""
    for val, enc in parts:
        if isinstance(val, bytes): out += val.decode(enc or "utf-8", errors="replace")
        else: out += val
    return out

def fetch_latest_verification_email():
    host = os.getenv("IMAP_HOST"); port = int(os.getenv("IMAP_PORT", "993"))
    user = os.getenv("IMAP_USER");  pwd  = os.getenv("IMAP_PASS")
    folder = os.getenv("IMAP_FOLDER", "INBOX")
    subj_re = os.getenv("IMAP_SUBJECT_FILTER", r"Verify|Verification|Confirm")
    from_re = os.getenv("IMAP_FROM_FILTER")  # optionnel

    if not all([host, user, pwd]):
        print("❌ IMAP config manquante (IMAP_HOST/IMAP_USER/IMAP_PASS)"); return None

    M = imaplib.IMAP4_SSL(host, port)
    M.login(user, pwd)
    M.select(folder)
    # Cherche les 20 derniers, puis filtre en Python (souvent plus simple)
    typ, data = M.search(None, "ALL")
    if typ != "OK" or not data or not data[0]:
        print("❌ IMAP: pas d'emails"); return None
    ids = data[0].split()[-20:]

    subj_pat = re.compile(subj_re, re.I)
    from_pat = re.compile(from_re, re.I) if from_re else None

    for eid in reversed(ids):  # du plus récent au plus ancien
        typ, msg_data = M.fetch(eid, "(RFC822)")
        if typ != "OK": continue
        msg = email.message_from_bytes(msg_data[0][1])
        subj = _decode(msg.get("Subject", ""))
        frm  = _decode(msg.get("From", ""))

        if not subj_pat.search(subj):
            continue
        if from_pat and not from_pat.search(frm):
            continue

        # Récupère le corps (texte + html)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                ctype = part.get_content_type()
                if ctype in ("text/html","text/plain"):
                    try:
                        body += part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8","replace")
                    except: pass
        else:
            try:
                body = msg.get_payload(decode=True).decode(msg.get_content_charset() or "utf-8","replace")
            except:
                body = str(msg.get_payload())

        M.logout()
        print(f"✅ Email trouvé: From={frm} | Subject={subj}")
        return body

    M.logout()
    print("❌ Aucun email de vérification correspondant")
    return None

def extract_token_from_text(txt):
    # Tente plusieurs patterns usuels
    for pat in [
        r'[?&]token=([A-Za-z0-9._\-]+)',
        r'"token"\s*:\s*"([^"]+)"',
        r'token=([A-Za-z0-9._\-]+)'
    ]:
        m = re.search(pat, txt)
        if m: return m.group(1)
    return None

def verify_token(token):
    # Essaye GET ?token=... puis POST JSON
    r = requests.get(U(EP_VERIFY), params={"token": token}, timeout=15)
    if r.status_code in (200,204):
        print("✅ Verify (GET) OK"); return True
    r = requests.post(U(EP_VERIFY), json={"token": token}, timeout=15)
    if r.status_code in (200,204):
        print("✅ Verify (POST) OK"); return True
    print("❌ Verify failed:", r.status_code); jprint(r); return False

def main():
    email_addr = f"test+{uuid.uuid4().hex[:6]}@example.com"
    password   = "TestPassword123!"

    print("➡️  Registering user:", email_addr)
    register(email_addr, password)

    if EMAIL_MODE == "dev":
        print("➡️  Mode DEV: récupération du token via endpoint")
        token = get_token_dev(email_addr)
        if not token: raise SystemExit("Token introuvable en mode DEV.")
    else:
        print("➡️  Mode IMAP: lecture de la boîte mail")
        print("   Attente de l’email (jusqu’à 30s)…")
        body = None
        for _ in range(6):  # 6 * 5s = 30s
            time.sleep(5)
            body = fetch_latest_verification_email()
            if body: break
        if not body: raise SystemExit("Email de vérification non trouvé.")
        token = extract_token_from_text(body)
        if not token: raise SystemExit("Token introuvable dans l’email.")

    print("➡️  Vérification avec token:", token[:24] + "…")
    ok = verify_token(token)
    if not ok: raise SystemExit(1)

    print("🎉 Terminé : utilisateur vérifié.")

if __name__ == "__main__":
    main()
