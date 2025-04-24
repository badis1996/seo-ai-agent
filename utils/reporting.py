import pandas as pd
import json
import os
from datetime import datetime
import logging
from tabulate import tabulate

# Configure logging
logger = logging.getLogger(__name__)

def create_keyword_report(keywords_df, output_dir="reports"):
    """
    Create a report for keyword analysis
    
    Args:
        keywords_df (pandas.DataFrame): DataFrame with keyword analysis
        output_dir (str): Directory to save the report
        
    Returns:
        str: Path to the saved report
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_dir, f"keyword_report_{timestamp}.html")
        
        # Generate HTML report
        html = "<html><head><title>Keyword Analysis Report</title>"
        html += "<style>body{font-family:Arial;margin:20px;} table{border-collapse:collapse;width:100%;} "
        html += "th,td{padding:8px;text-align:left;border-bottom:1px solid #ddd;} "
        html += "th{background-color:#f2f2f2;} tr:hover{background-color:#f5f5f5;}</style>"
        html += "</head><body>"
        
        html += f"<h1>Keyword Analysis Report</h1>"
        html += f"<p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
        
        # Summary statistics
        html += "<h2>Summary</h2>"
        html += f"<p>Total keywords: {len(keywords_df)}</p>"
        
        if 'cluster' in keywords_df.columns:
            html += f"<p>Number of clusters: {keywords_df['cluster'].nunique()}</p>"
            
        if 'user_profile' in keywords_df.columns:
            html += "<h3>Keywords by User Profile</h3>"
            profile_counts = keywords_df['user_profile'].value_counts()
            html += "<table><tr><th>User Profile</th><th>Count</th></tr>"
            for profile, count in profile_counts.items():
                html += f"<tr><td>{profile}</td><td>{count}</td></tr>"
            html += "</table>"
            
        if 'intent' in keywords_df.columns:
            html += "<h3>Keywords by Intent</h3>"
            intent_counts = keywords_df['intent'].value_counts()
            html += "<table><tr><th>Intent</th><th>Count</th></tr>"
            for intent, count in intent_counts.items():
                html += f"<tr><td>{intent}</td><td>{count}</td></tr>"
            html += "</table>"
            
        # Top keywords
        html += "<h2>Top Keywords</h2>"
        
        if 'volume' in keywords_df.columns:
            top_by_volume = keywords_df.sort_values('volume', ascending=False).head(20)
            html += "<h3>Top Keywords by Search Volume</h3>"
            html += "<table><tr><th>Keyword</th><th>Volume</th>"
            if 'cluster_label' in top_by_volume.columns:
                html += "<th>Cluster</th>"
            html += "</tr>"
            
            for _, row in top_by_volume.iterrows():
                html += f"<tr><td>{row['keyword']}</td><td>{row['volume']}</td>"
                if 'cluster_label' in row:
                    html += f"<td>{row['cluster_label']}</td>"
                html += "</tr>"
            html += "</table>"
            
        # Clusters
        if 'cluster' in keywords_df.columns and 'cluster_label' in keywords_df.columns:
            html += "<h2>Keyword Clusters</h2>"
            
            clusters = keywords_df['cluster'].unique()
            for cluster in clusters:
                cluster_df = keywords_df[keywords_df['cluster'] == cluster]
                cluster_label = cluster_df['cluster_label'].iloc[0]
                
                html += f"<h3>Cluster: {cluster_label}</h3>"
                html += "<table><tr><th>Keyword</th>"
                if 'volume' in cluster_df.columns:
                    html += "<th>Volume</th>"
                if 'intent' in cluster_df.columns:
                    html += "<th>Intent</th>"
                if 'user_profile' in cluster_df.columns:
                    html += "<th>User Profile</th>"
                html += "</tr>"
                
                for _, row in cluster_df.head(10).iterrows():
                    html += f"<tr><td>{row['keyword']}</td>"
                    if 'volume' in row:
                        html += f"<td>{row['volume']}</td>"
                    if 'intent' in row:
                        html += f"<td>{row['intent']}</td>"
                    if 'user_profile' in row:
                        html += f"<td>{row['user_profile']}</td>"
                    html += "</tr>"
                html += "</table>"
                
                if len(cluster_df) > 10:
                    html += f"<p>Showing 10 of {len(cluster_df)} keywords in this cluster</p>"
        
        html += "</body></html>"
        
        # Save report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)
            
        return report_file
        
    except Exception as e:
        logger.error(f"Error creating keyword report: {e}")
        return None

def create_opportunity_report(opportunities, output_dir="reports"):
    """
    Create a report for content opportunities
    
    Args:
        opportunities (list): List of content opportunities
        output_dir (str): Directory to save the report
        
    Returns:
        str: Path to the saved report
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_dir, f"opportunity_report_{timestamp}.html")
        
        # Generate HTML report
        html = "<html><head><title>Content Opportunity Report</title>"
        html += "<style>body{font-family:Arial;margin:20px;} table{border-collapse:collapse;width:100%;} "
        html += "th,td{padding:8px;text-align:left;border-bottom:1px solid #ddd;} "
        html += "th{background-color:#f2f2f2;} tr:hover{background-color:#f5f5f5;}"
        html += ".high{background-color:#d4edda;} .medium{background-color:#fff3cd;} .low{background-color:#f8d7da;}"
        html += "</style></head><body>"
        
        html += f"<h1>Content Opportunity Report</h1>"
        html += f"<p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
        
        # Opportunities table
        html += "<h2>Content Opportunities</h2>"
        html += "<table><tr><th>Keyword</th><th>Opportunity Score</th><th>Featured Snippet</th>"
        html += "<th>People Also Ask</th><th>Already Ranking</th></tr>"
        
        for opportunity in opportunities:
            score = opportunity['opportunity_score']
            score_class = "high" if score >= 70 else "medium" if score >= 40 else "low"
            
            html += f"<tr class='{score_class}'><td>{opportunity['keyword']}</td>"
            html += f"<td>{score}</td>"
            html += f"<td>{'Yes' if opportunity['features'].get('featured_snippet', False) else 'No'}</td>"
            html += f"<td>{'Yes' if opportunity['features'].get('people_also_ask', False) else 'No'}</td>"
            html += f"<td>{'Yes' if opportunity.get('already_ranking', False) else 'No'}</td></tr>"
            
        html += "</table>"
        
        # Recommendations
        html += "<h2>Content Recommendations</h2>"
        html += "<ul>"
        
        high_opportunities = [op for op in opportunities if op['opportunity_score'] >= 70]
        if high_opportunities:
            html += "<li><strong>High Priority:</strong> Create content for these keywords:</li>"
            html += "<ul>"
            for op in high_opportunities[:3]:
                html += f"<li>{op['keyword']} (Score: {op['opportunity_score']})</li>"
            html += "</ul>"
            
        medium_opportunities = [op for op in opportunities if 40 <= op['opportunity_score'] < 70]
        if medium_opportunities:
            html += "<li><strong>Medium Priority:</strong> Consider creating content for these keywords:</li>"
            html += "<ul>"
            for op in medium_opportunities[:3]:
                html += f"<li>{op['keyword']} (Score: {op['opportunity_score']})</li>"
            html += "</ul>"
            
        html += "</ul>"
        
        html += "</body></html>"
        
        # Save report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)
            
        return report_file
        
    except Exception as e:
        logger.error(f"Error creating opportunity report: {e}")
        return None

