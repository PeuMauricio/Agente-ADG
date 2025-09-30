import os
import threading
import time
from pathlib import Path

import pandas as pd
from crewai import LLM, Agent, Crew, Process, Task
from dotenv import load_dotenv

# <-- CORREÇÃO AQUI
from custom_tool_generico import GeradorVisualizacaoTool, ExecutorCodigoPandas

load_dotenv()


class FluxoEDA:
    """
    Classe central que gerencia e orquestra o fluxo de Análise Exploratória de Dados.
    """

    def __init__(self, caminho_csv: str):
        self.caminho_csv = caminho_csv
        try:
            self.df = pd.read_csv(caminho_csv)
            print(f"✔ Fonte de dados carregada com êxito: {self.caminho_csv}")
            print(f"  - Dimensões do DataFrame: {self.df.shape}")
            print(f"  - Colunas identificadas: {list(self.df.columns)}")
        except Exception as e:
            raise RuntimeError(f"Falha crítica ao carregar o arquivo CSV: {e}")

    def executar(self, pergunta: str) -> dict | str:
        """
        Inicia e gerencia a execução da equipe de agentes (Crew) para responder à
        pergunta do usuário, seguindo uma lógica de segregação de tarefas.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("A chave OPENAI_API_KEY não foi configurada no arquivo .env. A execução não pode continuar.")

        llm_config = LLM(model="gpt-4o-mini", api_key=api_key, temperature=0.1)

        # <-- CORREÇÃO AQUI
        query_tool = ExecutorCodigoPandas()
        query_tool.df = self.df
        plot_tool = GeradorVisualizacaoTool()
        plot_tool.df = self.df

        # --- CONFIGURAÇÃO DOS AGENTES ESPECIALIZADOS ---
        analista_quantitativo = Agent(
            role="Analista de Dados Quantitativo e programador Python",
            goal="Converter perguntas de usuários em código Python executável para extrair insights numéricos e estatísticos de um DataFrame chamado 'df'.",
            backstory=(
                "Você é um cientista de dados metódico, especializado em Análise Exploratória de Dados (EDA). "
                "Sua única fonte de verdade é o DataFrame 'df'. Você opera com lógica pura, ignorando qualquer conhecimento externo. "
                "Sua principal ferramenta é a 'Executor de Código Python para Análise de DataFrame', que você usa para rodar scripts em pandas. "
                "O código que você escreve deve ser preciso e focado em produzir um resultado final na variável 'resultado'. "
                "**DIRETRIZ CRÍTICA**: Se a pergunta não puder ser respondida usando as colunas disponíveis no DataFrame, sua resposta final deve ser exatamente: 'A pergunta não pode ser respondida com os dados fornecidos.' "
                "Você é estritamente um analista de dados; a criação de visualizações está fora do seu escopo. "
                "Seu processo mental segue este padrão rigoroso:\n"
                "Thought: Decomponho a pergunta do usuário. Qual é a melhor abordagem em Python/pandas para encontrar a resposta? "
                "Action: Utilizo a 'Executor de Código Python para Análise de DataFrame' com o script que elaborei. "
                "Action Input: O script Python a ser executado. "
                "Observation: Analiso o output retornado pela ferramenta. "
                "Thought: Com base na 'Observation', formulo uma resposta factual. Se houver um erro, preciso repensar minha estratégia de código. "
            ),
            tools=[query_tool],
            verbose=True,
            memory=True,
            llm=llm_config,
        )

        arquiteto_visual = Agent(
            role="Especialista em Visualização de Dados",
            goal="Gerar um gráfico conforme a solicitação do usuário, utilizando a ferramenta apropriada e retornando exclusivamente o caminho do arquivo de imagem resultante.",
            backstory=(
                "Você é um especialista em visualização de dados com uma única função: transformar pedidos de gráficos em chamadas de ferramenta precisas. "
                "Você **NÃO** interpreta dados, não escreve resumos nem oferece conclusões. Seu único entregável é o caminho do arquivo PNG. "
                "Você utiliza a 'Ferramenta de Geração de Visualizações Gráficas', que requer os parâmetros: tipo_grafico, colunas e titulo. "
                "**PROTOCOLO DE ERRO 1:** Se a ferramenta falhar internamente (ex: tipo de dado incompatível), sua resposta final DEVE ser a mensagem exata: 'Falha na Visualização: Erro interno. Verifique se as colunas selecionadas são adequadas para o tipo de gráfico solicitado.' "
                "**PROTOCOLO DE ERRO 2:** Se a 'Observation' da ferramenta contiver as palavras '[FALHA]', '[INFO]' ou 'Nenhuma coluna numérica válida', você DEVE ABORTAR a tarefa e retornar a seguinte mensagem exata como sua resposta final: 'Falha na Visualização: A solicitação não pôde ser processada. Assegure-se de que as colunas são numéricas e o tipo de gráfico é compatível.'"
            ),
            tools=[plot_tool],
            verbose=True,
            memory=True,
            llm=llm_config,
        )

        sintetizador_de_insights = Agent(
            role="Estrategista de Dados e Revisor de Qualidade",
            goal="Consolidar os resultados das análises e visualizações em uma conclusão coesa, de alto nível e estritamente baseada nos fatos, validando a integridade das informações.",
            backstory=(
                "Você é o revisor final, responsável por transformar dados brutos em inteligência acionável. "
                "Suas responsabilidades são: 1. Validar a coerência dos dados recebidos em relação à pergunta original. 2. Descartar qualquer informação que pareça ser uma alucinação ou que não seja suportada pelos fatos. 3. Utilizar o histórico de análises (memória) para construir uma narrativa, mas **NUNCA** descrever um gráfico ou mencionar caminhos de arquivo na sua resposta. "
                "Sua comunicação deve ser objetiva, baseada apenas nos resultados validados. "
                "Você **NÃO** deve inventar contexto de negócio (ex: 'lucro', 'satisfação do cliente') se esses termos não estiverem explicitamente presentes nos dados analisados."
            ),
            verbose=True,
            memory=True,
            llm=llm_config,
        )

        # --- LÓGICA DE ROTEAMENTO DE TAREFAS (VISUALIZAÇÃO vs. ANÁLISE) ---
        gatilhos_imperativos_grafico = ["desenhe", "crie", "gere", "plote", "exiba"]
        termos_grafico = [
            "gráfico", "grafico", "plot", "visualização", "visualizacao", "chart",
            "distribuição", "distribuicao", "histograma", "boxplot", "dispersão",
            "barras", "scatter"
        ]

        e_pedido_grafico_direto = any(
            gatilho in pergunta.lower() for gatilho in gatilhos_imperativos_grafico
        ) and any(termo in pergunta.lower() for termo in termos_grafico)

        if e_pedido_grafico_direto:
            # ROTA 1: Foco exclusivo na geração de visualização
            tarefa_visualizacao = Task(
                description=(
                    f"Atenda à solicitação de visualização do usuário: '{pergunta}'.\n\n"
                    f"Contexto do DataFrame - Colunas disponíveis: {list(self.df.columns)}\n\n"
                    "DIRETRIZ DE SAÍDA: O Agente de Visualização deve fornecer como resposta final APENAS o caminho do arquivo PNG. Nenhum texto adicional é permitido."
                ),
                expected_output="O caminho absoluto para o arquivo de imagem .png gerado e salvo na pasta 'outputs/'.",
                agent=arquiteto_visual,
            )
            tarefas = [tarefa_visualizacao]
        else:
            # ROTA 2: Foco em análise textual e síntese de conclusões
            tarefa_extracao_dados = Task(
                description=(
                    f"Analise o DataFrame para responder à seguinte pergunta do usuário: '{pergunta}'.\n\n"
                    f"Metadados do Dataset:\n"
                    f"- Dimensões: {self.df.shape}\n"
                    f"- Colunas: {list(self.df.columns)}\n\n"
                    "Sua missão é empregar a ferramenta `Executor de Código Python para Análise de DataFrame` para escrever e executar um script Python que extraia a resposta. "
                    "O resultado deve ser um texto objetivo e conciso, estritamente baseado nos dados. "
                    "Evite suposições ou informações que não possam ser comprovadas pelo DataFrame."
                ),
                expected_output="Um resumo textual claro e factual, contendo as estatísticas e informações relevantes extraídas do DataFrame.",
                agent=analista_quantitativo,
            )
            tarefa_sintese_final = Task(
                description=(
                    "Compile todos os resultados das tarefas anteriores em uma resposta final e coesa, mantendo o foco **exclusivamente nos dados analisados**. "
                    "Evite adicionar qualquer contexto de negócio que não esteja explicitamente presente nos dados. "
                    "\n\nEstrutura da Resposta:\n"
                    "1. Resumo dos principais achados (estatísticas, padrões, outliers, etc.).\n"
                    "2. Se houver análises visuais anteriores (na memória), incorpore os insights delas em sua análise, mas **NUNCA** mencione o arquivo do gráfico ou tente descrever a imagem.\n"
                    "3. Conclusões diretas e objetivas, como correlações encontradas ou a falta delas.\n"
                    "4. Sugestões para próximas etapas de análise (ex: 'sugere-se uma investigação mais profunda dos valores atípicos', 'recomenda-se analisar a relação entre X e Y').\n\n"
                    "Tom: A resposta deve ser clara, profissional e puramente analítica."
                ),
                expected_output="Uma resposta final bem estruturada, rica em insights baseados em dados e livre de especulações de negócio.",
                agent=sintetizador_de_insights,
            )
            tarefas = [tarefa_extracao_dados, tarefa_sintese_final]

        equipe_analitica = Crew(
            agents=[analista_quantitativo, arquiteto_visual, sintetizador_de_insights],
            tasks=tarefas,
            process=Process.sequential,
            verbose=True,
        )

        try:
            resultado_container = [None]
            excecao_container = [None]

            def executar_crew():
                try:
                    resultado_container[0] = equipe_analitica.kickoff()
                except Exception as e:
                    excecao_container[0] = e

            thread_execucao = threading.Thread(target=executar_crew)
            thread_execucao.daemon = True
            thread_execucao.start()
            thread_execucao.join(timeout=300)

            if thread_execucao.is_alive():
                print("⏳ A execução excedeu o tempo limite de 5 minutos.")
                return "A análise está demorando mais do que o previsto. Por favor, tente uma pergunta mais específica."

            if excecao_container[0]:
                raise excecao_container[0]

            resultado_bruto = resultado_container[0]
            texto_resultado = str(resultado_bruto.output if hasattr(resultado_bruto, "output") else resultado_bruto)

            if e_pedido_grafico_direto:
                pasta_saida = Path("outputs")
                arquivos_grafico = list(pasta_saida.glob("*.png")) if pasta_saida.exists() else []

                if arquivos_grafico:
                    grafico_recente = max(arquivos_grafico, key=lambda p: p.stat().st_mtime)
                    nome_grafico = grafico_recente.name
                    print(f"🖼️ Visualização gerada com sucesso: {nome_grafico}")
                    return {
                        "text": "",
                        "image_url": f"http://localhost:8000/outputs/{nome_grafico}",
                    }
                return "O agente tentou criar a visualização, mas o arquivo final não foi encontrado. Consulte os logs para mais detalhes."
            else:
                print(f"✔ Análise concluída. Resumo: {texto_resultado[:200]}...")
                return {"response": texto_resultado}

        except Exception as e:
            print(f"🚨 Erro crítico durante a execução da equipe: {e}")
            import traceback
            traceback.print_exc()
            try:
                import matplotlib.pyplot as plt
                plt.close("all")
            except:
                pass
            return {
                "error": f"Ocorreu um erro durante a análise: {str(e)}. Tente reformular sua pergunta ou verifique os dados."
            }
        finally:
            try:
                import matplotlib.pyplot as plt
                plt.close("all")
            except:
                pass