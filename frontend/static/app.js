const API_BASE = API_BASE_URL.replace(/\/$/, '');
let currentDocumentId = null;

// API Request Helper
async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    const headers = {
        'Authorization': `Bearer ${token}`
    };

    // Sadece FormData değilse Content-Type ekle
    if (options.body && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    // Header'ları birleştir
    options.headers = { ...headers, ...options.headers };

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        
        if (response.status === 401) {
            // Token süresi dolmuş veya geçersiz
            localStorage.removeItem('token');
            window.location.href = 'index.html';
            throw new Error('Unauthorized');
        }

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'API Error');
        }
        return data;
    } catch (err) {
        console.error('API Error:', err);
        throw err;
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Token kontrolü
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }

    // Token'dan email'i okuma (JWT parse, basitçe)
    try {
        const payloadBase64 = token.split('.')[1];
        const payload = JSON.parse(atob(payloadBase64));
        const storedEmail = localStorage.getItem('userEmail');
        if (storedEmail) {
            document.getElementById('user-email-display').textContent = storedEmail;
        } else if (payload.email) {
            document.getElementById('user-email-display').textContent = payload.email;
        } else if (payload.sub) {
            document.getElementById('user-email-display').textContent = payload.sub;
        }
    } catch (e) {
        console.warn("Token parse edilemedi", e);
    }

    // Çıkış yap
    document.getElementById('logout-btn').addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('token');
        localStorage.removeItem('userEmail');
        window.location.href = 'index.html';
    });

    // 2. Dökümanları Yükle
    await fetchDocuments();

    // 3. Geçmiş mesajları yükle
    await fetchChatHistory();

    // Event Listeners
    setupEventListeners();
});

// Event Listeners Kurulumu
function setupEventListeners() {
    // Upload Butonu
    const uploadBtn = document.getElementById('upload-btn');
    const fileInput = document.getElementById('file-upload-input');

    uploadBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        uploadBtn.classList.add('opacity-50', 'cursor-not-allowed');
        uploadBtn.textContent = 'Yükleniyor...';

        try {
            await apiRequest('/documents/upload', {
                method: 'POST',
                body: formData
            });
            // Başarılı yüklemeden sonra listeyi yenile
            await fetchDocuments();
        } catch (error) {
            alert('Döküman yüklenirken hata oluştu: ' + error.message);
        } finally {
            // Butonu eski haline getir
            uploadBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            uploadBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg> Yükle`;
            fileInput.value = ''; // Reset input
        }
    });

    // Chat Input (Enter key & Send Button)
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');

    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    });

    sendBtn.addEventListener('click', () => {
        handleSendMessage();
    });
}

// Dökümanları Getir ve Sol Paneli Doldur
async function fetchDocuments() {
    try {
        const response = await apiRequest('/documents');
        const docs = response.documents || [];
        const listEl = document.getElementById('document-list');
        listEl.innerHTML = ''; // Temizle

        if (docs.length === 0) {
            listEl.innerHTML = '<li class="text-xs text-text-muted p-2">Henüz döküman yok.</li>';
            return;
        }

        // Eğer seçili bir döküman yoksa, ilkini otomatik seç
        if (!currentDocumentId && docs.length > 0) {
            currentDocumentId = docs[0].id;
            document.getElementById('current-doc-title').textContent = docs[0].filename;
        }

        docs.forEach(doc => {
            const isReady = doc.status === 'ready' || doc.status === 'completed'; // Backend'e göre değişebilir
            const isSelected = doc.id === currentDocumentId;

            const li = document.createElement('li');
            li.className = `relative cursor-pointer rounded-md p-3 flex items-center gap-3 transition-colors ${isSelected ? 'bg-bg-primary' : 'hover:bg-bg-primary group'}`;
            li.onclick = () => selectDocument(doc);

            // Active bar (sol şerit)
            let activeBarHtml = '';
            if (isSelected) {
                activeBarHtml = `<div class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-2/3 bg-accent-signal rounded-r-md"></div>`;
            }

            // Durum noktası
            const dotColor = isReady ? 'bg-accent-data' : 'bg-accent-signal animate-pulse';
            
            li.innerHTML = `
                ${activeBarHtml}
                <div class="w-2 h-2 rounded-full ${dotColor} ${isSelected ? 'ml-1' : ''}"></div>
                <span class="text-sm font-medium ${isSelected ? 'text-text-primary' : 'text-text-muted group-hover:text-text-primary'} truncate" title="${doc.filename}">${doc.filename}</span>
            `;

            listEl.appendChild(li);
        });
    } catch (error) {
        console.error("Dökümanlar çekilemedi", error);
    }
}

// Döküman Seçimi
function selectDocument(doc) {
    if (currentDocumentId === doc.id) return;
    
    currentDocumentId = doc.id;
    document.getElementById('current-doc-title').textContent = doc.filename;
    
    // UI Güncelleme için listeyi tekrar render et (basit yaklaşım)
    fetchDocuments();
    
    // Yeni dökümanın geçmiş mesajlarını yükle
    fetchChatHistory();
    
    // Trace panelini temizle
    document.getElementById('retrieval-trace').innerHTML = '';
}