def create_competitor_report(competitor_data, domain, output_dir="reports"):
    """
    Create a report for competitor analysis
    
    Args:
        competitor_data (dict): Dictionary with competitor analysis data
        domain (str): Your domain
        output_dir (str): Directory to save the report
        
    Returns:
        str: Path to the saved report
    """
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_dir, f"competitor_report_{timestamp}.html")
        
        # Generate HTML report
        html = "<html><head><title>Competitor Analysis Report</title>"
        html += "<style>body{font-family:Arial;margin:20px;} table{border-collapse:collapse;width:100%;} "
        html += "th,td{padding:8px;text-align:left;border-bottom:1px solid #ddd;} "
        html += "th{background-color:#f2f2f2;} tr:hover{background-color:#f5f5f5;}"
        html += "</style></head><body>"
        
        html += f"<h1>Competitor Analysis Report for {domain}</h1>"
        html += f"<p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
        
        # Gap analysis
        if 'content_gap' in competitor_data:
            gap_df = competitor_data['content_gap']
            
            html += "<h2>Content Gap Analysis</h2>"
            html += "<p>Keywords that competitors rank for but you don't:</p>"
            
            html += "<table><tr><th>Keyword</th><th>Volume</th><th>Difficulty</th><th>CPC</th><th>Competitors Ranking</th></tr>"
            
            for _, row in gap_df.head(20).iterrows():
                html += f"<tr><td>{row['keyword']}</td><td>{row['volume']}</td>"
                html += f"<td>{row['difficulty']}</td><td>${row['cpc']}</td>"
                competitors_str = ', '.join(row['competitors_ranking']) if isinstance(row['competitors_ranking'], list) else row['competitors_ranking']
                html += f"<td>{competitors_str}</td></tr>"
                
            html += "</table>"
            
            if len(gap_df) > 20:
                html += f"<p>Showing 20 of {len(gap_df)} keywords in the content gap</p>"
                
        # Competitor content analysis
        if 'competitor_content' in competitor_data:
            html += "<h2>Competitor Content Analysis</h2>"
            
            for url, content_analysis in competitor_data['competitor_content'].items():
                html += f"<h3>Analysis for: {url}</h3>"
                
                html += "<table>"
                html += f"<tr><th>Title</th><td>{content_analysis.get('title', '')}</td></tr>"
                html += f"<tr><th>Meta Description</th><td>{content_analysis.get('meta_description', '')}</td></tr>"
                html += f"<tr><th>Word Count</th><td>{content_analysis.get('word_count', 0)}</td></tr>"
                html += f"<tr><th>Images</th><td>{content_analysis.get('image_count', 0)}</td></tr>"
                html += f"<tr><th>Internal Links</th><td>{content_analysis.get('internal_links', 0)}</td></tr>"
                html += f"<tr><th>External Links</th><td>{content_analysis.get('external_links', 0)}</td></tr>"
                
                if 'keyword_density' in content_analysis:
                    html += f"<tr><th>Keyword Density</th><td>{content_analysis['keyword_density']:.2f}%</td></tr>"
                    
                html += "</table>"
                
                if 'headings' in content_analysis:
                    html += "<h4>Heading Structure</h4>"
                    html += "<ul>"
                    
                    for level, headings in content_analysis['headings'].items():
                        for heading in headings:
                            html += f"<li><strong>{level.upper()}:</strong> {heading}</li>"
                            
                    html += "</ul>"
                    
                if 'common_phrases' in content_analysis:
                    html += "<h4>Common Phrases</h4>"
                    html += "<ul>"
                    
                    for phrase in content_analysis['common_phrases']:
                        html += f"<li>{phrase}</li>"
                        
                    html += "</ul>"
                    
        html += "</body></html>"
        
        # Save report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html)
            
        return report_file
        
    except Exception as e:
        logger.error(f"Error creating competitor report: {e}")
        return None

