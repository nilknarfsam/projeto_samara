# Sistema de Chamados Flask 📋🔧

Este é um sistema web para registro, acompanhamento e fechamento de chamados técnicos em linhas de produção. Desenvolvido em **Flask** com HTML, CSS e JavaScript.

## Funcionalidades ✅

- Abertura de chamados por operadores
- Fechamento por técnicos com login
- Dashboard por linha de produção
- Filtros por data, turno e palavra-chave
- Exportação para Excel (.csv)
- Diário de bordo/status das linhas
- Painel visual de baias com falha
- Administração de usuários (login, senha, permissões)
- Design moderno (tema azul e cinza)

## Estrutura do Projeto 📂

```bash
app_chamados_flask/
│
├── app.py                  # Arquivo principal Flask
├── chamados/               # Chamados organizados por linha e data
├── diario/                 # Status das linhas
├── usuarios.txt            # Lista de usuários e senhas
├── logs_acesso.txt         # Logs de login e ações
├── templates/              # HTML (Jinja2)
│   ├── login.html
│   ├── abrir_chamado.html
│   ├── fechar_chamado.html
│   ├── status_linhas.html
│   └── admin.html
└── static/                 # CSS, JS, imagens (opcional)
