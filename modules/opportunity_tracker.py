import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import logging

# Import free alternative clients
from utils.api_clients import SerpAnalysisClient, TrendsAnalysisClient, KeywordDataClient

class OpportunityTracker:
    def __init__(self, domain, storage_dir="data"):
        """
        Initialize the opportunity tracker
        
        Args:
            domain (str): Your domain
            storage_dir (str): Directory to store tracked opportunities
        """
        self.domain = domain
        self.storage_dir = storage_dir
        
        # Initialize API clients with free alternatives
        self.serp_client = SerpAnalysisClient()
        self.trends_client = TrendsAnalysisClient()
        self.keyword_client = KeywordDataClient()
        
        self.logger = logging.getLogger(__name__)
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
            
    def track_keyword_rankings(self, keywords, update=True):
        """
        Track your domain's rankings for specified keywords
        
        Args:
            keywords (list): List of keywords to track
            update (bool): Whether to update existing data
            
        Returns:
            pandas.DataFrame: DataFrame containing ranking data
        """
        self.logger.info(f"Tracking rankings for {len(keywords)} keywords...")
        
        today = datetime.now().strftime("%Y-%m-%d")
        rankings = []
        
        # Limit to 30 keywords for free tier usage
        for keyword in keywords[:min(len(keywords), 30)]:
            try:
                # Get SERP results
                serp_results = self.serp_client.get_serp(keyword, num_results=50)
                
                # Check if the domain is ranking
                ranking = 0
                for i, result in enumerate(serp_results):
                    if 'url' in result and self.domain in result['url']:
                        ranking = i + 1
                        break
                
                rankings.append({
                    'keyword': keyword,
                    'ranking': ranking,
                    'date': today,
                    'in_top_100': ranking > 0
                })
            except Exception as e:
                self.logger.error(f"Error tracking ranking for {keyword}: {e}")
                # Add a placeholder entry
                rankings.append({
                    'keyword': keyword,
                    'ranking': 0,
                    'date': today,
                    'in_top_100': False,
                    'error': str(e)
                })
        
        # Create DataFrame
        rankings_df = pd.DataFrame(rankings)
        
        # Save to CSV if requested
        if update:
            rankings_file = os.path.join(self.storage_dir, "keyword_rankings.csv")
            
            if os.path.exists(rankings_file):
                # Append to existing data
                try:
                    existing_df = pd.read_csv(rankings_file)
                    combined_df = pd.concat([existing_df, rankings_df]).drop_duplicates(
                        subset=['keyword', 'date']
                    ).reset_index(drop=True)
                    combined_df.to_csv(rankings_file, index=False)
                    return combined_df
                except Exception as e:
                    self.logger.error(f"Error updating rankings file: {e}")
                    # If there's an error, just save the new data
                    rankings_df.to_csv(rankings_file, index=False)
            else:
                # Create new file
                rankings_df.to_csv(rankings_file, index=False)
                
        return rankings_df
            
    def identify_trending_topics(self, seed_keywords=None):
        """
        Identify trending topics related to your domain
        
        Uses Google Trends API (free) to find trending topics
        
        Args:
            seed_keywords (list): List of seed keywords related to your industry
            
        Returns:
            list: Trending topics with scores
        """
        self.logger.info("Identifying trending topics...")
        
        if not seed_keywords:
            seed_keywords = ['recruitment', 'talent acquisition', 'hiring', 'AI recruiter']
            
        trending_topics = []
        
        # Limit to 5 seed keywords for free tier usage
        for keyword in seed_keywords[:min(len(seed_keywords), 5)]:
            try:
                # Get trending queries from Google Trends (free)
                trending_queries = self.trends_client.get_related_queries(keyword)
                
                # Add to trending topics if rising queries exist
                if 'rising' in trending_queries:
                    for query in trending_queries['rising']:
                        trending_topics.append({
                            'topic': query['query'],
                            'trend_score': query['value'],
                            'seed_keyword': keyword,
                            'timeframe': 'now 7-d'
                        })
                        
            except Exception as e:
                self.logger.error(f"Error getting trending topics for {keyword}: {e}")
                
        # Sort by trend score and remove duplicates
        trending_topics.sort(key=lambda x: x['trend_score'], reverse=True)
        
        # Remove duplicates (keeping highest score)
        unique_topics = {}
        for topic in trending_topics:
            if topic['topic'] not in unique_topics or topic['trend_score'] > unique_topics[topic['topic']]['trend_score']:
                unique_topics[topic['topic']] = topic
                
        return list(unique_topics.values())
        
    def check_serp_volatility(self, keywords, days=7):
        """
        Check SERP volatility for keywords over time
        
        Args:
            keywords (list): List of keywords to check
            days (int): Number of days to check for changes
            
        Returns:
            dict: Keywords with volatility scores
        """
        self.logger.info(f"Checking SERP volatility for {len(keywords)} keywords over {days} days...")
        
        # Load historical ranking data
        rankings_file = os.path.join(self.storage_dir, "keyword_rankings.csv")
        
        if not os.path.exists(rankings_file):
            self.logger.warning("No historical ranking data available")
            return {}
            
        try:
            rankings_df = pd.read_csv(rankings_file)
        except Exception as e:
            self.logger.error(f"Error reading rankings file: {e}")
            return {}
        
        # Filter to just the keywords we're interested in
        rankings_df = rankings_df[rankings_df['keyword'].isin(keywords)]
        
        # Convert date to datetime
        rankings_df['date'] = pd.to_datetime(rankings_df['date'])
        
        # Filter to last N days
        cutoff_date = datetime.now() - timedelta(days=days)
        rankings_df = rankings_df[rankings_df['date'] >= cutoff_date]
        
        volatility = {}
        
        for keyword in keywords:
            keyword_data = rankings_df[rankings_df['keyword'] == keyword]
            
            if len(keyword_data) <= 1:
                # Not enough data for this keyword
                continue
                
            # Calculate standard deviation of rankings
            std_dev = keyword_data['ranking'].std()
            
            # Calculate mean change between consecutive days
            keyword_data = keyword_data.sort_values('date')
            ranking_changes = keyword_data['ranking'].diff().abs().dropna().mean()
            
            # Combined volatility score (normalized to 0-100)
            volatility_score = min(100, (std_dev + ranking_changes) * 5)
            
            volatility[keyword] = {
                'volatility_score': volatility_score,
                'std_dev': std_dev,
                'mean_daily_change': ranking_changes,
                'data_points': len(keyword_data)
            }
            
        return volatility
        
    def identify_weekly_opportunities(self, top_n=10):
        """
        Identify weekly content opportunities
        
        Args:
            top_n (int): Number of top opportunities to return
            
        Returns:
            list: Top content opportunities for the week
        """
        self.logger.info(f"Identifying weekly content opportunities (top {top_n})...")
        
        # Get trending topics
        trending_topics = self.identify_trending_topics()
        
        # Extract keywords from trending topics
        trending_keywords = [topic['topic'] for topic in trending_topics]
        
        # Check SERP features and competition for these keywords
        opportunities = []
        
        # Limit to 20 keywords for free tier
        for keyword in trending_keywords[:min(len(trending_keywords), 20)]:
            try:
                # Get SERP results (using free alternatives)
                serp_results = self.serp_client.get_serp(keyword)
                
                # Check if you're already ranking
                already_ranking = False
                for result in serp_results:
                    if 'url' in result and self.domain in result['url']:
                        already_ranking = True
                        break
                        
                # Check SERP features
                features = {
                    'featured_snippet': False,
                    'people_also_ask': False
                }
                
                for result in serp_results:
                    if result.get('type') == 'featured_snippet':
                        features['featured_snippet'] = True
                    elif result.get('type') == 'people_also_ask':
                        features['people_also_ask'] = True
                        
                # Calculate opportunity score
                score = 50  # Base score
                
                # Adjust for SERP features
                if features['featured_snippet']:
                    score += 20  # Featured snippets are good opportunities
                if features['people_also_ask']:
                    score += 10  # People also ask questions are valuable
                    
                # Adjust for current ranking
                if already_ranking:
                    score -= 30  # Less opportunity if already ranking
                    
                # Adjust for trend score (if available)
                trend_data = next((t for t in trending_topics if t['topic'] == keyword), None)
                if trend_data:
                    trend_bonus = min(30, trend_data['trend_score'] / 10)
                    score += trend_bonus
                    
                # Normalize score
                score = max(0, min(100, score))
                
                opportunities.append({
                    'keyword': keyword,
                    'opportunity_score': score,
                    'features': features,
                    'already_ranking': already_ranking,
                    'trend_data': trend_data
                })
                
            except Exception as e:
                self.logger.error(f"Error analyzing opportunity for {keyword}: {e}")
                
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        return opportunities[:top_n]
        
    def generate_weekly_report(self, top_keywords=None):
        """
        Generate a weekly content opportunity report
        
        Args:
            top_keywords (list): List of top keywords to track (if None, uses trending topics)
            
        Returns:
            dict: Weekly content opportunity report
        """
        self.logger.info("Generating weekly content opportunity report...")
        
        # Get trending topics
        trending_topics = self.identify_trending_topics()
        
        # Get top opportunities
        opportunities = self.identify_weekly_opportunities()
        
        # Track rankings if top_keywords provided
        rankings = None
        if top_keywords:
            rankings = self.track_keyword_rankings(top_keywords)
            
        # Generate report
        report = {
            'date': datetime.now().strftime("%Y-%m-%d"),
            'trending_topics': trending_topics[:10],  # Limit to top 10 trending topics
            'content_opportunities': opportunities,
            'rankings': rankings.to_dict('records') if rankings is not None else None
        }
        
        # Save report
        report_file = os.path.join(
            self.storage_dir, 
            f"opportunity_report_{datetime.now().strftime('%Y%m%d')}.json"
        )
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving opportunity report: {e}")
            
        return report