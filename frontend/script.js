// Arquivo: script.js (Versão Modificada)

document.addEventListener('DOMContentLoaded', () => {
    // --- Mapeamento dos Elementos da Interface ---
    const sidebar = document.getElementById('sidebar');
    const toggleSidebarBtn = document.getElementById('toggle-sidebar-btn');
    const menuIcon = document.getElementById('menu-icon');
    const closeIcon = document.getElementById('close-icon');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const fileDropArea = document.getElementById('file-drop-area');
    const fileInput = document.getElementById('file-input');
    const fileNameDisplay = document.getElementById('file-name-display');
    const newAnalysisBtn = document.getElementById('new-chat-btn'); // Renomeado para clareza

    let currentFile = null; // Armazena o arquivo carregado

    // --- Gerenciamento da Barra Lateral ---
    const toggleSidebar = () => {
        sidebar.classList.toggle('collapsed');
        const isCollapsed = sidebar.classList.contains('collapsed');
        
        toggleSidebarBtn.title = isCollapsed ? "Abrir Menu" : "Fechar Menu";
        menuIcon.style.display = isCollapsed ? 'block' : 'none';
        closeIcon.style.display = isCollapsed ? 'none' : 'block';
    };

    toggleSidebarBtn.addEventListener('click', toggleSidebar);

    // Inicia a barra lateral fechada em dispositivos móveis
    if (window.innerWidth <= 768) {
        sidebar.classList.add('collapsed');
    }

    // --- Funcionalidade de "Nova Análise" ---
    const startNewAnalysis = () => {
        // Restaura a mensagem de boas-vindas
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <h1>Assistente de Análise de Dados</h1>
                <p>Para começar, envie um arquivo CSV ou ZIP e faça sua primeira pergunta. Estou pronto para explorar seus dados, gerar gráficos e extrair insights.</p>
            </div>
        `;
        
        // Limpa o arquivo selecionado
        currentFile = null;
        fileNameDisplay.textContent = 'Arraste e solte um arquivo (.csv ou .zip) ou clique aqui para selecionar.';
        fileNameDisplay.classList.remove('file-selected');
        
        // Limpa a caixa de texto
        userInput.value = '';
        
        console.log('Nova sessão de análise iniciada.');
    };

    newAnalysisBtn.addEventListener('click', startNewAnalysis);

    // --- Gerenciamento de Upload de Arquivo (Drag & Drop) ---
    fileDropArea.addEventListener('click', () => fileInput.click());
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, e => e.preventDefault());
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => fileDropArea.classList.add('highlight'));
    });

    ['dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => fileDropArea.classList.remove('highlight'));
    });
    
    fileDropArea.addEventListener('drop', (e) => {
        const file = e.dataTransfer.files[0];
        if (file) handleFileSelection(file);
    });
    
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) handleFileSelection(file);
    });

    const handleFileSelection = (file) => {
        const validExtensions = ['.csv', '.zip'];
        const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        
        if (!validExtensions.includes(fileExtension)) {
            alert('Formato de arquivo inválido. Por favor, selecione um arquivo .csv ou .zip.');
            return;
        }
        
        currentFile = file;
        fileNameDisplay.textContent = `✔️ Arquivo pronto: ${file.name}`;
        fileNameDisplay.classList.add('file-selected');
        console.log('Arquivo selecionado:', file.name);
    };

    // --- Envio de Formulário e Comunicação com a API ---
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = userInput.value.trim();

        if (!question) return;
        if (!currentFile) {
            alert("Por favor, carregue um arquivo (.csv ou .zip) antes de fazer uma pergunta.");
            return;
        }

        appendMessage(question, 'user');
        userInput.value = '';

        const loadingId = appendLoadingIndicator();

        const formData = new FormData();
        formData.append('file', currentFile);
        formData.append('question', question);

        try {
            console.log('Enviando dados para a API...');
            const response = await fetch('/chat/', {
                method: 'POST',
                body: formData,
            });

            removeElementById(loadingId);

            if (!response.ok) {
                const errorData = await response.json().catch(() => null);
                const errorMessage = errorData?.error || `Falha na comunicação com o servidor (Status: ${response.status})`;
                throw new Error(errorMessage);
            }

            const data = await response.json();
            console.log('Resposta da API:', data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            const responseText = data.response || "Análise concluída.";
            appendMessage(responseText, 'agent', data.image_url);

        } catch (error) {
            removeElementById(loadingId);
            console.error('Erro na requisição:', error);
            appendMessage(`❗️ Erro: ${error.message}`, 'agent');
        }
    });
    
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // --- Funções de Manipulação da Interface de Chat ---
    const appendMessage = (text, sender, imageUrl = null) => {
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) welcomeMessage.remove();

        const messageBox = document.createElement('div');
        messageBox.className = `message-box ${sender}`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = sender === 'user' ? 'Você' : 'IA';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (imageUrl) {
            if (text) {
                const textElement = document.createElement('p');
                textElement.textContent = text;
                messageContent.appendChild(textElement);
            }
            
            const chartContainer = document.createElement('div');
            chartContainer.className = 'chart-container';
            
            const img = document.createElement('img');
            img.src = imageUrl;
            img.alt = 'Gráfico gerado pela análise';
            img.title = 'Clique para ampliar';
            img.addEventListener('click', () => openImageModal(imageUrl));
            
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'image-loading';
            loadingDiv.innerHTML = `<div class="loading-spinner"></div><span>Carregando visualização...</span>`;
            
            chartContainer.appendChild(loadingDiv);
            chartContainer.appendChild(img);
            
            img.style.display = 'none';
            img.onload = () => {
                loadingDiv.style.display = 'none';
                img.style.display = 'block';
            };
            img.onerror = () => {
                loadingDiv.innerHTML = '❌ Falha ao carregar a imagem.';
            };
            
            messageContent.appendChild(chartContainer);
        } else {
            messageContent.textContent = text;
        }
        
        messageBox.appendChild(avatar);
        messageBox.appendChild(messageContent);
        chatMessages.appendChild(messageBox);
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };

    const appendLoadingIndicator = () => {
        const loadingId = 'loading-' + Date.now();
        const messageHtml = `
            <div id="${loadingId}" class="message-box agent">
                <div class="avatar">IA</div>
                <div class="message-content">
                    <div class="image-loading" style="background: transparent;">
                        <div class="loading-spinner"></div>
                        <span>Processando sua solicitação...</span>
                    </div>
                </div>
            </div>
        `;
        chatMessages.insertAdjacentHTML('beforeend', messageHtml);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return loadingId;
    };

    const removeElementById = (id) => {
        const element = document.getElementById(id);
        if (element) element.remove();
    };

    // --- Gerenciamento do Modal de Imagem ---
    const imageModal = document.getElementById('image-modal');
    const modalImage = document.getElementById('modal-image');
    const modalCloseBtn = document.getElementById('modal-close');

    const openImageModal = (imageUrl) => {
        imageModal.classList.add('active');
        modalImage.src = imageUrl;
        document.body.style.overflow = 'hidden';
    };

    const closeImageModal = () => {
        imageModal.classList.remove('active');
        document.body.style.overflow = 'auto';
    };

    modalCloseBtn.addEventListener('click', closeImageModal);
    imageModal.addEventListener('click', (e) => {
        if (e.target === imageModal) closeImageModal();
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeImageModal();
    });

    // --- Gerenciamento do Tema (Claro/Escuro) ---
    const themeSwitch = document.getElementById('theme-switch');
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');

    const applyTheme = (theme) => {
        if (theme === 'light') {
            document.body.classList.add('light-theme');
            themeSwitch.checked = true;
        } else {
            document.body.classList.remove('light-theme');
            themeSwitch.checked = false;
        }
    };

    if (savedTheme) {
        applyTheme(savedTheme);
    } else if (prefersDark) {
        applyTheme('dark');
    } else {
        applyTheme('light');
    }

    themeSwitch.addEventListener('change', () => {
        const newTheme = themeSwitch.checked ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
        console.log(`Tema alterado para: ${newTheme}`);
    });

    // --- Gerenciamento de Redimensionamento da Janela ---
    window.addEventListener('resize', () => {
        if (window.innerWidth <= 768 && !sidebar.classList.contains('collapsed')) {
            toggleSidebar();
        }
    });

    // --- Inicialização ---
    console.log('Interface do Assistente de Análise de Dados carregada.');
});