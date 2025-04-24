import json
import logging
import os
import re
from datetime import datetime
import random
import requests
from bs4 import BeautifulSoup
import nltk

# Import free alternative clients
from utils.api_clients import SerpAnalysisClient

class ContentGenerator:
    def __init__(self, openai_api_key=None):
        """
        Initialize the content generator
        
        Args:
            openai_api_key (str): OpenAI API key for content generation
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.serp_client = SerpAnalysisClient()
        self.logger = logging.getLogger(__name__)
        
        # Initialize NLTK if needed
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            self.logger.info("Downloading NLTK punkt tokenizer")
            nltk.download('punkt', quiet=True)
            
    def generate_blog_outline(self, keyword, intent, target_word_count=1500, competitor_insights=None):
        """
        Generate an SEO-optimized blog post outline based on a keyword
        
        Args:
            keyword (str): Target keyword for the blog post
            intent (str): Search intent (informational, commercial, etc.)
            target_word_count (int): Target word count for the blog post
            competitor_insights (list): Insights from competitor content
            
        Returns:
            dict: Blog post outline including title, meta description, and sections
        """
        self.logger.info(f"Generating blog outline for keyword: {keyword}, intent: {intent}")
        
        # Get SERP results for the keyword
        serp_results = self.serp_client.get_serp(keyword, num_results=5)
        
        # Extract titles and snippets
        competing_titles = []
        competing_snippets = []
        
        for result in serp_results:
            if 'title' in result:
                competing_titles.append(result['title'])
            if 'snippet' in result:
                competing_snippets.append(result['snippet'])
                
        # Try to use OpenAI API if available
        if self.openai_api_key:
            try:
                return self._generate_outline_with_openai(
                    keyword=keyword,
                    intent=intent,
                    competing_titles=competing_titles,
                    competing_snippets=competing_snippets,
                    competitor_insights=competitor_insights,
                    target_word_count=target_word_count
                )
            except Exception as e:
                self.logger.error(f"Error using OpenAI API: {e}")
                # Fall back to template-based approach
        
        # If OpenAI is not available, use a template-based approach
        return self._generate_outline_from_template(
            keyword=keyword,
            intent=intent,
            competing_titles=competing_titles,
            competing_snippets=competing_snippets,
            target_word_count=target_word_count
        )
            
    def _generate_outline_with_openai(self, keyword, intent, competing_titles, competing_snippets, 
                                     competitor_insights=None, target_word_count=1500):
        """Generate outline using OpenAI API"""
        import openai
        openai.api_key = self.openai_api_key
        
        # Create system prompt
        system_prompt = self._create_outline_system_prompt(
            keyword=keyword,
            intent=intent,
            competing_titles=competing_titles,
            competing_snippets=competing_snippets,
            competitor_insights=competitor_insights,
            target_word_count=target_word_count
        )
        
        # Generate outline using OpenAI
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Using cheaper 3.5 model instead of 4.0
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create an SEO-optimized outline for a blog post targeting the keyword: {keyword}"}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        outline = json.loads(response.choices[0].message.content)
        
        # Add metadata
        outline['target_keyword'] = keyword
        outline['search_intent'] = intent
        outline['target_word_count'] = target_word_count
        outline['date_generated'] = datetime.now().strftime("%Y-%m-%d")
        
        return outline
    
    def _create_outline_system_prompt(self, keyword, intent, competing_titles, competing_snippets, 
                                     competitor_insights=None, target_word_count=1500):
        """Create a system prompt for outline generation"""
        prompt = f"""You are an expert SEO content strategist who specializes in creating highly effective content outlines for recruiters and talent acquisition professionals. Your task is to create a comprehensive, SEO-optimized blog post outline targeting the keyword: "{keyword}" with {intent} search intent.

The outline should include:
1. A compelling, click-worthy title (50-60 characters) that includes the target keyword naturally
2. A meta description (150-160 characters) that includes the target keyword and encourages clicks
3. A well-structured outline with H2 and H3 sections, including:
   - Introduction section with hook and value proposition
   - 4-7 main sections with meaningful H2 headings
   - Relevant H3 subsections where appropriate
   - A conclusion section
4. For each section, include:
   - The heading (H2/H3)
   - A brief description of the content to include (2-3 sentences)
   - Approximate word count for the section
   - Any suggestions for statistics, examples, or key points to include

The blog post should target approximately {target_word_count} words total.

