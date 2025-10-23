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

# Inicialização de variáveis com o nome das tabelas para obter maior facilidade caso haja manutenção no código.   regiao é o campo de estado da tabela de unidade
tabelas_1ano = {"planos": ["id","nome","mensalidade","armazenamento"], "condenas":["id","nome","tipo_condena"], "empresas":["id","nome","cnpj","unidade","regiao","id_planos","senha"]}
tabelas_2ano = {"planos": ["id","nome","preco","armazenamento"], "condena":["id","nome","tipo"], "duas_tabelas": {
        "empresa": ["id", "nome"],
        "unidade": ["cnpj", "nome", "estado",  "id_plano", "senha"]
    }}

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
        print(tabela_2ano)
    finally:
        cursor_1ano.close()
        cursor_2ano.close()


def RPA_inter_empresa_unidade(tabela_1ano, colunas_1ano, tabelas_2ano, conn_1ano_param, conn_2ano_param):
    cursor_1ano = conn_1ano_param.cursor()
    cursor_2ano = conn_2ano_param.cursor()

    # Divide tabelas e colunas
    tabelas_destino = list(tabelas_2ano.keys())       # ['empresa', 'unidade']
    colunas_destino = list(tabelas_2ano.values())     # [['id','nome'], ['cnpj','nome','estado','id_plano','senha']]

    tabela_empresa = tabelas_destino[0]
    tabela_unidade = tabelas_destino[1]
    colunas_empresa = colunas_destino[0]
    colunas_unidade = colunas_destino[1]
    colunas_unidade.append("id_empresa")
    print(colunas_unidade)
    
    colunas_empresa_str = ", ".join(colunas_empresa)
    colunas_unidade_str = ", ".join(colunas_unidade)
    

    print(f"Inserindo de {tabela_1ano} em {tabela_empresa} e {tabela_unidade}...")

    try:
        # Busca os dados da tabela do 1º ano
        cursor_1ano.execute(f"SELECT {', '.join(colunas_1ano)} FROM {tabela_1ano};")
        dados = cursor_1ano.fetchall()

        for linha in dados:
            # Monta dict com nome das colunas
            registro = dict(zip(colunas_1ano, linha))

            print(registro)
            nome_empresa = registro.get(f"{colunas_1ano[1]}")  
            cnpj_unidade = registro.get(f"{colunas_1ano[2]}")

            cnpj_unidade = str(cnpj_unidade)

            # Verifica se já existe empresa
            cursor_2ano.execute(f"SELECT verificar_empresa_existente('{cnpj_unidade}');")
            resultado = cursor_2ano.fetchone()
            print(resultado)
            id_empresa = resultado[0] if resultado and resultado[0] else None

            print(f"Processando empresa: {nome_empresa}, CNPJ: {cnpj_unidade}, ID Empresa: {id_empresa}")
 
            if id_empresa is None:
                cursor_2ano.execute(
                    f"""
                    INSERT INTO {tabela_empresa} ({colunas_1ano[1]})
                    VALUES (%s)
                    RETURNING id;
                    """,
                    (nome_empresa,)
                )
                id_empresa = cursor_2ano.fetchone()[0]
            
            id_empresa = int(id_empresa)
            

            placeholders = ", ".join(["%s"] * len(colunas_unidade))

            # Exclude feito com for para não atualizar o id
            excluded = ", ".join([
                f"{col} = EXCLUDED.{col}" for col in colunas_unidade if col != "id"
            ])
            # Condição para fazer o update apenas se houver mudanças nos dados (exceto o id)
            condicoes = " OR ".join([
                f"{tabela_unidade}.{col} IS DISTINCT FROM EXCLUDED.{col}"
                for col in colunas_unidade if col != "id"
            ])
            print("----------------------")
            print(colunas_unidade)
            print([registro.get(col) for col in colunas_unidade if col != "id_empresa"])
            valores_unidade = [registro.get(col) for col in colunas_1ano if col != "id" and col != "nome"]
            valores_unidade.append(id_empresa)

            query = f"""
                INSERT INTO {tabela_unidade} ({colunas_unidade_str})
                VALUES ({placeholders})
                ON CONFLICT (cnpj) DO UPDATE
                SET {excluded}
                WHERE {condicoes};
            """
            cursor_2ano.execute(query, valores_unidade)
        conn_2ano_param.commit()
        print("Dados de empresa/unidade inseridos com sucesso!")

    except Exception as e:
        conn_2ano_param.rollback()
        print("Erro ao inserir empresa/unidade:", e)

    finally:
        cursor_1ano.close()
        cursor_2ano.close()




# Executa o RPA para cada tabela
for (key_1, valor_1), (key_2, valor_2) in zip(tabelas_1ano.items(), tabelas_2ano.items()):
    if key_2 != "duas_tabelas":  # Ignora a entrada especial "duas_tabelas"
        RPA_inter(key_1, valor_1, key_2, valor_2, conn_1ano, conn_2ano)
    else:
        RPA_inter_empresa_unidade(key_1, valor_1, valor_2, conn_1ano, conn_2ano)
    