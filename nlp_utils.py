import nltk
import spacy
import logging
from collections import Counter
from string import punctuation
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import re

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

try:
    nlp = spacy.load('en_core_web_sm')
except OSError:
   
    import subprocess
    subprocess.call(['python', '-m', 'spacy', 'download', 'en_core_web_sm'])
    nlp = spacy.load('en_core_web_sm')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

logger = logging.getLogger(__name__)

def preprocess_text(text):
    #cleaning text
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = text.lower()
    return text

def extract_keywords(text, num_keywords=10):

    try:
        processed_text = preprocess_text(text)
        is_short_text = len(processed_text.split()) < 100
        if is_short_text:
            adjusted_num_keywords = max(3, min(5, num_keywords))
        else:
            adjusted_num_keywords = num_keywords
        try:
           
            doc = nlp(processed_text)
            candidate_keywords = []
            entity_keywords = []  
            for ent in doc.ents:
                entity_text = ent.text.lower()
                entity_keywords.append(entity_text)
                candidate_keywords.append(entity_text)  
            for chunk in doc.noun_chunks:
                chunk_text = chunk.text.lower()
                candidate_keywords.append(chunk_text)
        
            pos_tags_priority = {'NOUN': 3, 'PROPN': 3, 'ADJ': 2, 'VERB': 1}
            for token in doc:
                if token.pos_ in pos_tags_priority and not token.is_stop:
                    for _ in range(pos_tags_priority[token.pos_]):
                        candidate_keywords.append(token.text.lower())
            try:
                stop_words = set(stopwords.words('english'))
            except Exception:
                stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'this', 'that', 'in', 'on', 'at', 'to', 'is', 'are', 'was', 'were'}
            
            
            keyword_freq = Counter(candidate_keywords)
            
            # Filter and normalize counts
            filtered_freq = Counter()
            for word, count in keyword_freq.items():
                if len(word) >= 2:
                    filtered_freq[word] = count
            
            # Apply named entity boost without changing base frequency
            for keyword in entity_keywords:
                if keyword.lower() in filtered_freq:
                    filtered_freq[keyword.lower()] += 1
            
            keyword_freq = filtered_freq
            
           
            if is_short_text:
                tokens = [t.text.lower() for t in doc if not t.is_stop and t.is_alpha]
                for i in range(len(tokens) - 1):
                    bigram = f"{tokens[i]} {tokens[i+1]}"
                    if len(tokens[i]) > 2 and len(tokens[i+1]) > 2:
                        keyword_freq[bigram] += 1
            top_keywords = keyword_freq.most_common(adjusted_num_keywords)
            
        except Exception as e:
            logger.warning(f"SpaCy keyword extraction failed, using fallback method: {str(e)}")
            words = processed_text.split()
            try:
                stop_words = set(stopwords.words('english'))
            except Exception:
                stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'this', 'that', 'in', 'on', 'at', 'to', 'is', 'are', 'was', 'were'}
            filtered_words = [word.lower() for word in words if word.lower() not in stop_words and len(word) >= 2]
            bigrams = []
            if is_short_text:
                for i in range(len(filtered_words) - 1):
                    if (len(filtered_words[i]) >= 2 and len(filtered_words[i+1]) >= 2):
                        bigram = f"{filtered_words[i]} {filtered_words[i+1]}"
                        bigrams.append(bigram)
            keyword_freq = Counter(filtered_words)
            for bigram in bigrams:
                if bigram not in keyword_freq:
                    keyword_freq[bigram] = 0
                keyword_freq[bigram] += 2 
            if is_short_text:
                new_counts = {}
                for word in keyword_freq:
                    if len(word) > 6: 
                        new_counts[word] = keyword_freq[word] + 1  
                keyword_freq.update(new_counts)
            
            top_keywords = keyword_freq.most_common(adjusted_num_keywords)
        if top_keywords:
           
            max_freq = top_keywords[0][1] if top_keywords else 1
            keywords_with_scores = [
                {
                    'text': keyword,
                    'score': count / max_freq,
                    'count': count
                }
                for keyword, count in top_keywords
            ]
            
            return keywords_with_scores
        else:
            return [{'text': 'No significant keywords found', 'score': 1.0, 'count': 1}]
    
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        return [{'text': 'Error extracting keywords', 'score': 1.0, 'count': 1}]