Based on competing content, here are some titles ranking well for this keyword:
"""
        
        # Add competing titles to the prompt
        for i, title in enumerate(competing_titles[:3]):
            prompt += f"- {title}\n"
            
        prompt += "\nHere are snippets from competing content:\n"
        
        # Add competing snippets to the prompt
        for i, snippet in enumerate(competing_snippets[:3]):
            clean_snippet = re.sub(r'\s+', ' ', snippet).strip()
            prompt += f"- {clean_snippet}\n"
            
        # Add competitor insights if available
        if competitor_insights:
            prompt += "\nInsights from competitor content analysis:\n"
            for insight in competitor_insights[:3]:
                prompt += f"- {insight}\n"
                
        prompt += f"""
Target audience: Recruitment professionals and talent acquisition teams who want to optimize their hiring process and reduce time-to-hire.

Your outline should be better and more comprehensive than the competing content, covering aspects they might have missed. Make sure the structure is logical and creates a smooth reading experience.

IMPORTANT: Return your response as a JSON object with the following structure:
{{
  "title": "Your compelling blog post title",
  "meta_description": "Your meta description",
  "sections": [
    {{
      "heading": "Introduction",
      "level": "H2",
      "description": "Description of section content",
      "word_count": 150,
      "key_points": ["point 1", "point 2"]
    }},
    ...more sections...
  ],
  "estimated_total_word_count": 1500
}}
"""
        return prompt
    
    def _generate_outline_from_template(self, keyword, intent, competing_titles, competing_snippets, target_word_count=1500):
        """
        Generate an outline using templates when API is not available
        
        This uses a template-based approach with some randomization for variety
        """
        # Create title variations based on intent
        title_templates = {
            'informational': [
                f"The Complete Guide to {keyword.title()} in {datetime.now().year}",
                f"What is {keyword.title()}? Everything You Need to Know",
                f"Understanding {keyword.title()}: A Comprehensive Guide",
                f"How {keyword.title()} Works: The Ultimate Guide",
                f"{keyword.title()}: Definition, Benefits and Best Practices"
            ],
            'commercial': [
                f"Top 10 {keyword.title()} Solutions for Recruiters",
                f"Best {keyword.title()} Tools to Improve Your Hiring Process",
                f"Comparing the Best {keyword.title()} Platforms in {datetime.now().year}",
                f"{keyword.title()}: Which Solution is Right for Your Business?",
                f"How to Choose the Right {keyword.title()} Tool: Buyer's Guide"
            ],
            'transactional': [
                f"How to Implement {keyword.title()} in Your Business Today",
                f"Get Started with {keyword.title()}: Step-by-Step Guide",
                f"Setting Up {keyword.title()}: A Practical Guide",
                f"Implementing {keyword.title()}: Best Practices and Tips",
                f"{keyword.title()} Setup Guide for Recruitment Teams"
            ],
            'navigational': [
                f"{keyword.title()}: Features, Benefits and Use Cases",
                f"Exploring {keyword.title()} for Modern Recruiting",
                f"{keyword.title()}: The Essential Guide for HR Professionals",
                f"What Makes {keyword.title()} Different? A Detailed Look",
                f"{keyword.title()}: A Review and Practical Guide"
            ]
        }
        
        # Default to informational intent if intent is not recognized
        available_titles = title_templates.get(intent, title_templates['informational'])
        
        # Generate a title
        title = random.choice(available_titles)
        
        # Generate meta description
        meta_templates = [
            f"Learn everything about {keyword} in our comprehensive guide. Discover the best practices, tools, and strategies for effective {keyword} in {datetime.now().year}.",
            f"Looking to improve your {keyword} strategy? Our detailed guide covers everything you need to know about implementing {keyword} in your recruitment process.",
            f"Discover how {keyword} can transform your hiring process. This guide covers all aspects of {keyword} with practical tips and expert insights.",
            f"A complete breakdown of {keyword} for recruiters and talent acquisition teams. Learn how to implement and optimize {keyword} for your business."
        ]
        meta_description = random.choice(meta_templates)
        
        # Ensure meta description is not too long
        if len(meta_description) > 160:
            meta_description = meta_description[:157] + "..."
            
        # Generate sections based on intent
        sections = []
        
        # Introduction section (always included)
        intro_section = {
            "heading": "Introduction",
            "level": "H2",
            "description": f"Introduction to {keyword} and why it matters for recruiters and talent acquisition teams.",
            "word_count": random.randint(150, 250),
            "key_points": [
                f"Definition of {keyword}",
                "Importance in modern recruitment",
                "Overview of what the article covers"
            ]
        }
        sections.append(intro_section)
        
        # Generate main sections based on intent
        if intent == 'informational':
            informational_sections = [
                {
                    "heading": f"What is {keyword.title()}?",
                    "level": "H2",
                    "description": f"Detailed explanation of {keyword} and how it fits into the recruitment ecosystem.",
                    "word_count": random.randint(200, 350),
                    "key_points": [
                        f"Clear definition of {keyword}",
                        "Historical context and evolution",
                        "Core components and functionality"
                    ]
                },
                {
                    "heading": f"How {keyword.title()} Works",
                    "level": "H2",
                    "description": f"Step-by-step explanation of how {keyword} works in practice.",
                    "word_count": random.randint(250, 400),
                    "key_points": [
                        "Technical overview",
                        "Process breakdown",
                        "Key mechanisms and functioning"
                    ]
                },
                {
                    "heading": f"Benefits of {keyword.title()}",
                    "level": "H2",
                    "description": f"Key advantages and benefits of implementing {keyword} in your recruitment process.",
                    "word_count": random.randint(200, 350),
                    "key_points": [
                        "Time savings",
                        "Quality of hire improvements",
                        "Cost reduction",
                        "Candidate experience enhancement"
                    ]
                },
                {
                    "heading": f"Common Challenges with {keyword.title()} and How to Overcome Them",
                    "level": "H2",
                    "description": f"Addressing common obstacles when implementing {keyword}.",
                    "word_count": random.randint(200, 300),
                    "key_points": [
                        "Technical challenges",
                        "Adoption issues",
                        "Integration problems",
                        "Practical solutions"
                    ]
                }
            ]
            sections.extend(informational_sections)
            
        elif intent == 'commercial':
            commercial_sections = [
                {
                    "heading": f"Top {keyword.title()} Solutions in {datetime.now().year}",
                    "level": "H2",
                    "description": f"Review of the best {keyword} solutions currently available on the market.",
                    "word_count": random.randint(300, 450),
                    "key_points": [
                        "Evaluation criteria",
                        "Top 5-7 solutions",
                        "Comparison of key features"
                    ]
                },
                {
                    "heading": f"Key Features to Look for in {keyword.title()} Tools",
                    "level": "H2",
                    "description": f"Essential features and capabilities that make a {keyword} solution effective.",
                    "word_count": random.randint(250, 350),
                    "key_points": [
                        "Must-have features",
                        "Nice-to-have features",
                        "Integration capabilities",
                        "Scalability considerations"
                    ]
                },
                {
                    "heading": f"ROI of {keyword.title()} Solutions",
                    "level": "H2",
                    "description": f"Analysis of the return on investment for {keyword} implementation.",
                    "word_count": random.randint(200, 300),
                    "key_points": [
                        "Cost-benefit analysis",
                        "Time-to-value metrics",
                        "Success stories and case studies",
                        "Budget considerations"
                    ]
                }
            ]
            sections.extend(commercial_sections)
            
        elif intent == 'transactional':
            transactional_sections = [
                {
                    "heading": f"Step-by-Step Guide to Implementing {keyword.title()}",
                    "level": "H2",
                    "description": f"Detailed walkthrough of implementing {keyword} in your organization.",
                    "word_count": random.randint(350, 500),
                    "key_points": [
                        "Preparation steps",
                        "Implementation phases",
                        "Testing and validation",
                        "Common pitfalls to avoid"
                    ]
                },
                {
                    "heading": f"Required Resources for {keyword.title()} Implementation",
                    "level": "H2",
                    "description": f"Overview of the resources needed to successfully implement {keyword}.",
                    "word_count": random.randint(200, 300),
                    "key_points": [
                        "Budget considerations",
                        "Team requirements",
                        "Time investment",
                        "Technology requirements"
                    ]
                },
                {
                    "heading": f"Measuring the Success of Your {keyword.title()} Implementation",
                    "level": "H2",
                    "description": f"Key metrics and KPIs to track the success of your {keyword} implementation.",
                    "word_count": random.randint(200, 300),
                    "key_points": [
                        "Key performance indicators",
                        "Measurement techniques",
                        "Benchmarking strategies",
                        "Continuous improvement process"
                    ]
                }
            ]
            sections.extend(transactional_sections)
            
        else:  # Default or navigational intent
            default_sections = [
                {
                    "heading": f"Key Features of {keyword.title()}",
                    "level": "H2",
                    "description": f"Overview of the main features and capabilities of {keyword}.",
                    "word_count": random.randint(250, 400),
                    "key_points": [
                        "Core functionality",
                        "Unique features",
                        "Technology overview",
                        "Differentiating factors"
                    ]
                },
                {
                    "heading": f"Implementing {keyword.title()} in Your Recruitment Process",
                    "level": "H2",
                    "description": f"How to effectively integrate {keyword} into your existing recruitment workflow.",
                    "word_count": random.randint(250, 350),
                    "key_points": [
                        "Integration strategies",
                        "Best practices",
                        "Change management",
                        "Staff training"
                    ]
                },
                {
                    "heading": f"Benefits and ROI of {keyword.title()}",
                    "level": "H2",
                    "description": f"The business case for implementing {keyword} in your organization.",
                    "word_count": random.randint(200, 300),
                    "key_points": [
                        "Tangible benefits",
                        "Intangible benefits",
                        "Return on investment",
                        "Success stories"
                    ]
                }
            ]
            sections.extend(default_sections)
            
        # Conclusion section (always included)
        conclusion_section = {
            "heading": "Conclusion",
            "level": "H2",
            "description": f"Summary of key points and final thoughts on {keyword}.",
            "word_count": random.randint(100, 200),
            "key_points": [
                "Recap of main points",
                "Final recommendations",
                "Next steps"
            ]
        }
        sections.append(conclusion_section)
        
        # Calculate total word count
        total_word_count = sum(section['word_count'] for section in sections)
        
        # Create the final outline
        outline = {
            "title": title,
            "meta_description": meta_description,
            "sections": sections,
            "target_keyword": keyword,
            "search_intent": intent,
            "target_word_count": target_word_count,
            "estimated_total_word_count": total_word_count,
            "date_generated": datetime.now().strftime("%Y-%m-%d")
        }
        
        return outline
        
    def analyze_outline_seo(self, outline, keyword):
        """
        Analyze an outline for SEO optimization
        
        Args:
            outline (dict): Blog post outline to analyze
            keyword (str): Target keyword
            
        Returns:
            dict: SEO analysis and recommendations
        """
        analysis = {
            'keyword_in_title': keyword.lower() in outline.get('title', '').lower(),
            'title_length': len(outline.get('title', '')),
            'meta_description_length': len(outline.get('meta_description', '')),
            'keyword_in_meta_description': keyword.lower() in outline.get('meta_description', '').lower(),
            'section_count': len(outline.get('sections', [])),
            'section_analysis': [],
            'recommendations': []
        }
        
        # Title analysis
        if not analysis['keyword_in_title']:
            analysis['recommendations'].append(
                f"Add the target keyword '{keyword}' to the title"
            )
            
        if analysis['title_length'] < 30:
            analysis['recommendations'].append(
                "Title is too short (under 30 characters). Aim for 50-60 characters"
            )
        elif analysis['title_length'] > 60:
            analysis['recommendations'].append(
                "Title is too long (over 60 characters). Consider shortening it"
            )
            
        # Meta description analysis
        if not analysis['keyword_in_meta_description']:
            analysis['recommendations'].append(
                f"Add the target keyword '{keyword}' to the meta description"
            )
            
        if analysis['meta_description_length'] < 120:
            analysis['recommendations'].append(
                "Meta description is too short (under 120 characters). Aim for 150-160 characters"
            )
        elif analysis['meta_description_length'] > 160:
            analysis['recommendations'].append(
                "Meta description is too long (over 160 characters). Consider shortening it"
            )
            
        # Section analysis
        keyword_in_h2 = False
        total_word_count = 0
        
        for section in outline.get('sections', []):
            heading = section.get('heading', '')
            level = section.get('level', '')
            word_count = section.get('word_count', 0)
            total_word_count += word_count
            
            section_analysis = {
                'heading': heading,
                'level': level,
                'word_count': word_count,
                'keyword_in_heading': keyword.lower() in heading.lower()
            }
            
            if level == 'H2' and keyword.lower() in heading.lower():
                keyword_in_h2 = True
                
            analysis['section_analysis'].append(section_analysis)
            
        # Check if keyword is in at least one H2
        if not keyword_in_h2:
            analysis['recommendations'].append(
                f"Add the target keyword '{keyword}' to at least one H2 heading"
            )
            
        # Overall structure analysis
        if analysis['section_count'] < 5:
            analysis['recommendations'].append(
                "Consider adding more sections to make the content more comprehensive"
            )
            
        # Word count analysis
        target_word_count = outline.get('target_word_count', 1500)
        if total_word_count < target_word_count * 0.8:
            analysis['recommendations'].append(
                f"Content may be too thin. Current word count estimate is {total_word_count}, " +
                f"which is below the target of {target_word_count}"
            )
            
        # Overall score based on the number of recommendations
        recommendation_count = len(analysis['recommendations'])
        if recommendation_count == 0:
            analysis['seo_score'] = 100
        elif recommendation_count <= 2:
            analysis['seo_score'] = 90 - (recommendation_count * 5)
        elif recommendation_count <= 5:
            analysis['seo_score'] = 80 - ((recommendation_count - 2) * 5)
        else:
            analysis['seo_score'] = 60 - ((recommendation_count - 5) * 5)
            
        analysis['seo_score'] = max(0, min(100, analysis['seo_score']))
        
        return analysis
    
    def refine_outline(self, outline, seo_analysis, keyword):
        """
        Refine a blog post outline based on SEO analysis
        
        Args:
            outline (dict): Original blog post outline
            seo_analysis (dict): SEO analysis results
            keyword (str): Target keyword
            
        Returns:
            dict: Refined blog post outline
        """
        if seo_analysis['seo_score'] >= 90:
            # Outline is already well-optimized
            return outline
            
        # Create a copy of the original outline
        refined_outline = dict(outline)
        
        # Apply recommendations
        recommendations = seo_analysis.get('recommendations', [])
        for recommendation in recommendations:
            if "Add the target keyword" in recommendation and "to the title" in recommendation:
                # Ensure keyword is in title
                if keyword.lower() not in refined_outline.get('title', '').lower():
                    refined_outline['title'] = f"{keyword.title()}: {refined_outline.get('title', '')}"
                    
            elif "Add the target keyword" in recommendation and "to the meta description" in recommendation:
                # Ensure keyword is in meta description
                if keyword.lower() not in refined_outline.get('meta_description', '').lower():
                    refined_outline['meta_description'] = f"Learn about {keyword} in our guide. {refined_outline.get('meta_description', '')}"
                    
            elif "Title is too short" in recommendation:
                # Expand title if too short
                if len(refined_outline.get('title', '')) < 30:
                    refined_outline['title'] = f"{refined_outline.get('title', '')} - Complete Guide & Best Practices"
                    
            elif "Title is too long" in recommendation:
                # Shorten title if too long
                if len(refined_outline.get('title', '')) > 60:
                    refined_outline['title'] = refined_outline.get('title', '')[:57] + "..."
                    
            elif "Meta description is too short" in recommendation:
                # Expand meta description if too short
                if len(refined_outline.get('meta_description', '')) < 120:
                    refined_outline['meta_description'] += " Discover expert tips, strategies, and tools to improve your recruitment process."
                    
            elif "Meta description is too long" in recommendation:
                # Shorten meta description if too long
                if len(refined_outline.get('meta_description', '')) > 160:
                    refined_outline['meta_description'] = refined_outline.get('meta_description', '')[:157] + "..."
                    
            elif "Add the target keyword" in recommendation and "to at least one H2 heading" in recommendation:
                # Add keyword to an H2 heading
                for i, section in enumerate(refined_outline.get('sections', [])):
                    if section.get('level') == 'H2' and i > 0 and i < len(refined_outline.get('sections', [])) - 1:
                        # Don't modify introduction or conclusion
                        if keyword.lower() not in section.get('heading', '').lower():
                            section['heading'] = f"{keyword.title()}: {section['heading']}"
                            break
                            
            elif "Consider adding more sections" in recommendation:
                # Add more sections if needed
                if len(refined_outline.get('sections', [])) < 5:
                    # Find where to insert new section (before conclusion)
                    insert_index = len(refined_outline.get('sections', [])) - 1
                    if insert_index < 1:
                        insert_index = 1
                        
                    # Add a new section
                    new_section = {
                        "heading": f"Best Practices for {keyword.title()}",
                        "level": "H2",
                        "description": f"Recommendations and best practices for implementing {keyword} effectively.",
                        "word_count": 250,
                        "key_points": [
                            "Expert recommendations",
                            "Industry best practices",
                            "Tips for success"
                        ]
                    }
                    refined_outline['sections'].insert(insert_index, new_section)
        
        # Update metadata
        refined_outline['date_generated'] = datetime.now().strftime("%Y-%m-%d")
        refined_outline['refined'] = True
        
        # Update estimated total word count
        total_word_count = sum(section.get('word_count', 0) for section in refined_outline.get('sections', []))
        refined_outline['estimated_total_word_count'] = total_word_count
        
        return refined_outline
    
    def generate_content_for_section(self, section, keyword):
        """
        Generate content for a single section of a blog post
        
        Args:
            section (dict): Section data including heading and description
            keyword (str): Target keyword for the blog post
            
        Returns:
            str: Generated content for the section
        """
        # Try to use OpenAI API if available
        if self.openai_api_key:
            try:
                return self._generate_section_content_with_openai(section, keyword)
            except Exception as e:
                self.logger.error(f"Error using OpenAI API for section content: {e}")
                # Fall back to template approach
        
        # Use template-based content generation if API is not available
        return self._generate_section_content_from_template(section, keyword)