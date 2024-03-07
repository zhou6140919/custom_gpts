# Custom GPTs

This is an open source and simple framework based on `Streamlit` to get access to LLMs like GPT-4, GPT-3.5, Claude-3.

## Installation

```bash
git clone https://github.com/zhou6140919/custom_gpts.git
cd custom_gpts
```
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
- [ ] Retriever
- [x] Web Search
- [x] Arxiv

### Convenience
- [x] Load & Save Chat History
- [ ] Upload Files


## Updates

- 2024-03-06: Add Web Search based on DuckDuckGo; Add Arxiv Search
- 2024-03-05: Add GPT-4, GPT-3.5, Claude-3; Add Load & Save Chat History
