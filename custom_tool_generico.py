import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ExecutorCodigoPandas(BaseTool):
    """
    Uma ferramenta para executar scripts Python focados na análise de um DataFrame.
    Esta ferramenta opera sobre um DataFrame pandas que é injetado dinamicamente.
    """

    name: str = "Executor de Código Python para Análise de DataFrame"
    description: str = (
        "Executa um bloco de código Python para consultar um DataFrame (nomeado 'df'). "
        "A entrada deve ser um script Python válido. "
        "O DataFrame já está disponível na variável 'df' no escopo de execução."
    )
    # Atributo para receber o DataFrame injetado
    df: pd.DataFrame = None

    def _run(self, codigo_python: str) -> str:
        # O contexto de execução já recebe o DataFrame, eliminando a necessidade de caminhos de arquivo.
        contexto_execucao = {"df": self.df, "pd": pd, "np": np}
        try:
            # --- AJUSTE INTELIGENTE: Captura automática do resultado da última linha ---
            linhas_codigo = codigo_python.strip().split("\n")
            ultima_linha = linhas_codigo[-1].strip()

            # Verifica se a última linha é uma expressão a ser avaliada (e não uma atribuição ou declaração)
            if "=" not in ultima_linha and not ultima_linha.startswith(
                ("import", "def", "class", "for", "while", "if")
            ):
                # Transforma a última linha em uma atribuição para a variável 'resultado'
                codigo_python = "\n".join(linhas_codigo[:-1]) + f"\nresultado = {ultima_linha}"
            # ---------------------------------------------------------------------------

            # Executa o código fornecido pelo agente no contexto preparado
            exec(codigo_python, contexto_execucao)

            # Procura pela variável 'resultado' no contexto após a execução
            if "resultado" in contexto_execucao:
                resultado_final = contexto_execucao["resultado"]
                # Formata DataFrames e Series para uma representação textual legível
                if isinstance(resultado_final, (pd.DataFrame, pd.Series)):
                    # Limita a saída para evitar sobrecarga de tokens, mantendo o índice visível
                    return resultado_final.to_string(
                        index=True, max_rows=50
                    )
                return str(resultado_final)

            return f"[INFO] O código foi executado, mas a variável 'resultado' não foi definida. Código executado: {codigo_python}"
        except Exception as e:
            return f"[FALHA] Erro durante a execução do código: {e}"


