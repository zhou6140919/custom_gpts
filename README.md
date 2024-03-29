# Custom GPTs

This is an open source and simple framework based on `Streamlit` to get access to LLMs like GPT-4, GPT-3.5, Claude-3.

## Installation

```bash
git clone https://github.com/zhou6140919/custom_gpts.git
cd custom_gpts
```

Change the `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in the `.env` file.

### Docker
```bash
docker compose up
```
### Conda
```bash
conda create -n custom_gpts python=3.11
conda activate custom_gpts
pip install -r requirements.txt
streamlit run index.py
```

Navigate to [http://localhost:8501](http://localhost:8501) to see the app.

## Features

### Models
- [x] GPT-4
- [x] GPT-3.5
- [x] Claude-3
- [ ] Gemini

### Tools
- [x] Retriever
- [x] Web Search
- [x] Arxiv
- [x] Chat with Videos

### Convenience
- [x] Load & Save Chat History
- [x] Upload Files


## Updates

- 2024-03-11: Add 'Google Search'; Add 'default model' and 'search engine'
- 2024-03-08: Add 'Upload Files' and 'Retriever'; Add 'Chat with Videos'
- 2024-03-06: Add Web Search based on DuckDuckGo; Add Arxiv Search
- 2024-03-05: Add GPT-4, GPT-3.5, Claude-3; Add Load & Save Chat History
