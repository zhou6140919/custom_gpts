import os
import json
import datetime

from openai import OpenAI, OpenAIError
from anthropic import Anthropic
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import streamlit as st
import arxiv
from googlesearch import search as google_search

# results = DDGS().text("python programming", max_results=2)

class ActionHandler:
    def __init__(self, model, max_results=5, engine="duckduckgo"):
        self.ddgs = DDGS()
        self.model = model
        self.max_results = max_results
        self.engine = engine
        if 'gpt' in self.model:
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
        elif "claude" in self.model:
            self.client = Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        else:
            raise ValueError(f"{self.model} is not supported currently.")
        self.arxiv = arxiv.Client()
    
    def action(self, messages):
        system_prompt = f"""
You are an expert who can judge what to do next after reading the conversation records. There are a total of 3 predefined actions, which are web search, academic search, and no action. The following are examples, where what follows 'Output: ' is what you should output.:

1. Web Search: It is necessary to retrieve external relevant information from the web (usually decided by the question's timing compared to the given date and complexity), and generate an appropriate search query by reading the conversation record. Make sure to output starting with 'Search: ' and then the query you want to search for.
	Example1 System: Current date is 2024-03-06
	User: Can you show me some detailed information about the recent news of former Prime Minister of Canada Brian Mulroney?
	Output: Search: 2024 former Prime Minister of Canada Brian Mulroney
	---
	Example2 System: Current date is 2024-03-06
	User: Have you heard about the movie Oppenheimer?
	Assistant: According to the web information, Oppenheimer is a 2023 epic biographical thriller film[a] written, directed, and produced by Christopher Nolan,[9] starring Cillian Murphy as J. Robert Oppenheimer, the American theoretical physicist credited with being the "father of the atomic bomb" for his role in the Manhattan Project—the World War II undertaking that developed the first nuclear weapons. Based on the 2005 biography American Prometheus by Kai Bird and Martin J. Sherwin, the film chronicles the career of J. Robert Oppenheimer, with the story predominantly focusing on his studies, his direction of the Los Alamos Laboratory during World War II, and his eventual fall from grace due to his 1954 security hearing. The film also stars Emily Blunt as Oppenheimer's wife "Kitty", Matt Damon as head of the Manhattan Project Leslie Groves, Robert Downey Jr. as United States Atomic Energy Commission member Lewis Strauss, and Florence Pugh as Oppenheimer's communist lover Jean Tatlock. The ensemble supporting cast includes Josh Hartnett, Casey Affleck, Rami Malek, and Kenneth Branagh.
	User: Okay, can you help me find some comments on the Internet?
	Output: Search: Oppenheimer movie comments
2. Academic Search: It is necessary to search for papers or academic-related information from the arxiv website (usually the user will directly ask for the paper title, author, or technique, etc.), and generate an appropriate search query that only contains key information in user's questions by reading the conversation record and prepend 'Arxiv: '.
    Example1
    System: Current date is 2024-03-06
    User: Can you summarize the paper "SELF-RAG: LEARNING TO RETRIEVE, GENERATE, AND CRITIQUE THROUGH SELF-REFLECTION"?
    Output: Arxiv: SELF-RAG: LEARNING TO RETRIEVE, GENERATE, AND CRITIQUE THROUGH SELF-REFLECTION
	---
	Example2
	System: Current date is 2024-03-06
	User: Show me the papers written by Kaiming He.
	Output: Arxiv: Kaiming He
3. No Action: No external knowledge is required at all, and AI can answer the question using its already acquired knowledge. You only need to ONLY output "No Action", do not add any other content on your own.
	Example
	System: Current date is 2024-03-06
	User: Write a short story in third person narration about a protagonist who has to make an important career decision.
	Output: No Action
	---
	Example2
	System: Current date is 2024-03-06
    User: Describe a time when you had to make a difficult decision.
	Output: No Action
        """
        reform_messages = []
        for message in messages:
            if message["role"] == "user":
                reform_messages.append("User: "+message["content"])
            elif message["role"] == "assistant":
                reform_messages.append("Assistant: "+message["content"])
        last_question = reform_messages[-1][6:]
        reform_messages = f"System: Current date is {datetime.date.today().strftime('%Y-%m-%d')}\n" + "\n".join(reform_messages) + "\n" + "Output: "
        with st.status(label="Thinking...", expanded=False) as status:
            if os.getenv("OPENAI_API_KEY"):
                response = self.client.chat.completions.create(
                    model="gpt-4-1106-preview",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": reform_messages},
                    ],
                    max_tokens=100,
                ).choices[0].message.content
            # if 'gpt' in self.model:
            #     response = self.client.chat.completions.create(
            #         model=self.model,
            #         messages=[
            #             {"role": "system", "content": system_prompt},
            #             {"role": "user", "content": reform_messages},
            #         ],
            #         max_tokens=2000,
            #     ).choices[0].message.content
            # elif "claude" in self.model:
            #     response = self.client.messages.create(
            #         model=self.model,
            #         system=system_prompt,
            #         messages=[
            #             {"role": "user", "content": reform_messages},
            #         ],
            #         max_tokens=2000,
            #     ).content[0].text
            #     print(response)
            else:
                raise ValueError(f"{self.model} is not supported currently.")
            if response.startswith("Search: "):
                status.update(label=response)
                query = response[8:]
                new_prompt = f"""
                The question input by the user is: "{last_question}"
                Based on your judgment, the following information has been found on the Internet using the query {query}. Please consider this information as your own knowledge to form an accurate answer.
                {json.dumps(self.search(query, self.engine), ensure_ascii=False, indent=4)}
                """
                st.write(new_prompt)
                return new_prompt, response
            elif response.startswith("Arxiv: "):
                status.update(label=response)
                query = response[7:]
                r = list(self.arxiv.results(arxiv.Search(query=query, max_results=self.max_results, sort_by=arxiv.SortCriterion.Relevance)))
                retrieved = [{"Title": result.title, "Authors": ", ".join([author.name for author in result.authors]), "Summary": result.summary} for result in r]
                new_prompt = f"""
                The question input by the user is: "{last_question}"
                Based on your judgment, the following information has been found on the Internet. Please consider this information as your own knowledge to form an accurate answer.
                {json.dumps(retrieved, ensure_ascii=False, indent=4)}
                """
                st.write(new_prompt)
                return new_prompt, response
            elif response.startswith("No Action"):
                return last_question, ""
            else:
                return last_question, ""
        

    def search(self, query, engine="duckduckgo"):
        if engine == "duckduckgo":
            result_dict = self.ddgs.text(query, max_results=self.max_results)
            # scrape the hrefs and return them
            hrefs = [result["href"] for result in result_dict]
            titles = [result["title"] for result in result_dict]
        elif engine == "google":
            results = google_search(query, num=self.max_results, advanced=True)
            hrefs = [result.url for result in results]
            titles = [result.title for result in results]
        else:
            raise ValueError(f"{engine} is not supported currently.")
        all_results = []
        for href, title in zip(hrefs, titles):
            response = requests.get(href)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                paragraphs = soup.find_all('p')
                text = " ".join([p.get_text(strip=True) for p in paragraphs])[:3000]
                all_results.append({"title": title, "text": text})
            else:
                print(f"Failed to retrieve {href} from web")
        return all_results
