import json
import os
import shutil
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import BackgroundTasks, FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from agent_utils import GerenciadorDeArquivos
from fluxo import FluxoEDA

# --- Configuração da Aplicação FastAPI ---
app = FastAPI(
    title="Assistente de Análise de Dados com IA",
    description="Uma API RESTful que serve como interface para uma equipe de agentes de IA especializados em Análise Exploratória de Dados (EDA) sobre arquivos CSV.",
    version="1.0.0",
)

# --- Configuração de CORS (Cross-Origin Resource Sharing) ---
# Permite que o frontend (mesmo em origens diferentes) se comunique com a API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, restrinja a domínios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Gerenciamento de Diretórios ---
# Define e cria os diretórios necessários para uploads e saídas.
DIRETORIO_UPLOADS = Path("./uploads")
DIRETORIO_UPLOADS.mkdir(exist_ok=True)

DIRETORIO_SAIDAS = Path("./outputs")
DIRETORIO_SAIDAS.mkdir(exist_ok=True)


# --- Funções de Limpeza em Background ---
def limpar_arquivo(caminho: str) -> None:
    """Remove um arquivo de forma segura em uma tarefa de fundo."""
    try:
        if os.path.exists(caminho):
            os.remove(caminho)
            print(f"🧹 Arquivo temporário limpo: {caminho}")
    except Exception as e:
        print(f"❗️ Falha ao limpar o arquivo {caminho}: {e}")


def limpar_diretorio(caminho: str) -> None:
    """Remove um diretório e todo o seu conteúdo em uma tarefa de fundo."""
    try:
        if os.path.exists(caminho):
            shutil.rmtree(caminho)
            print(f"🧹 Diretório temporário limpo: {caminho}")
    except Exception as e:
        print(f"❗️ Falha ao limpar o diretório {caminho}: {e}")


# --- Endpoint Principal de Interação ---
@app.post("/chat/")
async def interagir_com_agente(
    file: Annotated[UploadFile, File()],
    question: Annotated[str, Form()],
    background_tasks: BackgroundTasks,
):
    """
    Endpoint central para processar solicitações de análise de dados.
    Recebe um arquivo (.csv ou .zip) e uma pergunta, orquestra a análise
    pelos agentes de IA e retorna o resultado.
    """
    try:
        print(f"📨 Nova solicitação recebida: {file.filename}")
        print(f"💬 Pergunta do usuário: '{question}'")

        # Salva o arquivo enviado em um local temporário
        caminho_arquivo_upload = DIRETORIO_UPLOADS / file.filename
        with caminho_arquivo_upload.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Processa o arquivo, descompactando se for um ZIP
        if caminho_arquivo_upload.suffix == ".zip":
            pasta_descompactada = DIRETORIO_SAIDAS / caminho_arquivo_upload.stem
            GerenciadorDeArquivos.descompactar_zip_condicionalmente(str(pasta_descompactada), str(caminho_arquivo_upload))
            arquivos_csv_encontrados = list(pasta_descompactada.glob("*.csv"))
            if not arquivos_csv_encontrados:
                return {"error": "O arquivo ZIP fornecido não contém nenhum arquivo CSV."}
            caminho_final_csv = str(arquivos_csv_encontrados[0])
            background_tasks.add_task(limpar_diretorio, str(pasta_descompactada))
        elif caminho_arquivo_upload.suffix == ".csv":
            caminho_final_csv = str(caminho_arquivo_upload)
        else:
            return {
                "error": "Formato de arquivo inválido. Apenas arquivos .csv e .zip são aceitos."
            }

        # Agenda a remoção do arquivo de upload original após a resposta ser enviada
        background_tasks.add_task(limpar_arquivo, str(caminho_arquivo_upload))

        # Inicializa e executa o fluxo de análise
        print("🤖 Acionando a equipe de agentes de IA...")
        fluxo_analise = FluxoEDA(caminho_csv=caminho_final_csv)

        dados_resposta = fluxo_analise.executar(question)
        print(f"💡 Resposta recebida da equipe de agentes.")
        print(f"   - Tipo da resposta: {type(dados_resposta)}")

        # --- Roteamento da Resposta com Base no Conteúdo ---

        if isinstance(dados_resposta, dict) and dados_resposta.get("image_url"):
            # Cenário 1: A resposta é uma visualização gráfica.
            url_imagem_local = dados_resposta["image_url"]
            nome_arquivo_grafico = Path(url_imagem_local).name

            print(f"🖼️  Resposta contém uma visualização: {nome_arquivo_grafico}")
            return {
                "response": dados_resposta.get(
                    "text", "A visualização solicitada foi gerada."
                ),
                "image_url": f"/outputs/{nome_arquivo_grafico}",
            }

        elif isinstance(dados_resposta, dict) and dados_resposta.get("response"):
            # Cenário 2: A resposta é uma análise textual.
            return dados_resposta

        else:
            # Cenário de fallback para respostas inesperadas.
            return {
                "error": f"Formato de resposta inesperado ou inválido recebido dos agentes: {dados_resposta}"
            }

    except Exception as e:
        print(f"🚨 Erro crítico no endpoint /chat/: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Ocorreu um erro interno no servidor: {str(e)}"}


# --- Endpoints de Suporte ---

@app.get("/outputs/{filename}")
async def servir_arquivo_de_saida(filename: str):
    """Serve os arquivos gerados (como gráficos) a partir do diretório de saídas."""
    caminho_arquivo = DIRETORIO_SAIDAS / filename
    if caminho_arquivo.is_file():
        return FileResponse(caminho_arquivo)
    else:
        return {"error": "O arquivo solicitado não foi encontrado."}


@app.get("/healthcheck")
async def verificar_saude_api():
    """Endpoint de verificação de saúde para monitoramento."""
    return {
        "status": "operacional",
        "message": "A API do Assistente de Análise de Dados está online.",
        "chave_openai_configurada": "OPENAI_API_KEY" in os.environ and bool(os.getenv("OPENAI_API_KEY")),
    }


@app.get("/", response_class=HTMLResponse)
async def servir_pagina_principal():
    """Serve a interface do usuário (frontend) na rota raiz."""
    try:
        caminho_html = "index.html"
        with open(caminho_html, encoding="utf-8") as f:
            conteudo_html = f.read()
        return HTMLResponse(content=conteudo_html, status_code=200)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Erro 404: Interface não encontrada</h1><p>Verifique se a pasta 'frontend' com o arquivo 'index.html' está presente na raiz do projeto.</p>",
            status_code=404,
        )


# --- Montagem de Diretórios Estáticos ---
# Permite que o FastAPI sirva arquivos CSS, JS e imagens diretamente.
app.mount("/static", StaticFiles(directory="."), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# --- Ponto de Entrada para Execução ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)