def extract_topics(text, num_topics=5, num_words=5):
    try:
        processed_text = preprocess_text(text)
        simple_sentences = []
        for sent in re.split(r'(?<=[.!?])\s+', processed_text):
            if sent.strip():
                simple_sentences.append(sent.strip())
        try:
            sentences = sent_tokenize(processed_text)
        except Exception as e:
            logger.warning(f"NLTK sentence tokenize failed, using simple method: {str(e)}")
            sentences = simple_sentences
        
        text_is_short = len(processed_text.split()) < 100
        if len(sentences) < 3:
            if text_is_short and len(processed_text.split()) > 20:
                artificial_sentences = []
                words = processed_text.split()
                chunk_size = max(5, min(10, len(words) // 3))  
                
                for i in range(0, len(words), chunk_size):
                    chunk = ' '.join(words[i:i+chunk_size])
                    if chunk.strip():
                        artificial_sentences.append(chunk)
                
                if len(artificial_sentences) >= 3:
                    sentences = artificial_sentences
                else:
                    return [{"topic_id": 1, "words": [{"text": "Text too short for effective topic modeling", "weight": 1.0}]}]
            elif len(processed_text.split()) <= 20:
                return [{"topic_id": 1, "words": [{"text": "Text too short for topic modeling", "weight": 1.0}]}]
        try:
            stop_words = set(stopwords.words('english'))
        except Exception:
            stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'this', 'that', 'in', 'on', 'at', 'to', 'is', 'are', 'was', 'were'}
        vectorizer = CountVectorizer(
            stop_words='english',
            max_features=1000,
            max_df=0.95, 
            min_df=1      
        )
        try:
            dtm = vectorizer.fit_transform(sentences)
            
            if dtm.shape[0] < num_topics or dtm.shape[1] < num_words:
                num_topics = min(num_topics, max(1, dtm.shape[0] - 1))
                num_words = min(num_words, max(1, dtm.shape[1]))
            lda = LatentDirichletAllocation(
                n_components=num_topics,
                random_state=42,
                max_iter=20,      
                learning_method='online',
                learning_offset=10.0, 
                doc_topic_prior=0.9,  
                topic_word_prior=0.9  
            ) 
            lda.fit(dtm)
            feature_names = vectorizer.get_feature_names_out()
            topics = []
            for topic_idx, topic in enumerate(lda.components_):
               
                top_word_indices = topic.argsort()[:-num_words-1:-1]
                top_words = [feature_names[i] for i in top_word_indices]
                word_objects = []
                total_weight = sum(topic[top_word_indices])
                
                for i, word in enumerate(top_words):
                    word_objects.append({
                        "text": word,
                        "weight": float(topic[top_word_indices[i]] / total_weight)
                    })
                topics.append({
                    "topic_id": topic_idx + 1,
                    "words": word_objects
                })
            return topics
        
        except Exception as e:
            logger.error(f"Error in LDA topic modeling: {str(e)}")
            all_text = ' '.join(sentences)
            words = all_text.split()
            filtered_words = [w.lower() for w in words if w.lower() not in stop_words and len(w) > 3]
            word_counts = Counter(filtered_words)
            common_words = word_counts.most_common(num_topics * num_words)
            topics = []
            for i in range(min(num_topics, len(common_words) // num_words)):
                word_objects = []
                batch = common_words[i * num_words:(i + 1) * num_words]
                total_count = sum(count for _, count in batch)
                
                for word, count in batch:
                    word_objects.append({
                        "text": word,
                        "weight": count / total_count
                    })
                
                topics.append({
                    "topic_id": i + 1,
                    "words": word_objects
                })
            
            return topics if topics else [{"topic_id": 1, "words": [{"text": "Unable to extract topics", "weight": 1.0}]}]
            
    except Exception as e:
        logger.error(f"Error extracting topics: {str(e)}")
        return [{"topic_id": 1, "words": [{"text": "Error extracting topics", "weight": 1.0}]}]

def get_text_stats(text):
   
    try:
        simple_words = text.split()
        word_count = len(simple_words)
        
        sentence_splitters = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
        sentences_text = text
        for splitter in sentence_splitters:
            sentences_text = sentences_text.replace(splitter, '[SPLIT]')
        
        sentences = [s for s in sentences_text.split('[SPLIT]') if s.strip()]
        sentence_count = len(sentences)
        if sentence_count == 0:
            sentence_count = 1
        avg_words_per_sentence = word_count / sentence_count
        unique_words = set(w.lower() for w in simple_words if w.isalnum())
        unique_word_count = len(unique_words)
        word_lengths = [len(word) for word in simple_words if word.strip().isalnum()]
        avg_word_length = sum(word_lengths) / len(word_lengths) if word_lengths else 0
        
        try:
            nltk_words = word_tokenize(text)
            nltk_sentences = sent_tokenize(text)
            
            word_count = len(nltk_words)
            sentence_count = len(nltk_sentences) if nltk_sentences else 1
        
            avg_words_per_sentence = word_count / sentence_count
        
            unique_words = set(w.lower() for w in nltk_words if w.isalnum())
            unique_word_count = len(unique_words)
            word_lengths = [len(word) for word in nltk_words if word.isalnum()]
            avg_word_length = sum(word_lengths) / len(word_lengths) if word_lengths else 0
        except Exception as e:
            logger.warning(f"Using simplified text stats calculation: {str(e)}")
        
        return {
            "word_count": word_count,
            "unique_word_count": unique_word_count,
            "sentence_count": sentence_count,
            "avg_words_per_sentence": round(avg_words_per_sentence, 2),
            "avg_word_length": round(avg_word_length, 2)
        }
        
    except Exception as e:
        logger.error(f"Error calculating text statistics: {str(e)}")
        return {
            "word_count": 0,
            "unique_word_count": 0,
            "sentence_count": 0,
            "avg_words_per_sentence": 0,
            "avg_word_length": 0
        }
