import os, json, base64, datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

CLIENT_ID     = os.environ["ANBIMA_CLIENT_ID"]
CLIENT_SECRET = os.environ["ANBIMA_CLIENT_SECRET"]

AMBIENTE = "producao"
BASE_URL = (
    "https://api.anbima.com.br"
    if AMBIENTE == "producao"
    else "https://api.sandbox.anbima.com.br"
)

def get_token():
    creds = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

    # Tenta formato form-urlencoded (padrão OAuth2 correto)
    payload = urlencode({"grant_type": "client_credentials"}).encode()
    req = Request(
        f"{BASE_URL}/oauth/access-token",
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {creds}"
        }
    )
    try:
        with urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
            print(f"  Token obtido. Expira em: {resp.get('expires_in', '?')}s")
            return resp["access_token"]
    except HTTPError as e:
        # Lê o corpo do erro para diagnóstico
        body = e.read().decode("utf-8", errors="ignore")
        print(f"  Falha no token — HTTP {e.code}: {e.reason}")
        print(f"  Resposta do servidor: {body[:500]}")
        raise

def anbima_get(token, path):
    url = f"{BASE_URL}/feed/precos-indices/v1/titulos-publicos/{path}"
    print(f"  → GET {path} ...", end=" ", flush=True)
    req = Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            print("OK")
            return data
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print(f"FALHOU — HTTP {e.code}: {e.reason} | {body[:200]}")
        return None
    except URLError as e:
        print(f"FALHOU — {e.reason}")
        return None

def fetch_all():
    print(f"Obtendo token ANBIMA ({AMBIENTE})...")
    token = get_token()
    print(f"Token OK.\n")

    data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "data_referencia": None,
        "ambiente": AMBIENTE,
    }

    endpoints = [
        "curvas-juros",
        "mercado-secundario-TPF",
        "vna",
        "estimativa-selic",
    ]

    for ep in endpoints:
        resultado = anbima_get(token, ep)
        if resultado:
            chave = ep.replace("-", "_").replace("/", "_")
            data[chave] = resultado
            if not data["data_referencia"]:
                if isinstance(resultado, list) and resultado:
                    data["data_referencia"] = (
                        resultado[0].get("DataReferencia")
                        or resultado[0].get("data_referencia")
                    )
                elif isinstance(resultado, dict):
                    data["data_referencia"] = (
                        resultado.get("DataReferencia")
                        or resultado.get("data_referencia")
                    )

    ok  = [ep for ep in endpoints if ep.replace("-","_") in data]
    nok = [ep for ep in endpoints if ep.replace("-","_") not in data]
    print(f"\n✓ OK:     {ok}")
    if nok:
        print(f"✗ Falhos: {nok}")

    return data

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    result = fetch_all()

    today       = datetime.date.today().strftime("%Y-%m-%d")
    path_today  = f"data/anbima_{today}.json"
    path_latest = "data/anbima_latest.json"

    with open(path_today,  "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    with open(path_latest, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Salvo: {path_today}")
    print(f"✓ Latest: {path_latest}")
    if result.get("data_referencia"):
        print(f"  Referência: {result['data_referencia']}")
