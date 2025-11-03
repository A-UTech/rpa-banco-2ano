# 🤖 RPA Interdisciplinar – Integração de Bancos de Dados

Este projeto automatiza a **sincronização entre dois bancos de dados PostgreSQL** (1º Ano → 2º Ano) usando Python.  
O objetivo é manter as tabelas atualizadas entre os dois sistemas acadêmicos, garantindo consistência de dados e reduzindo a necessidade de manutenção manual.

---

## 🧩 Estrutura do Projeto

📂 RPA_Bancos/
├── .github/
│   └── workflows/
│       └── pull_request_template.md
│       └── agendador_rpa.yml
├── .gitignore
├── LICENSE
├── README.md
├── RPA_interdisciplinar.py
├── Requirements.txt
└── envFalso.txt


---

## ⚙️ Configuração e Execução Local

Antes de executar o RPA, é necessário criar o ambiente virtual, instalar as dependências e configurar o arquivo `.envFalso`.

### 1. Criar o ambiente virtual
```bash
python -m venv venv
```

### 2. Ativar o ambiente virtual
```bash
venv/Scripts/Activate
```

### 3. Instalar as dependências
```bash
pip install -r requirements.txt
```

---

## 🔐 Configuração do .envFalso

O arquivo `.envFalso` deve conter as variáveis de ambiente usadas para conectar aos bancos de dados.

**Exemplo de configuração:**
```env
# Banco do 1º ano
DB1_HOST=localhost
DB1_NAME=banco_primeiro_ano
DB1_USER=postgres
DB1_PASS=senha123
DB1_PORT=5432

# Banco do 2º ano
DB2_HOST=localhost
DB2_NAME=banco_segundo_ano
DB2_USER=postgres
DB2_PASS=senha456
DB2_PORT=5432
```

⚠️ Esse arquivo **não deve ser commitado** no repositório público.  
Use o `.envFalso` como modelo e crie um `.env` local com suas credenciais reais.

---

## 🚀 Executando o RPA Manualmente

Após configurar tudo corretamente, basta rodar o script:
```bash
python RPA_interdisciplinar.py
```

Durante a execução, o script:

- Conecta aos dois bancos de dados (1º e 2º ano);
- Sincroniza registros com base nas chaves primárias;
- Usa `ON CONFLICT` para atualizar apenas quando necessário;
- Exibe logs no terminal indicando as inserções, atualizações e possíveis erros.

---

## 🧱 Estrutura de Sincronização

| Banco 1º Ano | Banco 2º Ano | Tipo de Sincronização |
|---------------|---------------|-------------------------|
| plano | planos | Inserção/atualização direta por id |
| condena | condena | Inserção/atualização direta por id |
| empresa | empresa / unidade | Divisão em duas tabelas com FK |

---

## ☁️ Execução Automática com GitHub Actions

O projeto inclui um workflow configurado no arquivo:
```
.github/workflows/agendador_rpa.yml
```

Esse workflow permite:

- Rodar o RPA manualmente pela aba **Actions** no GitHub;
- Ou automaticamente todos os dias às **12:00 UTC (09:00 em Brasília)**.

**Estrutura básica do workflow:**
```yaml
name: Agendador do RPA Python

on:
  workflow_dispatch:
  schedule:
    - cron: '0 12 * * *'

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout do Repositório
        uses: actions/checkout@v3

      - name: Configurar Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Instalar Dependências
        run: |
          python -m pip install --upgrade pip
          pip install -r Requirements.txt

      - name: Executar o Script RPA
        env:
          DBNAME_1ANO: ${{ secrets.DBNAME_1ANO }}
          DBNAME_2ANO: ${{ secrets.DBNAME_2ANO }}
          HOST: ${{ secrets.HOST }}
          PASSWORD: ${{ secrets.PASSWORD }}
          USER: ${{ secrets.USER }}
        run: python RPA_Interdisciplinar.py
```

---

## 🔒 Variáveis de Ambiente (Secrets)

As credenciais dos bancos devem ser configuradas como **GitHub Secrets** para garantir segurança.

No repositório, acesse:  
`Settings → Secrets and variables → Actions → New repository secret`

E adicione:

- `DBNAME_1ANO`
- `DBNAME_2ANO`
- `HOST`
- `PASSWORD`
- `USER`

---

## 🧠 Tecnologias Utilizadas

- **Python 3.11+**
- **psycopg2** → Conexão e execução de queries PostgreSQL  
- **python-dotenv** → Carregamento seguro das variáveis de ambiente  
- **pandas** → Manipulação de dados antes da sincronização  
- **GitHub Actions** → Automação e agendamento do RPA  

---

## 💡 Dicas

- Sempre teste o script localmente antes de liberar o agendamento automático.  
- Utilize bancos de teste antes de conectar aos bancos principais.  
- Configure logs para acompanhar o histórico das sincronizações.  

---

## 👨‍💻 Autor

**Gabriel Martins**  
📅 Projeto Interdisciplinar – RPA (Integração de Bancos de Dados)  
🧠 Desenvolvimento em Python, PostgreSQL e Automação com GitHub Actions