// Geçmiş Mesajları Getir
async function fetchChatHistory() {
    if (!currentDocumentId) {
        document.getElementById('chat-messages').innerHTML = '<div class="text-sm text-text-muted p-4 text-center">Sohbeti görmek için bir döküman seçin.</div>';
        return;
    }
    
    try {
        const response = await apiRequest(`/chat/history?document_id=${currentDocumentId}`);
        const historyRows = response.history || [];
        const messagesEl = document.getElementById('chat-messages');
        messagesEl.innerHTML = '';

        if (historyRows.length > 0) {
            historyRows.forEach(row => {
                appendMessageToUI(row.question, true, row.created_at || new Date().toISOString());
                appendMessageToUI(row.answer, false, row.created_at || new Date().toISOString());
            });
        }
    } catch (error) {
        console.error("Mesaj geçmişi çekilemedi", error);
    }
}

// Mesaj Gönderme
async function handleSendMessage() {
    const chatInput = document.getElementById('chat-input');
    const question = chatInput.value.trim();

    if (!question) return;
    if (!currentDocumentId) {
        alert("Lütfen önce bir döküman seçin.");
        return;
    }

    // 1. Optimistic UI: Kullanıcı mesajını hemen ekle
    chatInput.value = '';
    appendMessageToUI(question, true, new Date().toISOString());

    try {
        // 2. API Çağrısı
        const response = await apiRequest('/chat/query', {
            method: 'POST',
            body: JSON.stringify({
                question: question,
                document_id: currentDocumentId
            })
        });

        // 3. Sistem cevabını ekle
        appendMessageToUI(response.answer, false, new Date().toISOString());

        // 4. Retrieval Trace Panelini Güncelle
        updateRetrievalTrace(response.sources || []);

    } catch (error) {
        appendMessageToUI("Bir hata oluştu: " + error.message, false, new Date().toISOString());
    }
}

// Mesajı UI'a Ekleme (Orta Panel)
function appendMessageToUI(text, isUser, timestampStr) {
    const messagesEl = document.getElementById('chat-messages');
    
    // Basit saat formatı
    const dateObj = new Date(timestampStr);
    const timeString = isNaN(dateObj.getTime()) ? 'Şimdi' : dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const msgDiv = document.createElement('div');
    msgDiv.className = isUser ? 'flex justify-end' : 'flex justify-start';

    if (isUser) {
        msgDiv.innerHTML = `
            <div class="max-w-[80%] flex flex-col items-end">
                <div class="bg-accent-signal text-[#10141A] rounded-2xl rounded-tr-sm px-4 py-3 text-sm font-medium leading-relaxed shadow-sm whitespace-pre-wrap">${escapeHtml(text)}</div>
                <div class="mt-1.5 mr-1 text-[10px] text-text-muted font-mono">${timeString}</div>
            </div>
        `;
    } else {
        msgDiv.innerHTML = `
            <div class="max-w-[80%]">
                <div class="bg-surface border border-border-subtle rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-black font-medium leading-relaxed shadow-sm whitespace-pre-wrap">${escapeHtml(text)}</div>
                <div class="mt-1.5 ml-1 text-[10px] text-text-muted font-mono">${timeString}</div>
            </div>
        `;
    }

    messagesEl.appendChild(msgDiv);
    // Scroll to bottom
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

// Retrieval Trace'i Güncelleme (Sağ Panel)
function updateRetrievalTrace(sources) {
    const traceEl = document.getElementById('retrieval-trace');
    traceEl.innerHTML = '';

    if (!sources || sources.length === 0) {
        traceEl.innerHTML = '<div class="text-xs text-text-muted">Bu cevap için kaynak kullanılmadı.</div>';
        return;
    }

    sources.forEach(source => {
        // İlk ~80 karakteri al
        let previewText = source.content || source.text || '';
        if (previewText.length > 80) {
            previewText = previewText.substring(0, 80) + '...';
        }

        // Skor 0-1 arası farz ediliyor
        const score = source.similarity_score || source.similarity || source.score || 0;
        const widthPercent = Math.min(Math.max(score * 100, 0), 100);

        const chunkDiv = document.createElement('div');
        chunkDiv.className = 'space-y-2';
        
        chunkDiv.innerHTML = `
            <div class="text-xs font-mono text-text-muted line-clamp-3 bg-bg-primary p-2 rounded border border-border-subtle" title="${escapeHtml(source.content || source.text || '')}">
                ${escapeHtml(previewText)}
            </div>
            <div class="flex items-center gap-2">
                <div class="flex-1 h-1.5 bg-bg-primary rounded-full overflow-hidden">
                    <div class="h-full bg-accent-data rounded-full" style="width: ${widthPercent}%;"></div>
                </div>
                <span class="text-[10px] font-mono text-accent-data">${score.toFixed(2)}</span>
            </div>
        `;

        traceEl.appendChild(chunkDiv);
    });
}

// Basit XSS koruması
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
