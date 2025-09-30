import argparse
from pathlib import Path

import pandas as pd

from agent_utils import GerenciadorDeArquivos
from fluxo import FluxoEDA


def obter_caminho_csv(caminho_entrada: Path) -> Path:
    """
    Resolve o caminho final do arquivo CSV a ser processado.
    Esta função é capaz de lidar tanto com arquivos CSV diretos quanto com
    arquivos ZIP que contenham um CSV, descompactando-os automaticamente.

    Args:
        caminho_entrada (Path): O caminho fornecido pelo usuário, que pode
                                apontar para um arquivo .csv ou .zip.

    Returns:
        Path: O caminho validado e pronto para uso do arquivo CSV.

    Raises:
        FileNotFoundError: Lançado se o arquivo de entrada não for encontrado
                           ou se um arquivo ZIP não contiver nenhum CSV.
        ValueError: Lançado se o formato do arquivo de entrada não for
                    suportado (diferente de .csv ou .zip).
    """
    if caminho_entrada.suffix == ".zip":
        # Define um diretório de destino para a extração baseado no nome do ZIP.
        pasta_destino = Path("outputs") / caminho_entrada.stem
        GerenciadorDeArquivos.descompactar_zip_condicionalmente(str(pasta_destino), str(caminho_entrada))

        # Busca por qualquer arquivo .csv dentro da pasta extraída.
        arquivos_csv_encontrados = list(pasta_destino.glob("*.csv"))
        if not arquivos_csv_encontrados:
            raise FileNotFoundError(
                "O arquivo ZIP foi descompactado, mas nenhum arquivo CSV foi localizado em seu interior."
            )

        # Retorna o primeiro arquivo CSV encontrado.
        return arquivos_csv_encontrados[0]

    elif caminho_entrada.suffix == ".csv":
        if not caminho_entrada.exists():
            raise FileNotFoundError(f"O arquivo CSV especificado não existe no caminho: {caminho_entrada}")
        return caminho_entrada

    else:
        raise ValueError(
            f"Extensão de arquivo inválida: '{caminho_entrada.suffix}'. Apenas .csv e .zip são aceitos."
        )


def main():
    """
    Ponto de entrada principal para a execução do assistente de Análise
    Exploratória de Dados (EDA). Orquestra a análise a partir dos argumentos
    fornecidos via linha de comando.
    """
    parser = argparse.ArgumentParser(
        description="Assistente Inteligente para Análise Exploratória de Dados (EDA) em arquivos CSV."
    )
    parser.add_argument(
        "caminho_arquivo",
        type=str,
        help="Caminho do arquivo de dados (.csv) ou do pacote compactado (.zip) para análise.",
    )
    parser.add_argument(
        "pergunta",
        type=str,
        help="Sua pergunta em linguagem natural sobre o conjunto de dados (ex: 'Qual a correlação entre as colunas?').",
    )
    args = parser.parse_args()

    try:
        caminho_csv = obter_caminho_csv(Path(args.caminho_arquivo))
        pergunta_usuario = args.pergunta

        # A responsabilidade de carregar o DataFrame é delegada ao fluxo de agentes
        # para garantir que o contexto completo do arquivo seja mantido durante a análise.
        print(f"🚀 Processando sua solicitação para o arquivo: {caminho_csv}")
        print(f"🗣️ Pergunta do usuário: \"{pergunta_usuario}\"")

        fluxo_analise = FluxoEDA(caminho_csv=caminho_csv)
        resultado_final = fluxo_analise.kickoff(inputs={"text": pergunta_usuario})

        print("\n" + "*" * 60)
        print("🧠 Conclusão da Análise do Agente:")
        print("*" * 60)
        print(resultado_final)

    except (FileNotFoundError, ValueError) as e:
        print(f"⚠️ Atenção: {e}")
    except Exception as e:
        print(f"🚨 Um erro crítico ocorreu durante a execução: {e}")


if __name__ == "__main__":
    main()