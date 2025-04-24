import re
import string
import logging
from bs4 import BeautifulSoup
from collections import Counter

# Configure logging
logger = logging.getLogger(__name__)

def preprocess_text(text):
    """
    Preprocess text for NLP analysis
    
    Args:
        text (str): Input text
        
    Returns:
        str: Preprocessed text
    """
    if not text:
        return ""
        
    try:
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove HTML tags
        text = re.sub(r'<.*?>', '', text)
        
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    except Exception as e:
        logger.error(f"Error preprocessing text: {e}")
        return text

def extract_text_from_html(html_content):
    """
    Extract main content text from HTML
    
    Args:
        html_content (str or BeautifulSoup): HTML content or BeautifulSoup object
        
    Returns:
        str: Extracted text
    """
    try:
        if not isinstance(html_content, BeautifulSoup):
            soup = BeautifulSoup(html_content, 'html.parser')
        else:
            soup = html_content
            
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
            
        # Extract text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
        
    except Exception as e:
        logger.error(f"Error extracting text from HTML: {e}")
        return ""

def extract_important_phrases(text, top_n=10):
    """
    Extract important phrases from text
    
    Args:
        text (str): Input text
        top_n (int): Number of top phrases to extract
        
    Returns:
        list: Top important phrases
    """
    try:
        # Simple n-gram approach for phrase extraction
        words = preprocess_text(text).split()
        
        # Create bigrams and trigrams
        bigrams = [' '.join(words[i:i+2]) for i in range(len(words)-1)]
        trigrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
        
        # Count phrases
        phrase_counter = Counter(bigrams + trigrams)
        
        # Filter out rare phrases (appearing only once)
        filtered_phrases = {phrase: count for phrase, count in phrase_counter.items() 
                          if count > 1 and len(phrase.split()) > 1}
        
        # Return top phrases
        return [phrase for phrase, _ in 
                sorted(filtered_phrases.items(), key=lambda x: x[1], reverse=True)[:top_n]]
        
    except Exception as e:
        logger.error(f"Error extracting important phrases: {e}")
        return []

def extract_keywords_from_text(text, stopwords=None, top_n=20):
    """
    Extract keywords from text
    
    Args:
        text (str): Input text
        stopwords (set): Set of stopwords to exclude
        top_n (int): Number of top keywords to extract
        
    Returns:
        list: Top keywords with scores
    """
    try:
        if stopwords is None:
            # Basic stopwords for English
            stopwords = {
                'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
                'do', 'does', 'did', 'to', 'at', 'by', 'for', 'with', 'about', 'against',
                'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
                'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
                'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
                'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
                'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
                's', 't', 'can', 'will', 'just', 'should', 'now'
            }
            
        # Preprocess text
        processed_text = preprocess_text(text)
        
        # Tokenize
        words = processed_text.split()
        
        # Filter out stopwords and short words
        filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
        
        # Count words
        word_counts = Counter(filtered_words)
        
        # Get top keywords
        return word_counts.most_common(top_n)
        
    except Exception as e:
        logger.error(f"Error extracting keywords from text: {e}")
        return []

def calculate_text_similarity(text1, text2, method='jaccard'):
    """
    Calculate similarity between two texts
    
    Args:
        text1 (str): First text
        text2 (str): Second text
        method (str): Similarity method ('jaccard' or 'cosine')
        
    Returns:
        float: Similarity score
    """
    try:
        # Preprocess texts
        text1_processed = preprocess_text(text1)
        text2_processed = preprocess_text(text2)
        
        if method == 'jaccard':
            # Tokenize texts
            set1 = set(text1_processed.split())
            set2 = set(text2_processed.split())
            
            # Calculate Jaccard similarity
            intersection = set1.intersection(set2)
            union = set1.union(set2)
            
            similarity = len(intersection) / len(union) if union else 0
            
        elif method == 'cosine':
            # Import here to avoid dependency for simple methods
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.metrics.pairwise import cosine_similarity
                
                # Vectorize texts
                vectorizer = TfidfVectorizer()
                vectors = vectorizer.fit_transform([text1_processed, text2_processed])
                
                # Calculate cosine similarity
                similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            except ImportError:
                logger.warning("scikit-learn not available, falling back to Jaccard similarity")
                return calculate_text_similarity(text1, text2, method='jaccard')
                
        else:
            raise ValueError(f"Unknown similarity method: {method}")
            
        return similarity
        
    except Exception as e:
        logger.error(f"Error calculating text similarity: {e}")
        return 0.0

def identify_keyword_patterns(keywords):
    """
    Identify patterns in a list of keywords
    
    Args:
        keywords (list): List of keywords to analyze
        
    Returns:
        dict: Patterns identified in keywords
    """
    try:
        patterns = {
            'question_keywords': [],
            'comparison_keywords': [],
            'list_keywords': [],
            'how_to_keywords': [],
            'best_keywords': []
        }
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Identify question keywords
            if any(q in keyword_lower for q in ['what', 'how', 'why', 'when', 'where', 'who', 'which']):
                patterns['question_keywords'].append(keyword)
                
            # Identify comparison keywords
            if any(c in keyword_lower for c in [' vs ', ' versus ', ' compared to ', ' compared with ', ' or ']):
                patterns['comparison_keywords'].append(keyword)
                
            # Identify list keywords
            if any(l in keyword_lower for q in ['top', 'list', 'best', 'ways to', 'tips', 'ideas']):
                patterns['list_keywords'].append(keyword)
                
            # Identify how-to keywords
            if 'how to' in keyword_lower:
                patterns['how_to_keywords'].append(keyword)
                
            # Identify best keywords
            if 'best' in keyword_lower:
                patterns['best_keywords'].append(keyword)
                
        return patterns
        
    except Exception as e:
        logger.error(f"Error identifying keyword patterns: {e}")
        return {}

def cluster_by_similarity(items, threshold=0.5, max_clusters=10):
    """
    Cluster items by similarity
    
    Args:
        items (list): List of items to cluster
        threshold (float): Similarity threshold (0-1)
        max_clusters (int): Maximum number of clusters
        
    Returns:
        list: List of clusters (lists of items)
    """
    try:
        # Initialize clusters
        clusters = []
        
        # Process each item
        for item in items:
            # Check if item fits in any existing cluster
            found_cluster = False
            
            for cluster in clusters:
                # Calculate similarity with cluster center
                cluster_center = cluster[0]  # Use first item as center
                similarity = calculate_text_similarity(item, cluster_center)
                
                if similarity >= threshold:
                    cluster.append(item)
                    found_cluster = True
                    break
                    
            # If no suitable cluster found and we haven't reached max clusters
            if not found_cluster and len(clusters) < max_clusters:
                clusters.append([item])
                
            # If no suitable cluster and we've reached max clusters, add to most similar
            elif not found_cluster:
                best_similarity = -1
                best_cluster = None
                
                for i, cluster in enumerate(clusters):
                    cluster_center = cluster[0]
                    similarity = calculate_text_similarity(item, cluster_center)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_cluster = i
                        
                clusters[best_cluster].append(item)
                
        return clusters
        
    except Exception as e:
        logger.error(f"Error clustering by similarity: {e}")
        return []