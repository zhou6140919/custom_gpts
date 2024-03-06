FROM python:3.11-slim

WORKDIR /custom_gpts

RUN apt-get update && apt-get install -y \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

COPY . $WORKDIR

RUN rm -rf ./data/*

RUN pip3 install -r requirements.txt

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "index.py", "--server.port=8501", "--server.address=0.0.0.0"]
