# Media Bias Analysis Tool

A Python-based tool that analyzes news coverage from different sources to identify potential political bias. The tool uses web scraping and AI to analyze content from AP News, Drudge Report, and Alternet, providing insights into story selection, language, source attribution, and framing.

## Features

- Web scraping of news websites using Selenium and BeautifulSoup
- Content analysis using the Gemma 3 4B language model via Ollama
- Interactive web interface built with Streamlit
- JSON-formatted output of news summaries
- Detailed bias analysis across multiple dimensions
- Support for multiple news sources

## Prerequisites

- Python 3.9 or higher
- Chrome browser installed (for Selenium)
- Ollama installed and running locally

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/media-bias-analyzer.git
cd media-bias-analyzer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Install Ollama and pull the required model:
```bash
# Install Ollama from https://ollama.ai
ollama pull gemma3:4b
```

## Usage

1. Start the Streamlit app:
```bash
streamlit run main.py
```

2. Open your web browser and navigate to the URL shown in the terminal (typically http://localhost:8501)

3. Click the "Run Analysis" button to start the analysis

## How It Works

1. **Web Scraping**: The tool uses Selenium and BeautifulSoup to extract content from news websites
2. **Content Processing**: Newspaper3k is used to clean and structure the extracted content
3. **AI Analysis**: The Gemma 3 4B model analyzes the content for political bias
4. **Results Display**: Results are presented in a clean, markdown-formatted interface

## Project Structure

```
media-bias-analyzer/
├── main.py              # Main application file
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Ollama](https://ollama.ai) for providing the AI model
- [Streamlit](https://streamlit.io) for the web interface
- [Newspaper3k](https://github.com/codelucas/newspaper) for content extraction
- [Selenium](https://www.selenium.dev) for web scraping
