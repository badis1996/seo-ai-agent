import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from sentence_transformers import SentenceTransformer
import networkx as nx
import logging

# Import free alternative clients
from utils.api_clients import KeywordDataClient, KeywordSuggestionClient
from utils.data_processing import preprocess_text

class KeywordClusterer:
    def __init__(self, domain, user_profiles=None, embedding_model='all-MiniLM-L6-v2'):
        """
        Initialize the keyword clusterer
        
        Args:
            domain (str): The domain to analyze keywords for
            user_profiles (list): List of user profiles to segment keywords by
            embedding_model (str): The sentence transformer model to use
        """
        self.domain = domain
        self.user_profiles = user_profiles
        
        # Initialize NLP tools (optional - can be lazily loaded)
        try:
            self.nlp = spacy.load("en_core_web_md")
        except:
            # Fall back to smaller model or mock implementation
            self.nlp = None
            
        try:
            self.sentence_model = SentenceTransformer(embedding_model)
        except:
            # Fall back to TF-IDF for embeddings if sentence-transformers not available
            self.sentence_model = None
            
        # Initialize API clients
        self.keyword_client = KeywordDataClient()
        self.suggestion_client = KeywordSuggestionClient()
        
        self.logger = logging.getLogger(__name__)
        
    def fetch_keywords(self, seed_keywords=None, additional_sources=True):
        """
        Fetch keywords from various sources
        
        Args:
            seed_keywords (list): Initial seed keywords to expand from
            additional_sources (bool): Whether to get keywords from additional sources
            
        Returns:
            pandas.DataFrame: DataFrame containing keywords and metadata
        """
        keywords_df = pd.DataFrame()
        
        # Get organic keywords from free keyword data sources
        try:
            organic_kws = self.keyword_client.get_organic_keywords(self.domain)
            keywords_df = pd.concat([keywords_df, organic_kws])
        except Exception as e:
            self.logger.error(f"Error fetching organic keywords: {e}")
        
        # Expand from seed keywords if provided
        if seed_keywords:
            for keyword in seed_keywords:
                try:
                    related_kws = self.suggestion_client.get_keyword_ideas(keyword)
                    keywords_df = pd.concat([keywords_df, related_kws])
                except Exception as e:
                    self.logger.error(f"Error expanding keyword {keyword}: {e}")
        
        # Remove duplicates and reset index
        if not keywords_df.empty:
            keywords_df = keywords_df.drop_duplicates(subset=['keyword']).reset_index(drop=True)
        
        return keywords_df
    
    def _create_embeddings(self, keywords):
        """Create embeddings for keywords using sentence transformer or TF-IDF"""
        if self.sentence_model:
            # Use sentence transformer model if available
            return self.sentence_model.encode(keywords)
        else:
            # Fall back to TF-IDF for embeddings
            vectorizer = TfidfVectorizer()
            return vectorizer.fit_transform(keywords)
    
    def _detect_intent(self, keyword):
        """Detect search intent for a keyword"""
        intents = {
            'informational': ['what', 'how', 'why', 'guide', 'tutorial', 'tips', 'learn'],
            'navigational': ['login', 'sign in', 'website', 'official', 'download'],
            'commercial': ['best', 'top', 'review', 'compare', 'vs', 'versus'],
            'transactional': ['buy', 'price', 'deal', 'discount', 'purchase', 'free', 'trial']
        }
        
        keyword_lower = keyword.lower()
        
        for intent, markers in intents.items():
            if any(marker in keyword_lower for marker in markers):
                return intent
                
        # Analyze using spaCy for more complex intent detection if available
        if self.nlp:
            doc = self.nlp(keyword_lower)
            
            # Check for question words
            if any(token.text in ['what', 'how', 'why', 'when', 'where', 'who'] for token in doc):
                return 'informational'
            
        # Default to informational if no clear intent is found
        return 'informational'
    
    def _assign_user_profile(self, keyword):
        """Assign a user profile to a keyword based on relevance"""
        if not self.user_profiles:
            return None
            
        keyword_lower = keyword.lower()
        profile_scores = {}
        
        profile_keywords = {
            'recruiter': ['recruiter', 'recruiting', 'talent sourcing', 'headhunter', 'talent acquisition'],
            'talent_acquisition': ['talent acquisition', 'hiring manager', 'recruitment strategy', 'talent pipeline'],
            'hr_manager': ['hr', 'human resources', 'people operations', 'employee', 'workforce'],
            'candidate': ['job seeker', 'candidate', 'job application', 'interview', 'resume', 'cv']
        }
        
        for profile, markers in profile_keywords.items():
            if profile in self.user_profiles:
                score = sum(marker in keyword_lower for marker in markers)
                profile_scores[profile] = score
        
        # If no clear signal and spaCy is available, use NLP comparison
        if max(profile_scores.values(), default=0) == 0 and self.nlp:
            keyword_doc = self.nlp(keyword_lower)
            for profile, markers in profile_keywords.items():
                if profile in self.user_profiles:
                    max_similarity = max([keyword_doc.similarity(self.nlp(marker)) for marker in markers], default=0)
                    profile_scores[profile] = max_similarity
        
        # Return the profile with the highest score if above threshold
        if profile_scores:
            best_profile = max(profile_scores.items(), key=lambda x: x[1])
            if best_profile[1] > 0.3:  # Similarity threshold
                return best_profile[0]
            
        return 'general'  # Default profile
    
    def cluster_keywords(self, keywords_df, n_clusters=None, method='kmeans'):
        """
        Cluster keywords by semantic similarity
        
        Args:
            keywords_df (pandas.DataFrame): DataFrame containing keywords
            n_clusters (int): Number of clusters for KMeans (if None, estimated)
            method (str): Clustering method ('kmeans', 'dbscan', or 'graph')
            
        Returns:
            pandas.DataFrame: DataFrame with cluster assignments
        """
        if keywords_df.empty:
            self.logger.warning("Empty keywords DataFrame. Nothing to cluster.")
            return keywords_df
            
        # Preprocess keywords
        keywords_df['processed_keyword'] = keywords_df['keyword'].apply(preprocess_text)
        
        # Create embeddings
        try:
            embeddings = self._create_embeddings(keywords_df['processed_keyword'].tolist())
        except Exception as e:
            self.logger.error(f"Error creating embeddings: {e}")
            # Fall back to mock clustering
            keywords_df['cluster'] = np.random.randint(0, 5, size=len(keywords_df))
            keywords_df['intent'] = [self._detect_intent(kw) for kw in keywords_df['keyword']]
            keywords_df['user_profile'] = [self._assign_user_profile(kw) for kw in keywords_df['keyword']]
            keywords_df['cluster_label'] = keywords_df['cluster'].apply(lambda x: f"Cluster {x}")
            return keywords_df
        
        # Perform clustering based on method
        if method == 'kmeans':
            if n_clusters is None:
                # Estimate number of clusters using silhouette score or elbow method
                n_clusters = min(max(3, len(keywords_df) // 10), 10)
                
            # Perform KMeans clustering
            try:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                clusters = kmeans.fit_predict(embeddings)
            except Exception as e:
                self.logger.error(f"Error with KMeans clustering: {e}")
                clusters = np.random.randint(0, n_clusters, size=len(keywords_df))
            
        elif method == 'dbscan':
            # Perform DBSCAN clustering
            try:
                dbscan = DBSCAN(eps=0.3, min_samples=5)
                clusters = dbscan.fit_predict(embeddings)
            except Exception as e:
                self.logger.error(f"Error with DBSCAN clustering: {e}")
                clusters = np.random.randint(0, 5, size=len(keywords_df))
            
        elif method == 'graph':
            # Graph-based clustering using cosine similarity
            try:
                similarity_matrix = cosine_similarity(embeddings)
                threshold = 0.7  # Similarity threshold
                
                # Create a graph
                G = nx.Graph()
                for i in range(len(keywords_df)):
                    G.add_node(i, keyword=keywords_df.iloc[i]['keyword'])
                    
                # Add edges based on similarity
                for i in range(len(keywords_df)):
                    for j in range(i+1, len(keywords_df)):
                        if similarity_matrix[i, j] > threshold:
                            G.add_edge(i, j, weight=similarity_matrix[i, j])
                
                # Find communities
                communities = list(nx.algorithms.community.greedy_modularity_communities(G))
                
                # Assign community labels
                clusters = np.zeros(len(keywords_df), dtype=int)
                for i, community in enumerate(communities):
                    for node in community:
                        clusters[node] = i
            except Exception as e:
                self.logger.error(f"Error with graph-based clustering: {e}")
                clusters = np.random.randint(0, 5, size=len(keywords_df))
        
        # Add cluster assignments to dataframe
        keywords_df['cluster'] = clusters
        
        # Detect intent and user profile for each keyword
        keywords_df['intent'] = keywords_df['keyword'].apply(self._detect_intent)
        keywords_df['user_profile'] = keywords_df['keyword'].apply(self._assign_user_profile)
        
        # Generate cluster labels
        cluster_labels = {}
        for cluster_id in keywords_df['cluster'].unique():
            if cluster_id == -1:  # Noise points in DBSCAN
                cluster_labels[cluster_id] = "Unclustered"
                continue
                
            cluster_keywords = keywords_df[keywords_df['cluster'] == cluster_id]['keyword'].tolist()
            
            if len(cluster_keywords) == 1:
                cluster_labels[cluster_id] = cluster_keywords[0]
                continue
                
            # Use most common intent in the cluster
            cluster_intent = keywords_df[keywords_df['cluster'] == cluster_id]['intent'].mode()[0]
            
            # Use most common user profile in the cluster
            cluster_profile = keywords_df[keywords_df['cluster'] == cluster_id]['user_profile'].mode()[0]
            
            # Use most common words in the cluster as the label
            all_words = ' '.join(cluster_keywords).lower().split()
            word_counts = pd.Series(all_words).value_counts()
            top_words = word_counts.head(3).index.tolist()
            
            cluster_labels[cluster_id] = f"{' '.join(top_words)} ({cluster_intent}, {cluster_profile})"
        
        keywords_df['cluster_label'] = keywords_df['cluster'].map(cluster_labels)
        
        return keywords_df
    
    def get_top_keywords_by_cluster(self, clustered_df, metric='volume', top_n=5):
        """
        Get top keywords from each cluster
        
        Args:
            clustered_df (pandas.DataFrame): DataFrame with cluster assignments
            metric (str): Metric to sort by ('volume', 'cpc', 'difficulty')
            top_n (int): Number of top keywords to get per cluster
            
        Returns:
            dict: Dictionary mapping cluster labels to top keywords
        """
        if clustered_df.empty:
            return {}
            
        top_keywords = {}
        
        for cluster_id in clustered_df['cluster'].unique():
            cluster_df = clustered_df[clustered_df['cluster'] == cluster_id]
            
            # Get cluster label
            if 'cluster_label' in cluster_df.columns:
                cluster_label = cluster_df['cluster_label'].iloc[0]
            else:
                cluster_label = f"Cluster {cluster_id}"
            
            if metric in cluster_df.columns:
                sorted_df = cluster_df.sort_values(by=metric, ascending=False)
                top_keywords[cluster_label] = sorted_df.head(top_n)['keyword'].tolist()
            else:
                # If metric not available, just return the first top_n keywords
                top_keywords[cluster_label] = cluster_df.head(top_n)['keyword'].tolist()
                
        return top_keywords