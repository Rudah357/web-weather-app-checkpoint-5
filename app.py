from flask import Flask, render_template, request
import requests
import json
import os
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
API_KEY = "COLOCAR_SUA_KEY"

HISTORICO_FILE = "historico.json"

def carregar_historico():
    if os.path.exists(HISTORICO_FILE):
        try:
            with open(HISTORICO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def salvar_historico(cidade):
    historico = carregar_historico()
    
    if cidade in historico:
        historico.remove(cidade)
        
    historico.insert(0, city_name := cidade)
    historico = historico[:3]
    
    with open(HISTORICO_FILE, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=4)

def formatar_timestamp(timestamp, timezone_offset):

    hora_utc = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    hora_local = hora_utc + timedelta(seconds=timezone_offset)
    return hora_local.strftime("%H:%M")

@app.route("/", methods=["GET", "POST"])
def index():
    clima = None
    erro = None
    estado = None
    dados_extras = {}

    if request.method == "POST":
        cidade = request.form.get("cidade")
        if cidade:

            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={cidade}&limit=1&appid={API_KEY}"
            try:
                geo_resposta = requests.get(geo_url)
                if geo_resposta.status_code == 200 and len(geo_resposta.json()) > 0:
                    geo_dados = geo_resposta.json()[0]
                    estado = geo_dados.get('state') 
                    lat = geo_dados['lat']
                    lon = geo_dados['lon']
                    
                    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=pt_br"
                    resposta = requests.get(url)
                    
                    if resposta.status_code == 200:
                        clima = resposta.json()
                        
                        salvar_historico(clima['name'])
                        
                        offset = clima.get('timezone', 0)
                        sunrise_unix = clima['sys']['sunrise']
                        sunset_unix = clima['sys']['sunset']
                        
                        dados_extras['sunrise'] = formatar_timestamp(sunrise_unix, offset)
                        dados_extras['sunset'] = formatar_timestamp(sunset_unix, offset)
                        
                    else:
                        erro = "Não foi possível obter os dados do clima."
                else:
                    erro = "Cidade não encontrada! Tente novamente."
            except requests.exceptions.RequestException:
                erro = "Não foi possível conectar ao servidor de clima."

    historico = carregar_historico()
    return render_template("index.html", clima=clima, erro=erro, estado=estado, extras=dados_extras, historico=historico)

if __name__ == "__main__":
    app.run(debug=True)