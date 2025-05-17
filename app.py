from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
import os
from datetime import datetime

# -------------------- CONFIGURAÇÃO INICIAL -------------------- #
app = Flask(__name__)
app.secret_key = 'segredo_super_secreto'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
CHAMADOS_DIR = os.path.join(BASE_DIR, 'chamados')
USUARIOS_PATH = os.path.join(BASE_DIR, 'usuarios.txt')
LOG_PATH = os.path.join(BASE_DIR, 'logs_acesso.txt')
LINHAS = ["lm04", "lm06", "lm08", "lm10", "lm12"]

# -------------------- FUNÇÕES AUXILIARES -------------------- #
def ler_usuarios():
    usuarios = []
    if os.path.exists(USUARIOS_PATH):
        with open(USUARIOS_PATH, 'r', encoding='utf-8') as f:
            for linha in f:
                partes = linha.strip().split(';')
                if len(partes) == 2:
                    usuarios.append((partes[0], 'comum'))
                elif len(partes) == 3:
                    usuarios.append((partes[0], partes[2]))
    return usuarios

def escrever_usuario(nome, senha, tipo):
    with open(USUARIOS_PATH, 'a', encoding='utf-8') as f:
        f.write(f"{nome};{senha};{tipo}\n")

def salvar_log(mensagem):
    data = datetime.now().strftime('%d/%m/%Y %H:%M')
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f"[{data}] {mensagem}\n")

# -------------------- ABRIR CHAMADO -------------------- #
@app.route('/abrir_chamado', methods=['GET', 'POST'])
def abrir_chamado():
    mensagem = ""
    if request.method == 'POST':
        operador = request.form['operador']
        linha = request.form['linha']
        problema = request.form['problema']
        data = datetime.now().strftime("%Y-%m-%d")
        hora = datetime.now().strftime("%H:%M:%S")
        data_humano = datetime.now().strftime("%d-%m-%Y")

        pasta_linha = os.path.join(CHAMADOS_DIR, linha)
        os.makedirs(pasta_linha, exist_ok=True)
        caminho = os.path.join(pasta_linha, f"{data}.txt")

        numero = 1
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                for linha_txt in f:
                    if "#Pedido de Suporte#" in linha_txt:
                        numero += 1

        with open(caminho, 'a', encoding='utf-8') as f:
            f.write(f"#Pedido de Suporte# {numero}\n")
            f.write(f"Data: {data_humano}\n")
            f.write(f"Hora: {hora}\n")
            f.write(f"Operador: {operador}\n")
            f.write(f"Problema: {problema}\n")
            f.write("Status Atual=aberto\n")
            f.write("Técnico Atuante=-\n")
            f.write("Solução=-\n")
            f.write("Fechado em: -\n\n")

        salvar_log(f"Chamado #{numero} ABERTO por {operador} na linha {linha}")
        mensagem = f"Chamado #{numero} aberto com sucesso!"

    return render_template('abrir_chamado.html', mensagem=mensagem)

@app.route('/visualizar_linhas')
def visualizar_linhas():
    return render_template('visualizar_linhas.html')


