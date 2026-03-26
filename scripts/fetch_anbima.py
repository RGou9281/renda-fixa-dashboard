import os, json, base64, datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

CLIENT_ID     = os.environ["ANBIMA_CLIENT_ID"]
CLIENT_SECRET = os.environ["ANBIMA_CLIENT_SECRET"]

# Troque para "sandbox" se quiser testar sem aprovação
AMBIENTE = "producao"
BASE_URL = (
    "https://api.anbima.com.br"
    if AMBIENTE == "producao"
    else "https://api.sandbox.anbima.com.br"
)

def get_token():
    creds   = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    payload = b'{"grant_type":"client_credentials"}'
    req = Request(
        f"{BASE_URL}/oauth/access-token",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Basic {creds}"}
    )
    with urlopen(req, timeout=15) as r:
        return json.loads(r.read())["access_token"]

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
        print(f"FALHOU — HTTP {e.code}: {e.reason}")
        return None
    except URLError as e:
        print(f"FALHOU — {e.reason}")
        return None

def fetch_all():
    print("Obtendo token ANBIMA...")
    token = get_token()
    print(f"Token OK. Ambiente: {AMBIENTE}\n")

    data = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "data_referencia": None,
        "ambiente": AMBIENTE,
    }

    # Testa cada endpoint individualmente
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
            # Tenta extrair data de referência do primeiro endpoint bem-sucedido
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

    # Resumo
    ok  = [ep for ep in endpoints if ep.replace("-","_").replace("/","_") in data]
    nok = [ep for ep in endpoints if ep.replace("-","_").replace("/","_") not in data]
    print(f"\n✓ Endpoints OK:     {ok}")
    if nok:
        print(f"✗ Endpoints falhos: {nok}")

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

    print(f"\n✓ Salvo em: {path_today}")
    print(f"✓ Atualizado: {path_latest}")
    if result.get("data_referencia"):
        print(f"  Data de referência: {result['data_referencia']}")
    else:
        print("  Atenção: nenhuma data de referência encontrada nos dados")
