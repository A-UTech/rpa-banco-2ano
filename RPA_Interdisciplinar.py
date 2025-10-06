import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os

# congigurar variáveis de ambiente
load_dotenv()
# Conectar ao banco PostgreSQL do 1° ano
try:
    conn_1ano = psycopg2.connect(
        dbname=os.getenv("DBNAME_1ano"),
        user=os.getenv("USER"),
        password=os.getenv("PASSWORD"),
        host=os.getenv("HOST"),
    )
    cur_1ano = conn_1ano.cursor()
except Exception as e:
    print("Erro ao conectar com o banco de dados do 1°ano: ",e)

# Conectar ao banco PostgreSQL do 2° ano
try:
    conn_2ano = psycopg2.connect(
        dbname=os.getenv("DBNAME_2ANO"),
        user=os.getenv("USER"),
        password=os.getenv("PASSWORD"),
        host=os.getenv("HOST"),
    )
    cur_2ano = conn_2ano.cursor()
except Exception as e:
    print("Erro ao conectar com o banco de dados do 2°ano: ",e)

# Inicialização de variáveis com o nome das tabelas para obter maior facilidade caso haja manutenção no código.
tabelas_1ano = {"plano": ["id","nome","preco","armazenamento"], "condena":["id","nome","tipo"], "empresa":["id","nome","cnpj"]}
tabelas_2ano = {"planos": ["id","nome","preco","armazenamento"], "condena":["id","nome","tipo"], "empresa":["id","nome"]}

# Função que realiza o RPA entre as duas tabelas
def RPA_inter(tabela_1ano, colunas_1ano, tabela_2ano, colunas_2ano, conn_1ano_param, conn_2ano_param):

    cursor_1ano = conn_1ano_param.cursor()
    cursor_2ano = conn_2ano_param.cursor()

    # Transforma a lista em texto separado por vírgulas para colocar na query
    colunas_1ano_str = ", ".join(colunas_1ano)
    colunas_2ano_str = ", ".join(colunas_2ano)
    
    # Monta placeholders (%s, %s, ...) -- vários %s apenas para o número de colunas
    placeholders = ", ".join(["%s"] * len(colunas_2ano))

    # Exclude feito com for para não atualizar o id
    excluded = ", ".join([
        f"{col} = EXCLUDED.{col}" for col in colunas_2ano if col != "id"
    ])
    # Condição para fazer o update apenas se houver mudanças nos dados (exceto o id)
    condicoes = " OR ".join([
        f"{tabela_2ano}.{col} IS DISTINCT FROM EXCLUDED.{col}"
        for col in colunas_2ano if col != "id"
    ])

    # --- Busca de dados da tabela do 1° ano ---
    cursor_1ano.execute(f"SELECT {colunas_1ano_str} FROM {tabela_1ano};")
    dados_1ano = cursor_1ano.fetchall()

    

    # --- Faz o merge na tabela de destino, se nao houver conflitos no id irá adicionar o que veio do banco, porém caso tenha o id, atualiza se necessário ---
    try:
        for linha in dados_1ano:
            query = f"""
                INSERT INTO {tabela_2ano} ({colunas_2ano_str})
                VALUES ({placeholders})
                ON CONFLICT (id) DO UPDATE
                SET {excluded}
                WHERE {condicoes};
            """
            cursor_2ano.execute(query, linha)
        conn_2ano.commit()
        print(f"Dados da tabela {tabela_1ano} inseridos/atualizados com sucesso na tabela {tabela_2ano}.")
    except Exception as e:
        conn_2ano.rollback()
        print("Erro ao inserir/atualizar dados: ",e)
    finally:
        cursor_1ano.close()
        cursor_2ano.close()

# Executa o RPA para cada tabela
for (key_1, valor_1), (key_2, valor_2) in zip(tabelas_1ano.items(), tabelas_2ano.items()):
    if key_1 == "empresa":
        valor_1.remove("cnpj")  # Remover a coluna 'cnpj' da tabela do 1° ano, pois não existe na tabela do 2° ano e não é utilizado
    RPA_inter(key_1, valor_1, key_2, valor_2, conn_1ano, conn_2ano)