# -------------------- LOGIN -------------------- #
@app.route('/')
def index():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('fechar_chamado'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        with open(USUARIOS_PATH, 'r', encoding='utf-8') as f:
            for linha in f:
                partes = linha.strip().split(';')
                if len(partes) >= 2 and partes[0] == nome and partes[1] == senha:
                    session['usuario'] = nome
                    session['tipo'] = partes[2] if len(partes) == 3 else 'comum'
                    salvar_log(f"Login: {nome}")
                    return redirect(url_for('fechar_chamado'))
        return 'Usuário ou senha inválidos'
    return render_template('login.html')

@app.route('/logout')
def logout():
    salvar_log(f"Logout: {session.get('usuario', '')}")
    session.pop('usuario', None)
    session.pop('tipo', None)
    return redirect(url_for('login'))

# -------------------- FECHAR CHAMADO -------------------- #
@app.route('/fechar_chamado')
def fechar_chamado():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('fechar_chamado.html', usuario=session['usuario'])

@app.route('/api/listar/<linha>')
def listar_chamados(linha):
    data_hoje1 = datetime.now().strftime("%Y-%m-%d")
    data_hoje2 = datetime.now().strftime("%d-%m-%Y")
    arq1 = os.path.join(CHAMADOS_DIR, linha, data_hoje1 + ".txt")
    arq2 = os.path.join(CHAMADOS_DIR, linha, data_hoje2 + ".txt")
    arq = arq1 if os.path.exists(arq1) else arq2
    if not os.path.exists(arq):
        return jsonify([])

    chamados = []
    with open(arq, 'r', encoding='utf-8') as f:
        linhas = f.readlines()

    atual = {}
    for l in linhas:
        l = l.strip()
        if l.startswith("#Pedido de Suporte#"):
            if atual:
                chamados.append(atual)
            atual = {
                "numero": l.split("#")[-1].strip(),
                "status": "aberto",
                "tecnico": "",
                "solucao": "",
                "fechado_em": ""
            }
        elif l.startswith("Data:"):
            atual["data"] = l.split(":",1)[1].strip()
        elif l.startswith("Hora:"):
            atual["hora"] = l.split(":",1)[1].strip()
        elif l.startswith("Operador:"):
            atual["operador"] = l.split(":",1)[1].strip()
        elif l.startswith("Problema:"):
            atual["problema"] = l.split(":",1)[1].strip()
        elif "Status Atual" in l and "Fechado" in l:
            atual["status"] = "fechado"
        elif "Técnico Atuante" in l:
            atual["tecnico"] = l.split("=",1)[-1].strip()
        elif "Solução" in l:
            atual["solucao"] = l.split("=",1)[-1].strip()
        elif "Data/Hora Resolução" in l or "Fechado em" in l:
            atual["fechado_em"] = l.split(":",1)[-1].strip().replace("=", "").strip()
    if atual:
        chamados.append(atual)

    chamados.sort(key=lambda x: f"{x.get('data', '')} {x.get('hora', '')}", reverse=True)
    return jsonify(chamados)

@app.route('/api/fechar_chamado', methods=['POST'])
def fechar_chamado_api():
    numero = request.form.get("numero")
    linha = request.form.get("linha")
    solucao = request.form.get("solucao")
    tecnico = request.form.get("tecnico")

    if not all([numero, linha, solucao, tecnico]):
        return "Erro: dados incompletos", 400

    data_hoje1 = datetime.now().strftime("%Y-%m-%d")
    data_hoje2 = datetime.now().strftime("%d-%m-%Y")
    arq1 = os.path.join(CHAMADOS_DIR, linha, data_hoje1 + ".txt")
    arq2 = os.path.join(CHAMADOS_DIR, linha, data_hoje2 + ".txt")
    arq = arq1 if os.path.exists(arq1) else arq2
    if not os.path.exists(arq):
        return "Arquivo do dia não encontrado", 404

    data_hora = datetime.now().strftime("%H:%M - %d/%m/%Y")
    linhas = []
    encontrado = False

    with open(arq, "r", encoding="utf-8") as f:
        for l in f:
            if f"#Pedido de Suporte# {numero}" in l:
                encontrado = True
                linhas.append(l)
            elif encontrado and "Status Atual=" in l:
                linhas.append("Status Atual=Fechado\n")
            elif encontrado and "Técnico Atuante=" in l:
                linhas.append(f"Técnico Atuante={tecnico}\n")
            elif encontrado and "Solução=" in l:
                linhas.append(f"Solução={solucao}\n")
            elif encontrado and ("Data/Hora Resolução=" in l or "Fechado em" in l):
                linhas.append(f"Data/Hora Resolução= {data_hora}\n")
                encontrado = False
            else:
                linhas.append(l)

    with open(arq, "w", encoding="utf-8") as f:
        f.writelines(linhas)

    salvar_log(f"Chamado #{numero} fechado por {tecnico} na linha {linha}")
    return "Chamado fechado com sucesso"

# -------------------- ADMINISTRAÇÃO -------------------- #
@app.route('/admin')
def admin():
    if 'usuario' not in session or session.get('tipo') != 'admin':
        return redirect(url_for('login'))
    usuarios = ler_usuarios()
    logs = []
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            logs = f.readlines()[-50:]
    return render_template('admin.html', usuarios=usuarios, logs=logs)

@app.route('/admin/add', methods=['POST'])
def admin_add():
    if session.get('tipo') != 'admin': return "Acesso negado"
    nome = request.form['usuario']
    senha = request.form['senha']
    tipo = request.form.get('tipo', 'comum')
    escrever_usuario(nome, senha, tipo)
    salvar_log(f"Usuário criado: {nome} ({tipo})")
    return redirect(url_for('admin'))

@app.route('/admin/remove', methods=['POST'])
def admin_remove():
    if session.get('tipo') != 'admin': return "Acesso negado"
    usuario = request.form['usuario']
    usuarios = ler_usuarios()
    usuarios = [u for u in usuarios if u[0] != usuario]
    with open(USUARIOS_PATH, 'w', encoding='utf-8') as f:
        for nome, tipo in usuarios:
            f.write(f"{nome};senha_padrao;{tipo}\n")
    salvar_log(f"Usuário removido: {usuario}")
    return redirect(url_for('admin'))

@app.route('/admin/update_password', methods=['POST'])
def admin_update_password():
    if session.get('tipo') != 'admin': return "Acesso negado"
    nome = request.form['usuario']
    nova_senha = request.form['nova_senha']
    usuarios = ler_usuarios()
    with open(USUARIOS_PATH, 'w', encoding='utf-8') as f:
        for u, tipo in usuarios:
            if u == nome:
                f.write(f"{u};{nova_senha};{tipo}\n")
            else:
                f.write(f"{u};senha_padrao;{tipo}\n")
    salvar_log(f"Senha atualizada para o usuário: {nome}")
    return redirect(url_for('admin'))

@app.route('/status_linhas')
def status_linhas():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('status_linhas.html', lista_linhas=LINHAS, usuario=session['usuario'], now=datetime.now())

@app.route('/api/enviar_status', methods=['POST'])
def enviar_status():
    if 'usuario' not in session:
        return "Não autorizado", 403
    linha = request.form.get("linha")
    mensagem = request.form.get("mensagem")
    usuario = session['usuario']
    data = datetime.now()
    data_str = data.strftime('%Y-%m-%d')
    data_hora_str = data.strftime('%d/%m/%Y %H:%M')

    pasta = os.path.join(BASE_DIR, 'diario', linha)
    os.makedirs(pasta, exist_ok=True)
    caminho = os.path.join(pasta, f"{data_str}.txt")

    with open(caminho, 'a', encoding='utf-8') as f:
        f.write(f"{data_hora_str}|{usuario}|{mensagem.strip()}\n")

    salvar_log(f"Status registrado por {usuario} na linha {linha}")
    return "OK"

@app.route('/api/status/<linha>')
def listar_status_linha(linha):
    resultado = []
    hoje = datetime.now()
    for i in range(7):
        dia = hoje.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        nome = dia.strftime('%Y-%m-%d')
        caminho = os.path.join(BASE_DIR, 'diario', linha, f"{nome}.txt")
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                for linha_arq in f:
                    partes = linha_arq.strip().split('|')
                    if len(partes) == 3:
                        resultado.append({
                            'data_hora': partes[0],
                            'usuario': partes[1],
                            'mensagem': partes[2]
                        })
    resultado = sorted(resultado, key=lambda x: x['data_hora'], reverse=True)
    return jsonify(resultado)

# -------------------- RODAR -------------------- #
# if __name__ == '__main__':
#    app.run(debug=True, port=5000)
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

