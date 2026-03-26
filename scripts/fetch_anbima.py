import os, json, base64, datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

CLIENT_ID     = os.environ["ANBIMA_CLIENT_ID"]
CLIENT_SECRET = os.environ["ANBIMA_CLIENT_SECRET"]

TOKEN_URL  = "https://api.anbima.com.br/oauth/access-token"
API_URL    = "https://api-sandbox.anbima.com.br"

def get_token():
    creds   = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    payload = urlencode({"grant_type": "client_credentials"}).encode()
    req = Request(
        TOKEN_URL,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {creds}"
        }
    )
    with urlopen(req, timeout=15) as r:
        resp = json.loads(r.read())
        print(f"  Token OK. Expira em {resp.get('expires_in','?')}s")
        return resp["access_token"]

def anbima_get(token, path):
    url = f"{API_URL}/feed/precos-indices/v1/titulos-publicos/{path}"
    print(f"\n  GET {path}")
    req = Request(url, headers={
        "access_token": token,
        "client_id":    CLIENT_ID,
        "Accept":       "application/json"
    })
    try:
        with urlopen(req, timeout=15) as r:
            raw  = r.read()
            data = json.loads(raw)
            preview = json.dumps(data, ensure_ascii=False)[:300]
            print(f"  OK: {preview}")
            return data
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"  FALHOU HTTP {e.code}: {e.reason} | {body[:300]}")
        return None
    except URLError as e:
        print(f"  FALHOU URLError: {e.reason}")
        return None

def fetch_all():
    print("Obtendo token...")
    token = get_token()
    data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z
