"""
Media Bias Analysis Tool

This script analyzes news coverage from different sources to identify potential political bias.
It uses web scraping and AI to analyze content from AP News, Drudge Report, and Alternet,
providing insights into story selection, language, source attribution, and framing.
"""

import os
import json
import time
import subprocess
import streamlit as st
from bs4 import BeautifulSoup
from newspaper import Article
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import ollama

def get_bias_analysis():
    """
    Analyzes news content from multiple sources and returns a bias analysis.
    
    Returns:
        str: A markdown-formatted analysis of political bias in the news sources.
    """
    # Ensure the model is loaded
    subprocess.run(["ollama", "pull", "gemma3:4b"])

    # Constants
    MODEL = "gemma3:4b"

    class Website:
        """
        A class to handle web scraping and content extraction from news websites.
        """
        def __init__(self, url):
            """
            Initialize the Website object and extract content from the given URL.
            
            Args:
                url (str): The URL of the website to analyze.
            """
            self.url = url
            
            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36')
            
            # Initialize the Chrome driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                # Load the page
                driver.get(url)
                time.sleep(5)  # Wait for dynamic content
                
                # Get the page source
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Get the title
                self.title = soup.title.string if soup.title else "No title found"
                
                # Extract main content
                main_content = None
                content_selectors = [
                    'main', 
                    'article', 
                    '[class*="content"]', 
                    '[class*="main"]',
                    '[class*="article"]',
                    '[class*="story"]'
                ]
                
                for selector in content_selectors:
                    main_content = soup.select_one(selector)
                    if main_content:
                        break
                
                if not main_content:
                    main_content = soup.body
                
                if main_content:
                    # Remove navigation and other non-content elements
                    for nav in main_content.find_all(['nav', 'header', 'footer', 'aside', 'script', 'style']):
                        nav.decompose()
                    
                    # Get text content
                    self.text = main_content.get_text(separator="\n", strip=True)
                    
                    # Clean up the text
                    lines = []
                    for line in self.text.split('\n'):
                        line = line.strip()
                        if line and len(line) > 20:  # Only keep substantial lines
                            lines.append(line)
                    self.text = '\n'.join(lines)
                else:
                    self.text = "No content found"
                
                # Try to get article content using newspaper3k
                try:
                    article = Article(url)
                    article.download()
                    article.parse()
                    if article.text:
                        self.text = article.text
                except Exception as e:
                    print(f"Newspaper3k extraction failed: {e}")
            
            finally:
                driver.quit()

    # Define our system prompt
    system_prompt = """You are a news summarizer. Your task is to:
1. Read the provided website content
2. Identify and summarize the main news stories
3. Present the summaries in a structured JSON format
4. Ignore any website navigation, ads, or non-news content

Format your response as a JSON array of objects, where each object has the following structure:
{
    "title": "Brief headline of the story",
    "description": "1-2 sentence summary of the story",
    "media_outlet": "Name of the news source"
}

CRITICAL INSTRUCTIONS:
- Your response should ONLY contain the JSON array
- DO NOT include any thinking process, analysis, or internal monologue
- DO NOT use <think> tags or any other markers
- DO NOT explain your reasoning or approach
- DO NOT include any text that isn't part of the JSON structure
- Start directly with the JSON array"""

    def user_prompt_for(website):
        """
        Generate a user prompt for the LLM based on the website content.
        
        Args:
            website (Website): The Website object containing the content to analyze.
            
        Returns:
            str: The formatted user prompt.
        """
        user_prompt = f"Here is the content from {website.title}. Please summarize the main news stories:\n\n"
        user_prompt += website.text
        user_prompt += "\n\nIMPORTANT: Provide ONLY a JSON array of story summaries. Do not include any thinking process, analysis, or explanations."
        return user_prompt

    def messages_for(website):
        """
        Generate the messages for the LLM API call.
        
        Args:
            website (Website): The Website object to analyze.
            
        Returns:
            dict: The formatted messages for the API call.
        """
        return {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt_for(website)}
            ],
            "options": {
                "temperature": 0.1  # Lower temperature for more deterministic output
            }
        }

    def summarize(url):
        """
        Summarize the content from a given URL.
        
        Args:
            url (str): The URL to summarize.
            
        Returns:
            str: A JSON string containing the summaries.
        """
        try:
            website = Website(url)
            response = ollama.chat(**messages_for(website))
            content = response['message']['content']
            
            # Clean up the JSON response
            try:
                # Remove any non-JSON text before or after the JSON array
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx]
                    # Parse and re-stringify to ensure valid JSON
                    stories = json.loads(json_str)
                    # Remove duplicates based on title
                    seen_titles = set()
                    unique_stories = []
                    for story in stories:
                        if story['title'] not in seen_titles:
                            seen_titles.add(story['title'])
                            unique_stories.append(story)
                    return json.dumps(unique_stories, indent=2)
                else:
                    return "[]"  # Return empty array if no valid JSON found
            except json.JSONDecodeError:
                print(f"Warning: Invalid JSON response from model for {url}")
                return "[]"
        except Exception as e:
            print(f"Error processing {url}: {e}")
            return "[]"

    # List of news sites to summarize
    news_sites = [
        "https://www.alternet.org",
        "https://drudgereport.com",
        "https://apnews.com"
    ]

    # After summarizing all sites, collect summaries and evaluate bias
    summaries = []
    for site in news_sites:
        try:
            summary = summarize(site)
            if summary != "[]":  # Only add non-empty summaries
                summaries.append(f"Summary for {site}:\n{summary}")
        except Exception as e:
            print(f"Error summarizing {site}: {e}")

    # Get bias analysis
    if summaries:
        bias_analysis_prompt = """Please analyze the following news summaries and provide a detailed comparison of their political bias. Focus on:

1. Story Selection: What types of stories are covered or emphasized?
2. Language and Tone: How are stories presented? Look for loaded words or emotional language.
3. Source Attribution: How are sources and quotes used?
4. Story Framing: How are issues and events contextualized?
5. Overall Bias Assessment: Provide a balanced analysis of any apparent political leanings.

Here are the summaries to analyze:

"""
        bias_analysis_prompt += "\n".join(summaries)
        bias_response = ollama.chat(
            model=MODEL,
            messages=[
                {"role": "system", "content": """You are an expert media analyst specializing in political bias detection. Your task is to provide an objective, evidence-based analysis of news coverage.

CRITICAL INSTRUCTIONS:
- Provide ONLY the analysis of political bias
- DO NOT include any thinking process or internal monologue
- DO NOT use <think> tags or any other markers
- DO NOT explain your reasoning or approach
- Focus on concrete examples from the content
- Start directly with the analysis"""},
                {"role": "user", "content": bias_analysis_prompt}
            ],
            options={
                "temperature": 0.1  # Lower temperature for more deterministic output
            }
        )
        return bias_response['message']['content']
    else:
        return "No valid summaries were collected. Please check the website URLs and try again."

def main():
    """
    Main function to run the Streamlit application.
    """
    st.set_page_config(
        page_title="Media Bias Analysis",
        page_icon="📰",
        layout="wide"
    )
    
    st.title("📰 Media Bias Analysis")
    st.markdown("""
    This tool analyzes news coverage from different sources to identify potential political bias.
    The analysis focuses on story selection, language, source attribution, and framing. This analysis focuses
    specificaly on AP News, Drudge Report, and Alternet.
    """)
    
    if st.button("Run Analysis"):
        with st.spinner("Analyzing news sources..."):
            analysis = get_bias_analysis()
            st.markdown(analysis)

if __name__ == "__main__":
    main()
    