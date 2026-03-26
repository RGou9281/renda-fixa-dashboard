import os, json, base64, datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

CLIENT_ID     = os.environ["ANBIMA_CLIENT_ID"]
CLIENT_SECRET = os.environ["ANBIMA_CLIENT_SECRET"]

def get_token():
    creds   = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    payload = b'{"grant_type":"client_credentials"}'
    req = Request(
        "https://api.anbima.com.br/oauth/access-token",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Basic {creds}"}
    )
    with urlopen(req, timeout=15) as r:
        return json.loads(r.read())["access_token"]

def anbima_get(token, path):
    url = f"https://api.anbima.com.br/feed/precos-indices/v1/titulos-publicos/{path}"
    req = Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except URLError as e:
        print(f"  Aviso: {path} falhou — {e}")
        return None

def fetch_all():
    print("Obtendo token ANBIMA...")
    token = get_token()
    print("Token OK. Buscando dados...")

    data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "data_referencia": None,
    }

    curvas = anbima_get(token, "curvas-juros")
    if curvas:
        data["curvas_juros"] = curvas
        if isinstance(curvas, list) and curvas:
            data["data_referencia"] = curvas[0].get("DataReferencia")
        elif isinstance(curvas, dict):
            data["data_referencia"] = curvas.get("DataReferencia")

    mercado = anbima_get(token, "mercado-secundario-TPF")
    if mercado:
        data["mercado_secundario"] = mercado

    vna = anbima_get(token, "vna")
    if vna:
        data["vna"] = vna

    selic_est = anbima_get(token, "estimativa-selic")
    if selic_est:
        data["estimativa_selic"] = selic_est

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

    print(f"✓ Salvo em {path_today}")
    print(f"✓ Atualizado {path_latest}")
    if result.get("data_referencia"):
        print(f"  Data de referência: {result['data_referencia']}")
