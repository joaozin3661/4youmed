from flask import Flask, render_template, request, jsonify
import mysql.connector
from mysql.connector import Error
import json
import random
import os

app = Flask(__name__)

# Configurações do banco de dados
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': 3306,
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'D3sm0dus'),
    'database': os.getenv('DB_NAME', 'vitin')
}

# --- FILTRO JINJA (para o site.html) ---
@app.template_filter('loads')
def json_loads_filter(s):
    try:
        if isinstance(s, str):
            return json.loads(s)
        return s
    except Exception as e:
        print("Erro ao carregar JSON no filtro Jinja:", e)
        return []

# --- Rota Principal: SEU SITE COMPLETO ---
@app.route("/")
def index():
    return render_template("4youmed ver.html")

# --- Rota de Teste (não precisa de alteração) ---
@app.route("/teste-simples")
def teste_simples():
    questoes = []
    try:
        conexao = mysql.connector.connect(**db_config)
        cursor = conexao.cursor()
        # Nota: Esta query também não busca imagem_url, mas não afeta o site principal.
        cursor.execute("SELECT id, disciplina, pergunta, explicacao, tema, opcoes, resposta_correta FROM questoesbanco;")
        questoes = cursor.fetchall()
        cursor.close()
        conexao.close()
    except Error as e:
        print("Erro ao buscar questões para a página de teste:", e)
    
    return render_template("site.html", site=questoes)


# --- ROTA DA API: Para o site principal buscar questões filtradas ---
@app.route("/api/questoes", methods=['POST'])
def api_questoes():
    try:
        filtros = request.get_json()
        temas_por_disciplina = filtros.get('temasSelecionados', {})
        limite_total = int(filtros.get('limite', 5))

        if not temas_por_disciplina:
            return jsonify({"erro": "Nenhum tema selecionado"}), 400

        conexao = mysql.connector.connect(**db_config)
        cursor = conexao.cursor(dictionary=True)

        questoes_encontradas = []
        for disciplina, temas in temas_por_disciplina.items():
            format_strings = ','.join(['%s'] * len(temas))
            
            # --- CORREÇÃO APLICADA AQUI ---
            # Adicionamos a coluna 'imagem_url' na consulta SQL
            query = f"""
                SELECT 
                    id, disciplina, tema, 
                    pergunta AS enunciado, 
                    opcoes AS alternativas, 
                    resposta_correta AS respostaCorreta, 
                    explicacao AS comentario,
                    imagem_url 
                FROM questoesbanco 
                WHERE disciplina = %s AND tema IN ({format_strings})
            """
            
            params = (disciplina,) + tuple(temas)
            cursor.execute(query, params)
            
            resultados = cursor.fetchall()
            questoes_encontradas.extend(resultados)

        cursor.close()
        conexao.close()

        random.shuffle(questoes_encontradas)
        questoes_finais = questoes_encontradas[:limite_total]

        return jsonify(questoes_finais)

    except Error as e:
        print(f"Erro no banco de dados: {e}")
        return jsonify({"erro": "Ocorreu um erro no servidor ao buscar as questões."}), 500
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return jsonify({"erro": "Ocorreu um erro inesperado."}), 500

if __name__ == "__main__":
    app.run(debug=True)

