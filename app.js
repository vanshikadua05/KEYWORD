document.addEventListener('DOMContentLoaded', function() {
    const textForm = document.getElementById('text-form');
    const textInput = document.getElementById('text-input');
    const fileInput = document.getElementById('file-input');
    const clearFileBtn = document.getElementById('clear-file-btn');
    const previewTextContainer = document.getElementById('preview-text-container');
    const extractedTextPreview = document.getElementById('extracted-text-preview');
    const numKeywords = document.getElementById('num-keywords');
    const numTopics = document.getElementById('num-topics');
    const minTopicWords = document.getElementById('min-topic-words');
    const saveToDb = document.getElementById('save-to-db');
    const sampleTextBtn = document.getElementById('sample-text-btn');
    const viewHistoryBtn = document.getElementById('view-history-btn');
    const analyzeBtn = document.getElementById('analyze-btn');
    const resultsSection = document.getElementById('results-section');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    const exportBtn = document.getElementById('export-btn');
    const textTab = document.getElementById('text-tab');
    const fileTab = document.getElementById('file-tab');
    const textInputPanel = document.getElementById('text-input-panel');
    const fileInputPanel = document.getElementById('file-input-panel');
    const historyModal = new bootstrap.Modal(document.getElementById('history-modal'));
    const historyLoading = document.getElementById('history-loading');
    const historyContent = document.getElementById('history-content');
    const historyError = document.getElementById('history-error');
    const historyErrorText = document.getElementById('history-error-text');
    const historyTableBody = document.getElementById('history-table-body');
    const noHistory = document.getElementById('no-history');
  
    const wordCount = document.getElementById('word-count');
    const uniqueWordCount = document.getElementById('unique-word-count');
    const sentenceCount = document.getElementById('sentence-count');
    const avgWordsPerSentence = document.getElementById('avg-words-per-sentence');
    const avgWordLength = document.getElementById('avg-word-length');
    
    const chartColors = [
        '#198754'
    ];
    
    let keywordsChart = null;
    
    const sampleText = `Artificial intelligence (AI) is intelligence demonstrated by machines, unlike the natural intelligence displayed by humans and animals, which involves consciousness and emotionality. The distinction between the former and the latter categories is often revealed by the acronym chosen. 'Strong' AI is usually labelled as artificial general intelligence (AGI) while attempts to emulate 'natural' intelligence have been called artificial biological intelligence (ABI). Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term "artificial intelligence" is often used to describe machines that mimic "cognitive" functions that humans associate with the human mind, such as "learning" and "problem solving".

As machines become increasingly capable, tasks considered to require "intelligence" are often removed from the definition of AI, a phenomenon known as the AI effect. A quip in Tesler's Theorem says "AI is whatever hasn't been done yet." For instance, optical character recognition is frequently excluded from things considered to be AI, having become a routine technology. Modern machine capabilities generally classified as AI include successfully understanding human speech, competing at the highest level in strategic game systems (such as chess and Go), and also impacting outcomes in military simulations.

In the twenty-first century, AI techniques have experienced a resurgence following concurrent advances in computer power, large amounts of data, and theoretical understanding; and AI techniques have become an essential part of the technology industry, helping to solve many challenging problems in computer science, software engineering and operations research.`;
    
    textForm.addEventListener('submit', function(e) {
        e.preventDefault();
        if (fileTab.classList.contains('active') && fileInput.files.length > 0) {
            uploadAndAnalyzeFile();
        } else {
            analyzeText();
        }
    });
    
    sampleTextBtn.addEventListener('click', function() {
        textInput.value = sampleText;
        new bootstrap.Tab(textTab).show();
    });
    
    
    exportBtn.addEventListener('click', exportResults);
   
    fileInput.addEventListener('change', function() {
        if (this.files.length > 0) {
            const file = this.files[0];
            previewTextContainer.classList.add('d-none');
            
            extractedTextPreview.textContent = `Selected file: ${file.name} (${formatFileSize(file.size)})`;
            previewTextContainer.classList.remove('d-none');
        } else {
            previewTextContainer.classList.add('d-none');
        }
    });
    
    clearFileBtn.addEventListener('click', function() {
        fileInput.value = '';
        previewTextContainer.classList.add('d-none');
    });
    
    function analyzeText() {
        const text = textInput.value.trim();
        
        if (text.length < 50) {
            showError('Please enter more text (at least 50 characters) for accurate analysis.');
            return;
        }
        loadingIndicator.classList.remove('d-none');
        resultsSection.classList.add('d-none');
        errorMessage.classList.add('d-none');
        analyzeBtn.disabled = true;
        
        currentAnalysisId = null;
        
        const params = {
            text: text,
            num_keywords: numKeywords.value,
            num_topics: numTopics.value,
            min_topic_words: minTopicWords.value
        };
        
        fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(params)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (data.analysis_id) {
                currentAnalysisId = data.analysis_id;
            }
            
            displayResults(data);
        })
        .catch(error => {
            showError('Error analyzing text: ' + error.message);
        })
        .finally(() => {
            loadingIndicator.classList.add('d-none');
            analyzeBtn.disabled = false;
        });
    }
    
    function displayResults(data) {
      
        updateTextStats(data.stats);
        
    
        displayKeywords(data.keywords);
        
        displayTopics(data.topics);
        
       
        resultsSection.classList.remove('d-none');
    
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    function updateTextStats(stats) {
        wordCount.textContent = stats.word_count;
        uniqueWordCount.textContent = stats.unique_word_count;
        sentenceCount.textContent = stats.sentence_count;
        avgWordsPerSentence.textContent = stats.avg_words_per_sentence;
    }
    
  
    function displayKeywords(keywords) {
        const keywordsList = document.getElementById('keywords-list');
        keywordsList.innerHTML = '';
        
        keywords.forEach((keyword, index) => {
            const keywordBadge = document.createElement('span');
            keywordBadge.classList.add('badge', 'keyword-badge', 'me-2', 'mb-2');
            keywordBadge.style.backgroundColor = chartColors[index % chartColors.length];
            keywordBadge.innerHTML = `${keyword.text} <span class="keyword-count">(${keyword.count})</span>`;
            keywordsList.appendChild(keywordBadge);
        });
        
        const keywordsData = {
            labels: keywords.map(k => k.text),
            datasets: [{
                label: 'Keyword Frequency',
                data: keywords.map(k => k.count),
                backgroundColor: keywords.map((_, i) => chartColors[i % chartColors.length]),
                borderColor: keywords.map((_, i) => chartColors[i % chartColors.length]),
                borderWidth: 1
            }]
        };
        
        const keywordsCtx = document.getElementById('keywords-chart').getContext('2d');
    
        if (keywordsChart) {
            keywordsChart.destroy();
        }
        const ctx = document.getElementById('keywords-chart').getContext('2d');
        keywordsChart = new Chart(keywordsCtx, {
            type: 'bar',
            data: keywordsData,
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Frequency'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Frequency: ${context.raw}`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    function displayTopics(topics) {
        const topicsContainer = document.getElementById('topics-container');
        topicsContainer.innerHTML = '';
        
        topics.forEach((topic, index) => {
            const topicCard = document.createElement('div');
            topicCard.classList.add('card', 'mb-3', 'topic-card');
            
            const topicHeader = document.createElement('div');
            topicHeader.classList.add('card-header', 'bg-secondary', 'text-white');
            topicHeader.innerHTML = `<h5 class="mb-0">Topic ${topic.topic_id}</h5>`;
            
            const topicBody = document.createElement('div');
            topicBody.classList.add('card-body');
            
            const topicWords = document.createElement('div');
            topicWords.classList.add('topic-words');
            
            topic.words.forEach(word => {
                const wordSpan = document.createElement('span');
                wordSpan.classList.add('topic-word');
                wordSpan.style.fontSize = `${Math.max(1, word.weight * 2)}em`;
                wordSpan.style.opacity = `${Math.max(0.5, word.weight)}`;
                wordSpan.style.color = chartColors[index % chartColors.length];
                wordSpan.textContent = word.text;
                topicWords.appendChild(wordSpan);
                
                topicWords.appendChild(document.createTextNode(' '));
            });
            
            topicBody.appendChild(topicWords);
            topicCard.appendChild(topicHeader);
            topicCard.appendChild(topicBody);
            topicsContainer.appendChild(topicCard);
        });
    }
    
    function exportResults() {
      
        const now = new Date();
        const timestamp = now.toISOString().replace(/[:.]/g, '-').substring(0, 19);
        
        
        const stats = {
            wordCount: wordCount.textContent,
            uniqueWordCount: uniqueWordCount.textContent,
            sentenceCount: sentenceCount.textContent,
            avgWordsPerSentence: avgWordsPerSentence.textContent,
            avgWordLength: avgWordLength.textContent
        };
        
        const keywordsList = Array.from(document.querySelectorAll('.keyword-badge'))
            .map(badge => badge.textContent.trim());
        
        const topics = Array.from(document.querySelectorAll('.topic-card'))
            .map(card => {
                const topicName = card.querySelector('.card-header h5').textContent;
                const words = Array.from(card.querySelectorAll('.topic-word'))
                    .map(word => word.textContent.trim());
                return { topicName, words };
            });
           
        let exportContent = `# NLP Text Analysis Results\n\n`;
        exportContent += `Generated: ${now.toLocaleString()}\n`;
        
        exportContent += `\n`;
        
        exportContent += `## Text Statistics\n`;
        exportContent += `- Word Count: ${stats.wordCount}\n`;
        exportContent += `- Unique Word Count: ${stats.uniqueWordCount}\n`;
        exportContent += `- Sentence Count: ${stats.sentenceCount}\n`;
        exportContent += `- Average Words per Sentence: ${stats.avgWordsPerSentence}\n`;
       
        
        exportContent += `## Keywords\n`;
        keywordsList.forEach(keyword => {
            exportContent += `- ${keyword}\n`;
        });
        exportContent += `\n`;
        
        exportContent += `## Topics\n`;
        topics.forEach(topic => {
            exportContent += `### ${topic.topicName}\n`;
            topic.words.forEach(word => {
                exportContent += `- ${word}\n`;
            });
            exportContent += `\n`;
        });
       
        const blob = new Blob([exportContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `text-analysis-${timestamp}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    
    function uploadAndAnalyzeFile() {
      
        if (fileInput.files.length === 0) {
            showError('Please select a file to upload.');
            return;
        }
        
        const file = fileInput.files[0];
     
        if (file.size > 10 * 1024 * 1024) {
            showError('File size exceeds the maximum limit of 10MB.');
            return;
        }
     
        const formData = new FormData();
        formData.append('file', file);
        formData.append('num_keywords', numKeywords.value);
        formData.append('num_topics', numTopics.value);
        formData.append('min_topic_words', minTopicWords.value);
        
        loadingIndicator.classList.remove('d-none');
        resultsSection.classList.add('d-none');
        errorMessage.classList.add('d-none');
        analyzeBtn.disabled = true;
      
        currentAnalysisId = null;
        
        fetch('/upload-file', {
            method: 'POST',
            body: formData
        })
        
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
           
            if (data.analysis_id) {
                currentAnalysisId = data.analysis_id;
            }
            
            if (data.extracted_text) {
                textInput.value = data.extracted_text;
            }
            
            displayResults(data);
            
            const fileInfo = `Analyzed file: ${data.filename} (${formatFileSize(file.size)})`;
            extractedTextPreview.textContent = fileInfo;
        })
        .catch(error => {
            showError('Error processing file: ' + error.message);
        })
        .finally(() => {
            loadingIndicator.classList.add('d-none');
            analyzeBtn.disabled = false;
        });
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function showError(message) {
        errorText.textContent = message;
        errorMessage.classList.remove('d-none');
        loadingIndicator.classList.add('d-none');
        resultsSection.classList.add('d-none');
    }
});
