import unittest
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.keyword_clustering import KeywordClusterer

class TestKeywordClusterer(unittest.TestCase):
    """Test cases for KeywordClusterer module"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.domain = "asendia.ai"
        self.clusterer = KeywordClusterer(self.domain)
        
    def test_init(self):
        """Test initialization"""
        self.assertEqual(self.clusterer.domain, self.domain)
        self.assertIsNone(self.clusterer.user_profiles)
        
    def test_fetch_keywords(self):
        """Test keyword fetching"""
        # Test with seed keywords
        seed_keywords = ["recruitment", "hiring", "talent acquisition"]
        df = self.clusterer.fetch_keywords(seed_keywords)
        
        # Check if result is a DataFrame
        self.assertIsInstance(df, pd.DataFrame)
        
        # Check if it contains the expected columns
        self.assertIn("keyword", df.columns)
        self.assertIn("volume", df.columns)
        self.assertIn("cpc", df.columns)
        self.assertIn("competition", df.columns)
        
        # Check if seed keywords are included
        for keyword in seed_keywords:
            self.assertIn(keyword, df["keyword"].values)
            
    def test_cluster_keywords(self):
        """Test keyword clustering"""
        # Generate some test data
        test_data = {
            "keyword": ["recruitment software", "hiring software", "applicant tracking", 
                        "recruitment CRM", "talent acquisition platform", "hiring process"],
            "volume": [1000, 800, 600, 500, 400, 300],
            "cpc": [2.5, 2.0, 1.8, 1.5, 1.2, 1.0],
            "competition": [0.8, 0.7, 0.6, 0.5, 0.4, 0.3]
        }
        test_df = pd.DataFrame(test_data)
        
        # Test KMeans clustering
        result_kmeans = self.clusterer.cluster_keywords(test_df, n_clusters=2, method="kmeans")
        
        # Check if clustering added required columns
        self.assertIn("cluster", result_kmeans.columns)
        self.assertIn("intent", result_kmeans.columns)
        self.assertIn("user_profile", result_kmeans.columns)
        self.assertIn("cluster_label", result_kmeans.columns)
        
        # Check if we have the expected number of clusters
        self.assertLessEqual(result_kmeans["cluster"].nunique(), 2)
        
        # Test DBSCAN clustering
        result_dbscan = self.clusterer.cluster_keywords(test_df, method="dbscan")
        self.assertIn("cluster", result_dbscan.columns)
        
        # Test Graph clustering
        result_graph = self.clusterer.cluster_keywords(test_df, method="graph")
        self.assertIn("cluster", result_graph.columns)

    def test_get_top_keywords_by_cluster(self):
        """Test getting top keywords by cluster"""
        # Generate test data with clusters
        test_data = {
            "keyword": ["recruitment software", "hiring software", "applicant tracking", 
                       "recruitment CRM", "talent acquisition platform", "hiring process"],
            "volume": [1000, 800, 600, 500, 400, 300],
            "cluster": [0, 0, 1, 1, 0, 1],
            "cluster_label": ["Cluster 0", "Cluster 0", "Cluster 1", "Cluster 1", "Cluster 0", "Cluster 1"]
        }
        test_df = pd.DataFrame(test_data)
        
        # Get top keywords by volume
        top_keywords = self.clusterer.get_top_keywords_by_cluster(test_df, metric="volume", top_n=2)
        
        # Check if we got the expected result
        self.assertEqual(len(top_keywords), 2)  # Two clusters
        self.assertEqual(len(top_keywords["Cluster 0"]), 2)  # Two keywords per cluster
        self.assertEqual(len(top_keywords["Cluster 1"]), 2)
        
        # Check if the order is correct (by volume)
        self.assertEqual(top_keywords["Cluster 0"][0], "recruitment software")
        self.assertEqual(top_keywords["Cluster 0"][1], "hiring software")
        self.assertEqual(top_keywords["Cluster 1"][0], "applicant tracking")
        self.assertEqual(top_keywords["Cluster 1"][1], "recruitment CRM")


if __name__ == "__main__":
    unittest.main()