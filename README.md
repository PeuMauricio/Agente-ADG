🧠 Assistente de Análise de Dados com IA
Um sistema avançado de Agentes Autônomos, construído com CrewAI, projetado para realizar Análise Exploratória de Dados (EDA) de forma inteligente e genérica. Ele aceita qualquer arquivo CSV (ou um ZIP contendo um CSV) e responde a perguntas em linguagem natural, executando análises estatísticas e gerando visualizações de dados precisas.
O projeto foi desenvolvido com foco em robustez e eficiência, implementando uma arquitetura de fluxo de trabalho que minimiza a instabilidade dos LLMs e otimiza o consumo de tokens, garantindo respostas puramente factuais e baseadas nos dados fornecidos.
🚀 Tecnologias e Ferramentas
<p align='center'>
<img loading="lazy" src="https://skillicons.dev/icons?i=python,fastapi,git,github,js,html,css,md,vscode"/>
</p>
<p align='center'>
<img src="https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white" alt="Badge Pandas">
<img src="https://img.shields.io/badge/Matplotlib-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=black" alt="Badge Matplotlib">
<img src="https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white" alt="Badge NumPy">
</p>
Orquestração de Agentes: CrewAI
Modelo de Linguagem: OpenAI (GPT-4o-mini)
Análise e Visualização de Dados: Pandas, Matplotlib, Seaborn
🏛️ Arquitetura e Funcionalidades
O sistema opera com uma arquitetura de Segregação de Tarefas e uma equipe de três agentes especializados, cada um com uma missão clara.
1. A Equipe de Agentes Analíticos
Agente	Missão Principal
Analista Quantitativo	Converte perguntas em código Python (pandas) para extrair estatísticas (média, desvio padrão, outliers) e fatos numéricos dos dados.
Arquiteto Visual	Especialista em traduzir solicitações de visualização em gráficos (arquivos .png), seguindo o Fluxo de Visualização.
Sintetizador de Insights	Consolida os resultados factuais (incluindo insights de gráficos armazenados na memória) em conclusões estratégicas, seguindo o Fluxo de Análise.
2. Mecanismos de Estabilidade e Eficiência
A confiabilidade do assistente é assegurada por múltiplos mecanismos de controle:
Roteamento de Fluxo (Anti-Confusão): O sistema identifica a intenção do usuário (análise textual ou visualização) e direciona a tarefa para um fluxo de trabalho exclusivo. Uma pergunta analítica nunca gera um gráfico, e um pedido de gráfico nunca retorna uma análise textual, eliminando a ambiguidade e a geração de respostas incorretas.
Validação de Parâmetros com Pydantic: A GeradorVisualizacaoTool utiliza um esquema Pydantic para validar rigorosamente os parâmetros tipo_grafico, colunas e titulo, prevenindo erros e loops de tentativa e erro por parte do agente.
Tratamento Inteligente de Colunas: As ferramentas de visualização filtram automaticamente colunas não numéricas e limitam o número de gráficos gerados de uma só vez, evitando erros de execução (runtime errors) e garantindo performance.
Captura Automática de Resultado: A ferramenta ExecutorCodigoPandas foi aprimorada para capturar automaticamente o resultado da última linha de um script Python, atribuindo-o à variável resultado. Isso evita que o agente analítico entre em loops por não conseguir extrair a informação desejada.
Protocolos de Falha: O Arquiteto Visual é instruído com protocolos de erro claros em seu prompt. Em caso de falha, ele retorna uma mensagem de erro útil ao invés de tentar repetidamente, economizando tokens e tempo.
🛠️ Como Executar o Projeto Localmente
Siga os passos abaixo para configurar e executar o assistente em sua máquina.
Pré-requisitos
Python 3.8 ou superior
Uma chave de API da OpenAI
1. Configuração do Ambiente
code
Bash
# 1. Clone este repositório
git clone https://github.com/WFredTD/eda_agent_generic.git
cd eda_agent_generic

# 2. Crie e ative um ambiente virtual
python -m venv .venv
# No Linux/macOS:
source .venv/bin/activate
# No Windows:
.venv\Scripts\activate

# 3. Instale todas as dependências
pip install -r requirements.txt
2. Configuração da Chave de API
Crie um arquivo chamado .env na raiz do projeto e adicione sua chave de API da OpenAI da seguinte forma:
code
Env
OPENAI_API_KEY="sua-chave-de-api-aqui"
3. Diagnóstico do Ambiente (Opcional, mas recomendado)
Antes de iniciar, você pode rodar o script de diagnóstico para garantir que tudo está configurado corretamente:
code
Bash
python debug_setup.py
4. Execução do Servidor
Inicie a aplicação FastAPI com o Uvicorn. O servidor estará disponível em http://127.0.0.1:8000.
code
Bash
uvicorn api:app --reload
5. Acesso à Interface
Abra seu navegador e acesse o seguinte endereço:
code
Code
http://127.0.0.1:8000
Agora você pode arrastar um arquivo CSV ou ZIP (como Kaggle - Credit Card Fraud.zip ou AmesHousing.csv) para a interface e começar a fazer perguntas ao seu assistente de análise de dados.
📄 Licença
Este projeto é distribuído sob a licença MIT. Sinta-se à vontade para usar, modificar e distribuir o código, contanto que o aviso de direitos autorais e a licença original sejam preservados.
