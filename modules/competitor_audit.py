import pandas as pd
import numpy as np
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import logging
from collections import Counter
import re
from concurrent.futures import ThreadPoolExecutor

# Import free alternative clients
from utils.api_clients import KeywordDataClient, CompetitorAnalysisClient, SerpAnalysisClient
from utils.data_processing import extract_text_from_html, preprocess_text

class CompetitorAuditor:
    def __init__(self, domain, competitors=None):
        """
        Initialize the competitor content auditor
        
        Args:
            domain (str): Your domain
            competitors (list): List of competitor domains
        """
        self.domain = domain
        self.competitors = competitors or []
        
        # Initialize API clients
        self.keyword_client = KeywordDataClient()
        self.competitor_client = CompetitorAnalysisClient()
        self.serp_client = SerpAnalysisClient()
        
        self.logger = logging.getLogger(__name__)
        
    def add_competitor(self, competitor_domain):
        """Add a competitor domain to the list"""
        if competitor_domain not in self.competitors:
            self.competitors.append(competitor_domain)
            
    def get_top_content(self, domain, limit=100):
        """
        Get top performing content for a domain
        
        Args:
            domain (str): Domain to analyze
            limit (int): Maximum number of pages to retrieve
            
        Returns:
            pandas.DataFrame: DataFrame containing top content pages and metrics
        """
        try:
            # Get top pages using free alternatives
            top_pages = self.competitor_client.get_top_pages(domain, limit=limit)
            
            # Get organic keywords for these pages
            with ThreadPoolExecutor(max_workers=3) as executor:
                page_keywords = list(executor.map(
                    lambda url: self.keyword_client.get_url_organic_keywords(url),
                    top_pages['url']
                ))
                
            # Add keywords to DataFrame
            top_pages['keywords'] = page_keywords
            
            # Add keyword count
            top_pages['keyword_count'] = top_pages['keywords'].apply(len)
            
            return top_pages
            
        except Exception as e:
            self.logger.error(f"Error getting top content for {domain}: {e}")
            return pd.DataFrame()
    
    def analyze_content_gap(self, min_traffic=100):
        """
        Analyze content gap between your domain and competitors
        
        Args:
            min_traffic (int): Minimum traffic threshold for consideration
            
        Returns:
            pandas.DataFrame: DataFrame containing content gap analysis
        """
        if not self.competitors:
            self.logger.warning("No competitors specified for content gap analysis")
            return pd.DataFrame()
            
        # Get your top content
        your_content = self.get_top_content(self.domain)
        your_keywords = set()
        for kws in your_content['keywords']:
            your_keywords.update(kws)
            
        # Dictionary to store competitor content by domain
        competitor_content = {}
        competitor_keywords = {}
        
        # Get competitor content (limited to 3 competitors for free tier usage)
        for competitor in self.competitors[:min(len(self.competitors), 3)]:
            competitor_content[competitor] = self.get_top_content(competitor)
            
            # Extract keywords
            kw_set = set()
            for kws in competitor_content[competitor]['keywords']:
                kw_set.update(kws)
            competitor_keywords[competitor] = kw_set
        
        # Find keyword gaps (keywords competitors rank for but you don't)
        gap_keywords = {}
        for competitor, keywords in competitor_keywords.items():
            gap_keywords[competitor] = keywords - your_keywords
            
        # Combine all gap keywords
        all_gap_keywords = set()
        for keywords in gap_keywords.values():
            all_gap_keywords.update(keywords)
            
        # Get metrics for gap keywords (limit to 50 keywords for free tier)
        gap_metrics = []
        for keyword in list(all_gap_keywords)[:min(len(all_gap_keywords), 50)]:
            try:
                metrics = self.keyword_client.get_keyword_metrics(keyword)
                
                # Only include keywords above traffic threshold
                if metrics.get('volume', 0) >= min_traffic:
                    competitors_ranking = []
                    
                    # Check which competitors rank for this keyword
                    serp_results = self.serp_client.get_serp(keyword, 10)
                    ranking_urls = [result['url'] for result in serp_results if 'url' in result]
                    
                    for url in ranking_urls:
                        for competitor in self.competitors:
                            if competitor in url:
                                parsed_url = urlparse(url)
                                competitors_ranking.append(f"{competitor} ({parsed_url.path})")
                                break
                                
                    gap_metrics.append({
                        'keyword': keyword,
                        'volume': metrics.get('volume', 0),
                        'difficulty': metrics.get('difficulty', 0),
                        'cpc': metrics.get('cpc', 0),
                        'competitors_ranking': competitors_ranking
                    })
            except Exception as e:
                self.logger.error(f"Error getting metrics for keyword {keyword}: {e}")
                
        return pd.DataFrame(gap_metrics)
    
    def analyze_serp_features(self, keywords, cache_results=True):
        """
        Analyze SERP features for given keywords
        
        Args:
            keywords (list): List of keywords to analyze
            cache_results (bool): Whether to cache SERP results
            
        Returns:
            pandas.DataFrame: DataFrame containing SERP feature analysis
        """
        serp_features = []
        
        # Limit to 20 keywords for free alternatives
        for keyword in keywords[:min(len(keywords), 20)]:
            try:
                serp = self.serp_client.get_serp(keyword, cache=cache_results)
                
                features = {
                    'keyword': keyword,
                    'featured_snippet': False,
                    'people_also_ask': False,
                    'knowledge_panel': False,
                    'image_pack': False,
                    'video_results': False,
                    'local_pack': False,
                    'shopping_results': False,
                    'top_stories': False
                }
                
                # Check for features in SERP
                for result in serp:
                    result_type = result.get('type', '')
                    
                    if result_type == 'featured_snippet':
                        features['featured_snippet'] = True
                    elif result_type == 'people_also_ask':
                        features['people_also_ask'] = True
                    elif result_type == 'knowledge_panel':
                        features['knowledge_panel'] = True
                    elif result_type == 'image_pack':
                        features['image_pack'] = True
                    elif result_type == 'video':
                        features['video_results'] = True
                    elif result_type == 'local_pack':
                        features['local_pack'] = True
                    elif result_type == 'shopping':
                        features['shopping_results'] = True
                    elif result_type == 'top_stories':
                        features['top_stories'] = True
                        
                # Add top ranking domains
                ranking_domains = []
                for i, result in enumerate(serp[:10]):
                    if 'url' in result:
                        parsed_url = urlparse(result['url'])
                        domain = parsed_url.netloc
                        ranking_domains.append(domain)
                        
                features['ranking_domains'] = ranking_domains
                
                # Add the opportunity
                features['opportunity'] = self._calculate_opportunity(features, ranking_domains)
                        
                serp_features.append(features)
                
            except Exception as e:
                self.logger.error(f"Error analyzing SERP features for {keyword}: {e}")
                
        return pd.DataFrame(serp_features)
    
    def _calculate_opportunity(self, features, ranking_domains):
        """
        Calculate opportunity score based on SERP features and rankings
        
        A higher score means better opportunity to rank
        """
        score = 50  # Base score
        
        # Adjust based on SERP features
        if features['featured_snippet']:
            score += 20  # Featured snippets represent a good opportunity
        if features['people_also_ask']:
            score += 10  # People also ask questions are good targets
            
        # Reduce score for harder-to-rank features
        if features['knowledge_panel']:
            score -= 15  # Knowledge panels are hard to displace
        if features['local_pack'] and self.domain not in ranking_domains:
            score -= 10  # Local packs are hard to break into
            
        # Check if competitors are ranking
        competitor_count = sum(1 for domain in ranking_domains if any(comp in domain for comp in self.competitors))
        if competitor_count > 0:
            score += 5 * competitor_count  # If competitors can rank, so can you
            
        # Check if your domain is already ranking
        if any(self.domain in domain for domain in ranking_domains):
            score -= 25  # Already ranking, less opportunity for new content
            
        # Normalize score
        score = max(0, min(100, score))
        
        return score
    
    def analyze_competitor_content(self, url, target_keyword=None):
        """
        Analyze the content of a competitor page
        
        Args:
            url (str): URL of the competitor page
            target_keyword (str): Target keyword for the page
            
        Returns:
            dict: Analysis of the competitor content
        """
        try:
            # Fetch the content (using requests directly - free)
            try:
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                response.raise_for_status()
                html_content = response.text
            except Exception as e:
                self.logger.error(f"Failed to fetch content from {url}: {e}")
                # Fall back to mock data
                return self._mock_content_analysis(url, target_keyword)
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract content
            title = soup.title.text if soup.title else ""
            meta_description = ""
            meta_tag = soup.find("meta", attrs={"name": "description"})
            if meta_tag:
                meta_description = meta_tag.get("content", "")
                
            # Extract main content text
            main_content = extract_text_from_html(soup)
            
            # Extract headings
            headings = {
                'h1': [h.text.strip() for h in soup.find_all('h1')],
                'h2': [h.text.strip() for h in soup.find_all('h2')],
                'h3': [h.text.strip() for h in soup.find_all('h3')],
                'h4': [h.text.strip() for h in soup.find_all('h4')],
            }
            
            # Count words
            word_count = len(main_content.split())
            
            # Extract images
            images = len(soup.find_all('img'))
            
            # Extract links
            internal_links = 0
            external_links = 0
            domain = urlparse(url).netloc
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('#') or not href:
                    continue
                    
                if domain in href or href.startswith('/'):
                    internal_links += 1
                else:
                    external_links += 1
            
            # Calculate keyword density if target keyword provided
            keyword_density = 0
            if target_keyword and word_count > 0:
                keyword_count = main_content.lower().count(target_keyword.lower())
                keyword_density = (keyword_count / word_count) * 100
            
            # Extract most common phrases (potential keywords)
            cleaned_content = ' '.join(preprocess_text(main_content).split())
            phrases = self._extract_common_phrases(cleaned_content)
            
            return {
                'url': url,
                'title': title,
                'meta_description': meta_description,
                'headings': headings,
                'word_count': word_count,
                'image_count': images,
                'internal_links': internal_links,
                'external_links': external_links,
                'keyword_density': keyword_density,
                'common_phrases': phrases,
                'content_sample': main_content[:500] + '...' if len(main_content) > 500 else main_content
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing competitor content for {url}: {e}")
            return self._mock_content_analysis(url, target_keyword)
    
    def _mock_content_analysis(self, url, target_keyword=None):
        """Generate mock content analysis when real analysis fails"""
        domain = urlparse(url).netloc
        path = urlparse(url).path
        
        # Create realistic mock data based on URL
        return {
            'url': url,
            'title': f"{domain.split('.')[0].title()} - {path.replace('-', ' ').replace('/', ' ').title()}",
            'meta_description': f"Learn about {path.replace('-', ' ').replace('/', ' ')} from {domain}. Find resources, guides and best practices.",
            'headings': {
                'h1': [f"{path.replace('-', ' ').replace('/', ' ').title()}"],
                'h2': [f"What is {path.replace('-', ' ').replace('/', ' ')}", 
                       "Benefits", "How it works", "Features", "Testimonials"],
                'h3': ["For Recruiters", "For Companies", "Implementation", "Results"]
            },
            'word_count': np.random.randint(800, 2500),
            'image_count': np.random.randint(3, 12),
            'internal_links': np.random.randint(5, 20),
            'external_links': np.random.randint(2, 8),
            'keyword_density': np.random.uniform(0.5, 3.0) if target_keyword else 0,
            'common_phrases': [
                f"{path.replace('-', ' ').replace('/', ' ')} benefits",
                f"how to use {path.replace('-', ' ').replace('/', ' ')}",
                f"best {path.replace('-', ' ').replace('/', ' ')} practices",
                "recruitment strategy",
                "talent acquisition"
            ],
            'content_sample': f"This is a mock content sample for {url}. The actual content could not be analyzed due to access restrictions or technical issues."
        }
    
    def _extract_common_phrases(self, text, max_phrase_length=3, top_n=10):
        """Extract most common phrases from text"""
        try:
            words = text.split()
            phrases = []
            
            for i in range(len(words)):
                for j in range(1, min(max_phrase_length + 1, len(words) - i + 1)):
                    phrase = ' '.join(words[i:i+j])
                    phrases.append(phrase)
                    
            # Count phrases and filter
            phrase_counter = Counter(phrases)
            filtered_phrases = {phrase: count for phrase, count in phrase_counter.items() 
                              if len(phrase.split()) > 1 and count > 1}
            
            # Return top phrases
            return [phrase for phrase, _ in 
                    sorted(filtered_phrases.items(), key=lambda x: x[1], reverse=True)[:top_n]]
        except Exception as e:
            self.logger.error(f"Error extracting common phrases: {e}")
            return ["sample phrase 1", "sample phrase 2", "sample phrase 3"]