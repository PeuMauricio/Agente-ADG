#!/usr/bin/env python3
"""
Script de diagnóstico para validar o ambiente de execução do projeto CrewAI.
Realiza um check-up completo da configuração, desde a versão do Python até a
conectividade com a API da OpenAI.
"""

import os
import sys
from pathlib import Path


def validar_versao_python():
    """Verifica se a versão do interpretador Python atende aos requisitos."""
    versao = sys.version_info
    print(f"Interpretador Python detectado: {versao.major}.{versao.minor}.{versao.micro}")
    if versao.major < 3 or (versao.major == 3 and versao.minor < 8):
        print("⛔️ INCOMPATÍVEL: É necessário Python 3.8 ou superior.")
        return False
    print("✔️ Versão do Python compatível.")
    return True


def auditar_dependencias():
    """Audita a instalação das bibliotecas Python essenciais."""
    pacotes_necessarios = [
        "crewai",
        "pandas",
        "matplotlib",
        "seaborn",
        "fastapi",
        "uvicorn",
        "python-dotenv",
        "openai",
    ]

    ausentes = []
    for pacote in pacotes_necessarios:
        try:
            # O nome do módulo pode ser diferente do nome do pacote (ex: python-dotenv -> dotenv)
            __import__(pacote.replace("-", "_"))
            print(f"✔️ {pacote} - Instalado")
        except ImportError:
            print(f"⛔️ {pacote} - NÃO ENCONTRADO")
            ausentes.append(pacote)

    if ausentes:
        print(f"\n🛠️ Ação necessária: Instale os pacotes ausentes com o comando:")
        print(f"pip install {' '.join(ausentes)}")
        return False

    return True


def inspecionar_versao_crewai():
    """Verifica a versão da biblioteca CrewAI e a integridade de suas importações."""
    try:
        import crewai

        versao = getattr(crewai, "__version__", "não identificada")
        print(f"Versão do CrewAI: {versao}")

        # Valida se os componentes principais podem ser importados
        from crewai import LLM, Agent, Crew, Process, Task

        print("✔️ Importações essenciais do CrewAI funcionam corretamente.")
        return True
    except Exception as e:
        print(f"⛔️ Falha na verificação do CrewAI: {e}")
        return False


def verificar_arquivo_config():
    """Analisa a existência e o conteúdo do arquivo de configuração .env."""
    caminho_env = Path(".env")
    if not caminho_env.exists():
        print("⛔️ Arquivo de configuração '.env' não localizado.")
        print("Instrução: Crie um arquivo chamado .env na raiz do projeto com o seguinte conteúdo:")
        print("OPENAI_API_KEY=sua-chave-de-api-aqui")
        return False

    from dotenv import load_dotenv
    load_dotenv()

    chave_api = os.getenv("OPENAI_API_KEY")
    if not chave_api:
        print("⛔️ A variável OPENAI_API_KEY não foi encontrada dentro do arquivo .env.")
        return False

    if chave_api.startswith("sk-") and len(chave_api) > 20:
        print("✔️ A variável OPENAI_API_KEY parece estar configurada corretamente.")
        return True
    else:
        print("⚠️ ALERTA: O formato da OPENAI_API_KEY parece inválido. Verifique se copiou a chave completa.")
        return False


def checar_estrutura_diretorios():
    """Verifica se a estrutura de pastas esperada pelo projeto existe."""
    pastas_projeto = ["uploads", "outputs", "frontend"]
    for nome_pasta in pastas_projeto:
        caminho_pasta = Path(nome_pasta)
        if caminho_pasta.exists():
            print(f"✔️ Diretório '{nome_pasta}/' encontrado.")
        else:
            print(f"ℹ️ INFORMATIVO: O diretório '{nome_pasta}/' não existe e será criado durante a execução, se necessário.")


def testar_configuracao_llm():
    """Tenta instanciar o LLM para validar a configuração de conexão."""
    try:
        import os
        from crewai import LLM

        chave_api = os.getenv("OPENAI_API_KEY")
        if not chave_api:
            print("⛔️ Teste abortado: a chave de API não está disponível.")
            return False

        llm = LLM(model="gpt-4o-mini", api_key=chave_api)
        print("✔️ A configuração do LLM foi criada com sucesso.")
        return True

    except Exception as e:
        print(f"⛔️ Falha ao inicializar o LLM: {e}")
        return False


def testar_instanciacao_crewai():
    """Realiza um teste rápido de criação de um agente CrewAI."""
    try:
        import os
        from crewai import LLM, Agent

        chave_api = os.getenv("OPENAI_API_KEY")
        if not chave_api:
            print("⛔️ Teste abortado: a chave de API não está disponível.")
            return False

        llm = LLM(model="gpt-4o-mini", api_key=chave_api)

        # Cria um agente de teste para validar a funcionalidade básica
        agente_teste = Agent(
            role="Agente de Teste", goal="Validar a criação", backstory="N/A", llm=llm
        )

        print("✔️ Um agente de teste foi criado com sucesso.")
        return True

    except Exception as e:
        print(f"⛔️ Falha ao criar um agente de teste: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ponto de entrada para o script de diagnóstico do ambiente."""
    print("🩺 CHECK-UP DE SAÚDE DO AMBIENTE CrewAI")
    print("=" * 50)

    etapas_verificacao = [
        ("Versão do Python", validar_versao_python),
        ("Dependências do Projeto", auditar_dependencias),
        ("Integridade do CrewAI", inspecionar_versao_crewai),
        ("Arquivo de Configuração (.env)", verificar_arquivo_config),
        ("Estrutura de Diretórios", checar_estrutura_diretorios),
        ("Conexão com LLM", testar_configuracao_llm),
        ("Funcionalidade Básica do CrewAI", testar_instanciacao_crewai),
    ]

    resultados_finais = []
    for nome_etapa, funcao_etapa in etapas_verificacao:
        print(f"\n🔬 Executando verificação: {nome_etapa}...")
        try:
            resultado = funcao_etapa()
            resultados_finais.append((nome_etapa, resultado))
        except Exception as e:
            print(f"⛔️ Erro inesperado durante a verificação: {e}")
            resultados_finais.append((nome_etapa, False))

    print("\n" + "=" * 50)
    print("📋 RELATÓRIO FINAL DO DIAGNÓSTICO:")

    sucessos = sum(1 for _, resultado in resultados_finais if resultado)
    total_etapas = len(resultados_finais)

    for nome_etapa, resultado in resultados_finais:
        status_icone = "✔️" if resultado else "⛔️"
        print(f"{status_icone} {nome_etapa}")

    print(f"\n{sucessos} de {total_etapas} verificações concluídas com sucesso.")

    if sucessos == total_etapas:
        print("\n✅ Ambiente configurado corretamente! Tudo pronto para começar.")
    else:
        print(
            f"\n❗️ {total_etapas - sucessos} ponto(s) de atenção encontrado(s). Por favor, revise os itens marcados com '⛔️' acima."
        )


if __name__ == "__main__":
    main()