class GeradorVisualizacaoTool(BaseTool):
    """
    Ferramenta especializada em criar e salvar visualizações gráficas a partir de um DataFrame.
    """

    name: str = "Ferramenta de Geração de Visualizações Gráficas"
    description: str = (
        "Cria uma visualização gráfica (gráfico) a partir do DataFrame 'df' e a salva como um arquivo de imagem. "
        "A entrada deve ser um dicionário contendo 'tipo_grafico', 'colunas' e 'titulo'. "
        "Tipos suportados: histograma, dispersao, boxplot, barras, multiplos_histogramas."
    )

    class SchemaGeradorVisualizacao(BaseModel):
        tipo_grafico: str = Field(
            ...,
            description="Define o tipo de gráfico a ser criado. Opções válidas: 'histograma', 'dispersao', 'boxplot', 'barras', 'multiplos_histogramas'.",
        )
        colunas: list[str] = Field(
            ...,
            description="Lista com os nomes das colunas do DataFrame que serão usadas para gerar o gráfico.",
        )
        titulo: str = Field(
            None,
            description="Título a ser exibido no gráfico. Se omitido, um título padrão será usado.",
        )

    # Associa o esquema de validação à ferramenta
    args_schema = SchemaGeradorVisualizacao

    # Atributo para receber o DataFrame injetado
    df: pd.DataFrame = None

    # A assinatura do método _run é adaptada para receber os argumentos nomeados
    def _run(
        self, tipo_grafico: str, colunas: list[str], titulo: str = "Visualização de Dados"
    ) -> str:
        """
        Gera um gráfico com base nos parâmetros fornecidos e nos dados do DataFrame.

        Args:
            tipo_grafico (str): O tipo de gráfico a ser gerado.
            colunas (list[str]): As colunas a serem utilizadas.
            titulo (str, optional): O título para o gráfico. Padrão é "Visualização de Dados".

        Returns:
            str: O caminho para o arquivo de imagem salvo ou uma mensagem de erro detalhada.
        """

        try:
            # Configura o backend do matplotlib para ser não-interativo ('Agg')
            import matplotlib
            matplotlib.use("Agg")
            plt.ioff()  # Desativa o modo interativo para evitar pop-ups de janela

            # Limpa quaisquer figuras ou eixos pré-existentes para evitar sobreposição
            plt.clf()
            plt.close("all")

            # Garante que o diretório de saída exista
            pasta_saida = Path("outputs")
            pasta_saida.mkdir(exist_ok=True)

            if tipo_grafico == "histograma":
                if not colunas:
                    return "[FALHA] É necessário especificar uma coluna para o histograma."

                plt.figure(figsize=(10, 6))
                coluna_selecionada = colunas[0]

                if coluna_selecionada not in self.df.columns:
                    return f"[FALHA] A coluna '{coluna_selecionada}' não existe no DataFrame."

                plt.hist(
                    self.df[coluna_selecionada].dropna(),
                    bins=30,
                    alpha=0.7,
                    color="teal",
                    edgecolor="black",
                )
                plt.title(titulo)
                plt.xlabel(coluna_selecionada)
                plt.ylabel("Contagem")
                plt.grid(axis='y', linestyle='--', alpha=0.7)

            elif tipo_grafico == "multiplos_histogramas":
                # Lógica para determinar quais colunas plotar
                if colunas:
                    # Se o agente especificou colunas, usamos essa lista como base
                    colunas_para_plotar = [
                        col for col in colunas if col in self.df.columns
                    ]
                else:
                    # Caso contrário, selecionamos todas as colunas numéricas automaticamente
                    colunas_para_plotar = self.df.select_dtypes(
                        include=[np.number]
                    ).columns.tolist()

                # Limita o número de subplots para evitar sobrecarga e erros
                if len(colunas_para_plotar) > 30:
                    colunas_para_plotar = colunas_para_plotar[:30]
                    print(
                        f"AVISO: O número de histogramas foi limitado a {len(colunas_para_plotar)} por questões de desempenho."
                    )

                if not colunas_para_plotar:
                    return "[FALHA] Nenhuma coluna numérica válida foi encontrada para a geração dos histogramas."

                # Calcula as dimensões da grade de subplots
                num_cols = min(6, len(colunas_para_plotar))
                num_rows = (len(colunas_para_plotar) + num_cols - 1) // num_cols

                plt.figure(figsize=(20, 4 * num_rows))

                for i, col in enumerate(colunas_para_plotar):
                    plt.subplot(num_rows, num_cols, i + 1)
                    plt.hist(
                        self.df[col].dropna(),
                        bins=30,
                        alpha=0.7,
                        color="teal",
                        edgecolor="black",
                    )
                    plt.title(f"Distribuição de {col}", fontsize=10)
                    plt.xlabel("")
                    plt.ylabel("")
                    plt.xticks(fontsize=7)
                    plt.yticks(fontsize=7)

                plt.suptitle(titulo, fontsize=16, y=0.98)
                plt.tight_layout(rect=[0, 0.03, 1, 0.95])

            elif tipo_grafico == "dispersao":
                if len(colunas) < 2:
                    return "[FALHA] Um gráfico de dispersão exige a especificação de duas colunas (eixo X e eixo Y)."

                plt.figure(figsize=(10, 6))
                col_x, col_y = colunas[0], colunas[1]

                if col_x not in self.df.columns or col_y not in self.df.columns:
                    return f"[FALHA] Pelo menos uma das colunas especificadas não foi encontrada: {col_x}, {col_y}"

                plt.scatter(self.df[col_x], self.df[col_y], alpha=0.6, color="purple")
                plt.title(titulo)
                plt.xlabel(col_x)
                plt.ylabel(col_y)
                plt.grid(True, linestyle='--', alpha=0.7)

            elif tipo_grafico == "boxplot":
                if not colunas:
                    # Comportamento padrão: usa as 5 primeiras colunas numéricas se nenhuma for especificada
                    colunas_alvo = self.df.select_dtypes(
                        include=[np.number]
                    ).columns.tolist()[:5]
                else:
                    colunas_alvo = colunas

                # Filtra para garantir que apenas colunas numéricas sejam usadas
                colunas_numericas_validas = []
                for col in colunas_alvo:
                    if col in self.df.columns and pd.api.types.is_numeric_dtype(self.df[col]):
                        colunas_numericas_validas.append(col)
                    else:
                        print(f"AVISO: A coluna '{col}' foi ignorada para o boxplot por não ser numérica.")

                if not colunas_numericas_validas:
                    return "[FALHA AGENTE] Nenhuma coluna numérica válida foi fornecida ou encontrada para o boxplot. Especifique colunas numéricas."

                plt.figure(figsize=(12, 6))
                dados_para_boxplot = [self.df[col].dropna() for col in colunas_numericas_validas]
                
                plt.boxplot(dados_para_boxplot, labels=colunas_numericas_validas)
                plt.title(titulo)
                plt.ylabel("Distribuição dos Valores")
                plt.xticks(rotation=45, ha="right")
                plt.grid(axis='y', linestyle='--', alpha=0.7)

            elif tipo_grafico == "barras":
                if len(colunas) < 2:
                    return "[FALHA] Um gráfico de barras requer duas colunas: uma categórica (eixo X) e uma numérica (eixo Y)."

                plt.figure(figsize=(12, 6))
                col_categoria, col_valor = colunas[0], colunas[1]

                if col_categoria not in self.df.columns or col_valor not in self.df.columns:
                    return f"[FALHA] Pelo menos uma das colunas especificadas não foi encontrada: {col_categoria}, {col_valor}"

                # Agrupa, soma e pega os 20 maiores valores para visualização
                dados_agrupados = self.df.groupby(col_categoria)[col_valor].sum().nlargest(20)
                dados_agrupados.plot(kind="bar", color="darkorange", edgecolor="black")
                plt.title(titulo)
                plt.xlabel(col_categoria)
                plt.ylabel(f"Soma de {col_valor}")
                plt.xticks(rotation=45, ha="right")
                plt.grid(axis='y', linestyle='--', alpha=0.7)

            else:
                return f"[FALHA] Tipo de gráfico desconhecido: '{tipo_grafico}'. As opções válidas são: histograma, dispersao, boxplot, barras, multiplos_histogramas."

            # Salva a figura gerada em um arquivo
            pasta_saida = Path("outputs")
            pasta_saida.mkdir(exist_ok=True)
            timestamp = str(int(pd.Timestamp.now().timestamp()))
            caminho_arquivo_imagem = pasta_saida / f"visualizacao_{timestamp}.png"

            plt.tight_layout()
            plt.savefig(caminho_arquivo_imagem, dpi=300, bbox_inches="tight", facecolor="white")
            plt.close()  # Libera a memória fechando a figura

            print(f"🖼️ Visualização salva com sucesso em: {caminho_arquivo_imagem}")
            return str(caminho_arquivo_imagem)

        except Exception as e:
            plt.close()  # Garante a limpeza de recursos em caso de erro
            return f"[FALHA CRÍTICA] Ocorreu um erro inesperado ao gerar o gráfico: {e}"