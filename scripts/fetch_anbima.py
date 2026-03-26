import os
import json
import base64
import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlencode

CLIENT_ID = os.environ["ANBIMA_CLIENT_ID"]
CLIENT_SECRET = os.environ["ANBIMA_CLIENT_SECRET"]
TOKEN_URL = "https://api.anbima.com.br/oauth/access-token"
API_URL = "https://api-sandbox.anbima.com.br"


def get_token():
    creds = base64.b64encode(
        f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    ).decode()
    payload = urlencode({"grant_type": "client_credentials"}).encode()
    req = Request(
        TOKEN_URL,
        data=payload,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + creds,
        },
    )
    with urlopen(req, timeout=15) as r:
        resp = json.loads(r.read())
        print("Token OK. Expira em " + str(resp.get("expires_in", "?")) + "s")
        return resp["access_token"]


def anbima_get(token, path):
    url = API_URL + "/feed/precos-indices/v1/titulos-publicos/" + path
    print("GET " + path)
    req = Request(
        url,
        headers={
            "access_token": token,
            "client_id": CLIENT_ID,
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            preview = json.dumps(data, ensure_ascii=False)[:200]
            print("OK: " + preview)
            return data
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        print("FALHOU HTTP " + str(e.code) + ": " + body[:200])
        return None
    except URLError as e:
        print("FALHOU URLError: " + str(e.reason))
        return None


def fetch_all():
    print("Obtendo token...")
    token = get_token()
    now = datetime.datetime.utcnow().isoformat() + "Z"
    data = {
        "timestamp": now,
        "data_referencia": None,
        "ambiente": "sandbox",
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
            chave = ep.replace("-", "_")
            data[chave] = resultado
            if not data["data_referencia"]:
                ref = None
                if isinstance(resultado, list) and len(resultado) > 0:
                    ref = resultado[0].get("DataReferencia")
                elif isinstance(resultado, dict):
                    ref = resultado.get("DataReferencia")
                if ref:
                    data["data_referencia"] = ref
    return data


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    result = fetch_all()
    today = datetime.date.today().strftime("%Y-%m-%d")
    path1 = "data/anbima_" + today + ".json"
    path2 = "data/anbima_latest.json"
    with open(path1, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    with open(path2, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("Salvo: " + path1)
    print("Referencia: " + str(result.get("data_referencia", "nenhuma")))