def print_table(data, headers=None):
    """
    Print data as a formatted table
    
    Args:
        data (list): List of data rows
        headers (list): List of column headers
    """
    try:
        if headers:
            print(tabulate(data, headers=headers, tablefmt="grid"))
        else:
            print(tabulate(data, tablefmt="grid"))
    except Exception as e:
        logger.error(f"Error printing table: {e}")
        # Fallback to basic printing
        if headers:
            print(" | ".join(headers))
            print("-" * (sum(len(h) for h in headers) + 3 * (len(headers) - 1)))
        for row in data:
            print(" | ".join(str(item) for item in row))

def export_to_csv(data, filename):
    """
    Export data to CSV
    
    Args:
        data (pandas.DataFrame or list): Data to export
        filename (str): Output filename
        
    Returns:
        bool: Success status
    """
    try:
        if isinstance(data, pd.DataFrame):
            data.to_csv(filename, index=False)
        else:
            pd.DataFrame(data).to_csv(filename, index=False)
            
        return True
        
    except Exception as e:
        logger.error(f"Error exporting data to CSV: {e}")
        return False

def export_to_json(data, filename):
    """
    Export data to JSON
    
    Args:
        data (dict or list): Data to export
        filename (str): Output filename
        
    Returns:
        bool: Success status
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        return True
        
    except Exception as e:
        logger.error(f"Error exporting data to JSON: {e}")
        return False