import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Import the actual module implementations
from modules.keyword_clustering import KeywordClusterer
from modules.competitor_audit import CompetitorAuditor
from modules.content_generator import ContentGenerator
from modules.opportunity_tracker import OpportunityTracker
from utils.reporting import (
    create_keyword_report, 
    create_opportunity_report, 
    create_competitor_report,
    print_table,
    export_to_csv,
    export_to_json
)
import config

# Configure logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
    
log_file = os.path.join(log_dir, f"seo_agent_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_keyword_clustering(args):
    """Run keyword clustering module"""
    logger.info("Running keyword clustering...")
    
    # Initialize KeywordClusterer
    clusterer = KeywordClusterer(config.DOMAIN, user_profiles=config.USER_PROFILES)
    
    # Get keywords
    seed_keywords = args.seed_keywords.split(',') if args.seed_keywords else None
    keywords_df = clusterer.fetch_keywords(seed_keywords=seed_keywords)
    
    # Cluster keywords
    clustered_df = clusterer.cluster_keywords(
        keywords_df, 
        n_clusters=args.clusters, 
        method=args.method
    )
    
    # Get top keywords by cluster
    top_keywords = clusterer.get_top_keywords_by_cluster(
        clustered_df, 
        metric=args.metric, 
        top_n=args.top_n
    )
    
    # Create report
    report_path = create_keyword_report(clustered_df, output_dir=args.output_dir)
    
    # Export data
    if args.export:
        export_file = os.path.join(args.output_dir, "clustered_keywords.csv")
        clustered_df.to_csv(export_file, index=False)
        logger.info(f"Exported clustered keywords to {export_file}")
        
    # Print results
    print("\n--- Keyword Clustering Results ---")
    print(f"Total keywords: {len(keywords_df)}")
    print(f"Clusters: {clustered_df['cluster'].nunique()}")
    print(f"Report saved to: {report_path}")
    
    # Print sample of top keywords by cluster
    print("\nSample of top keywords by cluster:")
    for cluster_label, keywords in list(top_keywords.items())[:5]:
        print(f"\nCluster: {cluster_label}")
        for i, keyword in enumerate(keywords[:3]):
            print(f"  {i+1}. {keyword}")
            
    return clustered_df

def run_competitor_audit(args):
    """Run competitor audit module"""
    logger.info("Running competitor audit...")
    
    competitors = args.competitors.split(',') if args.competitors else config.COMPETITORS
    auditor = CompetitorAuditor(config.DOMAIN, competitors=competitors)
    
    # Analyze content gap
    gap_analysis = auditor.analyze_content_gap(min_traffic=args.min_traffic)
    
    # Analyze SERP features for gap keywords
    top_gap_keywords = gap_analysis['keyword'].tolist()[:20]
    serp_analysis = auditor.analyze_serp_features(top_gap_keywords)
    
    # Analyze competitor content
    competitor_content = {}
    if args.analyze_content:
        for competitor in competitors[:3]:  # Limit to top 3 competitors
            top_pages = auditor.get_top_content(competitor)
            if not top_pages.empty:
                top_url = top_pages.iloc[0]['url']
                competitor_content[top_url] = auditor.analyze_competitor_content(top_url)
    
    # Combine results
    results = {
        'content_gap': gap_analysis,
        'serp_analysis': serp_analysis,
        'competitor_content': competitor_content
    }
    
    # Create report
    report_path = create_competitor_report(
        results, 
        domain=config.DOMAIN, 
        output_dir=args.output_dir
    )
    
    # Export data
    if args.export:
        export_file = os.path.join(args.output_dir, "content_gap.csv")
        gap_analysis.to_csv(export_file, index=False)
        logger.info(f"Exported content gap analysis to {export_file}")
        
    # Print results
    print("\n--- Competitor Audit Results ---")
    print(f"Analyzed competitors: {', '.join(competitors)}")
    print(f"Content gap keywords: {len(gap_analysis)}")
    print(f"Report saved to: {report_path}")
    
    # Print sample of gap keywords
    print("\nTop content gap keywords:")
    for i, (_, row) in enumerate(gap_analysis.head(5).iterrows()):
        print(f"  {i+1}. {row['keyword']} (Volume: {row['volume']}, Difficulty: {row['difficulty']})")
        
    return results

def run_content_generator(args):
    """Run content generator module"""
    logger.info("Running content generator...")
    
    # Initialize content generator with OpenAI API key or alternative
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("No OpenAI API key found. Using Claude API if available or free alternatives.")
        # Could use Claude API here instead or other alternatives
    
    generator = ContentGenerator(openai_api_key=api_key)
    
    # Generate outlines
    outlines = []
    keywords = args.keywords.split(',') if args.keywords else []
    
    for keyword in keywords:
        # Determine intent
        intent = args.intent if args.intent else "informational"
        
        # Generate outline
        outline = generator.generate_blog_outline(
            keyword, 
            intent,
            target_word_count=args.word_count
        )
        
        # Analyze SEO
        seo_analysis = generator.analyze_outline_seo(outline, keyword)
        
        # Refine if needed
        if seo_analysis['seo_score'] < 80:
            outline = generator.refine_outline(outline, seo_analysis, keyword)
            
        outlines.append({
            'keyword': keyword,
            'outline': outline,
            'seo_analysis': seo_analysis
        })
        
    # Export data
    if args.export:
        for i, outline_data in enumerate(outlines):
            keyword = outline_data['keyword']
            safe_keyword = ''.join(c if c.isalnum() else '_' for c in keyword)
            
            export_file = os.path.join(args.output_dir, f"outline_{safe_keyword}.json")
            
            with open(export_file, 'w') as f:
                json.dump(outline_data, f, indent=2)
                
            logger.info(f"Exported outline for '{keyword}' to {export_file}")
            
    # Print results
    print("\n--- Content Generation Results ---")
    print(f"Generated outlines: {len(outlines)}")
    
    for outline_data in outlines:
        keyword = outline_data['keyword']
        outline = outline_data['outline']
        seo_analysis = outline_data['seo_analysis']
        
        print(f"\nOutline for: {keyword}")
        print(f"Title: {outline.get('title', '')}")
        print(f"SEO Score: {seo_analysis['seo_score']}/100")
        print("Sections:")
        
        for i, section in enumerate(outline.get('sections', [])[:5]):
            print(f"  {i+1}. {section.get('heading', '')} ({section.get('level', '')}, {section.get('word_count', 0)} words)")
            
        if len(outline.get('sections', [])) > 5:
            print(f"  ... and {len(outline.get('sections', [])) - 5} more sections")
            
    return outlines

def run_opportunity_tracker(args):
    """Run opportunity tracker module"""
    logger.info("Running opportunity tracker...")
    
    tracker = OpportunityTracker(config.DOMAIN, storage_dir=args.output_dir)
    
    # Track keywords if specified
    if args.track_keywords:
        keywords = args.track_keywords.split(',')
        rankings = tracker.track_keyword_rankings(keywords, update=True)
        print(f"Tracked rankings for {len(keywords)} keywords")
        
    # Generate weekly report
    weekly_report = tracker.generate_weekly_report()
    
    # Create report
    report_path = create_opportunity_report(
        weekly_report['content_opportunities'], 
        output_dir=args.output_dir
    )
    
    # Export data
    if args.export:
        export_file = os.path.join(args.output_dir, "weekly_opportunities.json")
        with open(export_file, 'w') as f:
            json.dump(weekly_report, f, indent=2)
        logger.info(f"Exported weekly opportunities to {export_file}")
        
    # Print results
    print("\n--- Weekly Opportunity Results ---")
    print(f"Trending topics: {len(weekly_report['trending_topics'])}")
    print(f"Content opportunities: {len(weekly_report['content_opportunities'])}")
    print(f"Report saved to: {report_path}")
    
    # Print top opportunities
    print("\nTop content opportunities:")
    for i, opportunity in enumerate(weekly_report['content_opportunities'][:5]):
        print(f"  {i+1}. {opportunity['keyword']} (Score: {opportunity['opportunity_score']})")
        
    return weekly_report

def run_all(args):
    """Run all modules in sequence"""
    logger.info("Running all modules...")
    
    # Run keyword clustering
    clustered_df = run_keyword_clustering(args)
    
    # Use top keywords from clustering for competitor audit
    top_keywords = clustered_df.sort_values('volume', ascending=False)['keyword'].head(20).tolist()
    args.keywords = ','.join(top_keywords[:5])  # Use top 5 for content generation
    
    # Run competitor audit
    competitor_results = run_competitor_audit(args)
    
    # Run content generator
    content_results = run_content_generator(args)
    
    # Use top keywords for opportunity tracking
    args.track_keywords = ','.join(top_keywords)
    
    # Run opportunity tracker
    opportunity_results = run_opportunity_tracker(args)
    
    # Final report
    print("\n--- SEO AI Agent Execution Complete ---")
    print(f"Processed {len(clustered_df)} keywords")
    print(f"Generated {len(content_results)} content outlines")
    print(f"Identified {len(opportunity_results['content_opportunities'])} content opportunities")
    print(f"All reports saved to: {args.output_dir}")
    
    return {
        "keyword_clusters": clustered_df,
        "competitor_analysis": competitor_results,
        "content_outlines": content_results,
        "opportunities": opportunity_results
    }

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SEO AI Agent for Asendia AI")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Keyword clustering parser
    cluster_parser = subparsers.add_parser("cluster", help="Run keyword clustering")
    cluster_parser.add_argument("--seed-keywords", help="Comma-separated list of seed keywords")
    cluster_parser.add_argument("--clusters", type=int, help="Number of clusters")
    cluster_parser.add_argument("--method", choices=["kmeans", "dbscan", "graph"], default="kmeans", help="Clustering method")
    cluster_parser.add_argument("--metric", default="volume", help="Metric for ranking keywords")
    cluster_parser.add_argument("--top-n", type=int, default=5, help="Number of top keywords per cluster")
    cluster_parser.add_argument("--output-dir", default="data", help="Output directory")
    cluster_parser.add_argument("--export", action="store_true", help="Export data to CSV")
    
    # Competitor audit parser
    audit_parser = subparsers.add_parser("audit", help="Run competitor audit")
    audit_parser.add_argument("--competitors", help="Comma-separated list of competitor domains")
    audit_parser.add_argument("--min-traffic", type=int, default=100, help="Minimum traffic threshold")
    audit_parser.add_argument("--analyze-content", action="store_true", help="Analyze competitor content")
    audit_parser.add_argument("--output-dir", default="data", help="Output directory")
    audit_parser.add_argument("--export", action="store_true", help="Export data to CSV")
    
    # Content generator parser
    content_parser = subparsers.add_parser("content", help="Run content generator")
    content_parser.add_argument("--keywords", required=True, help="Comma-separated list of keywords")
    content_parser.add_argument("--intent", choices=["informational", "commercial", "transactional", "navigational"], default="informational", help="Search intent")
    content_parser.add_argument("--word-count", type=int, default=1500, help="Target word count")
    content_parser.add_argument("--output-dir", default="data", help="Output directory")
    content_parser.add_argument("--export", action="store_true", help="Export data to JSON")
    
    # Opportunity tracker parser
    opportunity_parser = subparsers.add_parser("opportunity", help="Run opportunity tracker")
    opportunity_parser.add_argument("--track-keywords", help="Comma-separated list of keywords to track")
    opportunity_parser.add_argument("--output-dir", default="data", help="Output directory")
    opportunity_parser.add_argument("--export", action="store_true", help="Export data to JSON")
    
    # All-in-one parser
    all_parser = subparsers.add_parser("all", help="Run all modules")
    all_parser.add_argument("--seed-keywords", help="Comma-separated list of seed keywords")
    all_parser.add_argument("--competitors", help="Comma-separated list of competitor domains")
    all_parser.add_argument("--min-traffic", type=int, default=100, help="Minimum traffic threshold")
    all_parser.add_argument("--analyze-content", action="store_true", help="Analyze competitor content")
    all_parser.add_argument("--word-count", type=int, default=1500, help="Target word count")
    all_parser.add_argument("--output-dir", default="data", help="Output directory")
    all_parser.add_argument("--export", action="store_true", help="Export data to CSV/JSON")
    all_parser.add_argument("--clusters", type=int, help="Number of clusters")
    all_parser.add_argument("--method", choices=["kmeans", "dbscan", "graph"], default="kmeans", help="Clustering method")
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    if hasattr(args, 'output_dir') and not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        
    # Run appropriate command
    if args.command == "cluster":
        run_keyword_clustering(args)
    elif args.command == "audit":
        run_competitor_audit(args)
    elif args.command == "content":
        run_content_generator(args)
    elif args.command == "opportunity":
        run_opportunity_tracker(args)
    elif args.command == "all":
        run_all(args)
    else:
        parser.print_help()
        
if __name__ == "__main__":
    main()