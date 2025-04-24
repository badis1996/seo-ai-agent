# Asendia AI SEO Agent

An AI-powered SEO agent that helps Asendia AI grow inbound traffic without hiring a strategist or agency.

## Features

- **Keyword Clustering**: Clusters keywords by intent and user profile
- **Competitor Audit**: Audits competitor content and identifies SERP gaps
- **Content Generation**: Generates outlines for SEO-optimized blog posts
- **Opportunity Tracking**: Flags new content opportunities weekly

## Free Alternatives for SEO Tools

This SEO Agent is specifically designed to use free alternatives instead of expensive API providers:

### Keyword Research
- Uses Google Keyword Planner (free with Google Ads account)
- Leverages Google Trends API (completely free)
- Can use Google Search Console data if available
- Includes fallback mock implementations for development

### Competitor Analysis
- Uses direct web scraping within Terms of Service
- Leverages SimilarWeb free tier 
- Implements free SERP analysis techniques
- Includes fallback mock implementations for development

### Content Generation
- Can use OpenAI's trial credits or cheaper models
- Includes complete template-based alternative when API is unavailable
- Generates quality outlines without requiring paid tools

### Opportunity Tracking
- Uses Google Trends for trending topics (free)
- Implements free SERP tracking alternatives
- Includes robust fallback options for all features

## Project Overview

The SEO AI Agent is designed to automate the entire SEO workflow for Asendia AI, which helps companies qualify candidates in under 24 hours. The agent works by:

1. **Clustering Keywords**: The agent groups keywords based on user intent, profile, and semantic similarity.
2. **Auditing Competitors**: It analyzes competitor content to identify SERP gaps and opportunities.
3. **Generating Content Outlines**: The agent creates SEO-optimized outlines for blog posts.
4. **Tracking Opportunities**: It automatically identifies new content opportunities weekly.

All of this is done without the need to hire an SEO strategist or agency, enabling Asendia AI to grow inbound traffic efficiently.

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/badis1996/seo-ai-agent.git
   cd seo-ai-agent
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Download required NLTK and spaCy data:
   ```
   python -m nltk.downloader punkt stopwords
   python -m spacy download en_core_web_md
   ```

5. Create a `.env` file with your optional API keys:
   ```
   # Optional API keys - will use free alternatives if not provided
   OPENAI_API_KEY=your_openai_api_key_optional
   
   # Required settings
   DOMAIN=asendia.ai
   COMPETITORS=competitor1.com,competitor2.com,competitor3.com
   ```

## Usage

### Using Docker

The easiest way to run the SEO agent is using Docker:

```
docker-compose up -d
```

This will start the SEO agent and the weekly scheduler in separate containers.

### Using Command Line

You can run the SEO agent directly using the command line:

```
# Run all modules
python main.py all --export

# Run specific modules
python main.py cluster --seed-keywords "ai recruiter,talent acquisition,recruitment automation"
python main.py audit --competitors "competitor1.com,competitor2.com"
python main.py content --keywords "ai recruiter,talent acquisition"
python main.py opportunity --track-keywords "ai recruiter,talent acquisition"

# Run the weekly scheduler
python schedule_weekly.py
```

### Example Usage Scenarios

1. **Find and Cluster Keywords**:
   ```
   python main.py cluster --seed-keywords "recruitment automation,ai recruiter,talent acquisition" --method kmeans --clusters 5 --export
   ```

2. **Analyze Competitors**:
   ```
   python main.py audit --competitors "hiretual.com,hireez.com,eightfold.ai" --analyze-content --export
   ```

3. **Generate Content Outlines**:
   ```
   python main.py content --keywords "ai recruiter benefits,recruitment automation roi" --intent informational --word-count 2000 --export
   ```

4. **Track Weekly Opportunities**:
   ```
   python main.py opportunity --track-keywords "ai recruiting,talent acquisition automation,recruitment technology" --export
   ```

## Project Structure

```
seo-agent/
├── __init__.py
├── config.py              # Configuration settings
├── main.py                # Main entry point
├── modules/
│   ├── __init__.py
│   ├── keyword_clustering.py  # Keyword intent clustering
│   ├── competitor_audit.py    # Competitor content analysis
│   ├── content_generator.py   # Blog outline generator
│   └── opportunity_tracker.py # Weekly opportunity detection
├── utils/
│   ├── __init__.py
│   ├── api_clients.py     # Free alternative API clients
│   ├── data_processing.py # Data processing utilities
│   └── reporting.py       # Reporting utilities
└── tests/                 # Unit tests
```

## Output

The SEO agent generates various outputs:

- **Data**: Raw data files in CSV/JSON format
- **Reports**: HTML reports with analysis and recommendations
- **Logs**: Detailed logs of the agent's operations

All outputs are stored in the `data`, `reports`, and `logs` directories.

## Customization

You can customize the agent by modifying the `config.py` file:

- **Domain**: Your domain name
- **Competitors**: List of competitor domains
- **User Profiles**: Target user profiles for keyword clustering
- **Industry Verticals**: Industry verticals for content targeting

## Development

### Running Tests

To run the unit tests:

```
python -m unittest discover tests
```

### Extending the Agent

You can extend the agent by:

1. Adding new API clients in `utils/api_clients.py`
2. Creating new data processing methods in `utils/data_processing.py`
3. Implementing additional reporting formats in `utils/reporting.py`
4. Enhancing the modules with new capabilities

## License

Copyright (c) 2025 Asendia AI. All rights reserved.