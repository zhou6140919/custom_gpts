import os
import json

from openai import OpenAI, OpenAIError
from anthropic import Anthropic
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup

# results = DDGS().text("python programming", max_results=2)

class RetrievalHandler:
    def __init__(self, model, max_results=5, message_placeholder=None):
        self.ddgs = DDGS()
        self.model = model
        self.max_results = max_results
        self.ph = message_placeholder
        if 'gpt' in model:
            self.client = OpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
        elif "claude" in model:
            self.client = Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        else:
            raise ValueError(f"{model} is not supported currently.")

    def search(self, query):
        result_dict = self.ddgs.text(query, max_results=self.max_results)
        # scrape the hrefs and return them
        hrefs = [result["href"] for result in result_dict]
        titles = [result["title"] for result in result_dict]
        all_results = []
        for href, title in zip(hrefs, titles):
            response = requests.get(href)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                paragraphs = soup.find_all('p')
                text = " ".join([p.get_text(strip=True) for p in paragraphs])[:3000]
                all_results.append({"Title": title, "text": text})
            else:
                print(f"Failed to retrieve {href}")
        return all_results
        
    
    # TODO: refine query
    def check_and_retrieve(self, input_text):
        if self.need_retrieve(input_text):
            self.ph.markdown(f"This question is beyond my knowledge. Searching the internet for information...")
            new_prompt = f"""
            The question input by the user is: "{input_text}"
            Based on your judgment, the following information has been found on the Internet. Please combine this information to form an accurate answer.
            {json.dumps(self.search(input_text), ensure_ascii=False)}
            """
            print("New Prompt:", new_prompt)
            return new_prompt
        else:
            return input_text
            

    def need_retrieve(self, prompt) -> bool:
        example = """
        Instructions Given an instruction, please make a judgment on whether finding some external documents from the web (e.g., Wikipedia) helps to generate a better response. Please answer [Yes] or [No] and write an explanation. Demonstrations Instruction Give three tips for staying healthy.\nNeed retrieval? [Yes]\nExplanation There might be some online sources listing three tips for staying healthy or some reliable sources to explain the effects of different behaviors on health. So retrieving documents is helpful to improve the response to this query. Instruction Describe a time when you had to make a difficult decision.\nNeed retrieval? [No]\nExplanation This instruction is asking about some personal experience and thus it does not require one to find some external documents. Instruction Write a short story in third person narration about a protagonist who has to make an important career decision.\nNeed retrieval? [No]\nExplanation This instruction asks us to write a short story, which does not require external evidence to verify. Instruction What is the capital of France?\nNeed retrieval? [Yes]\nExplanation While the instruction simply asks us to answer the capital of France, which is a widely known fact, retrieving web documents for this question can still help. Instruction Find the area of a circle given its radius. Radius = 4\nNeed retrieval? [No]\nExplanation This is a math question and although we may be able to find some documents describing a formula, it is unlikely to find a document exactly mentioning the answer. Instruction Arrange the words in the given sentence to form a grammatically correct sentence. quickly the brown fox jumped\nNeed retrieval? [No]\nExplanation This task doesn’t require any external evidence, as it is a simple grammatical question. Instruction Explain the process of cellular respiration in plants.\nNeed retrieval? [Yes]\nExplanation This instruction asks for a detailed description of a scientific concept, and is highly likely that we can find a reliable and useful document to support the response.
        """
        if 'gpt' in self.model:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": example},
                    {"role": "user", "content": "Instruction " + prompt}],
                max_tokens=200,
            ).choices[0].message.content
        elif "claude" in self.model:
            response = self.client.messages.create(
                model=self.model,
                system=example,
                messages=[
                    {"role": "user", "content": "Instruction " + prompt}],
                max_tokens=200,
            ).content[0].text
        else:
            raise ValueError(f"{self.model} is not supported currently.")
        print(f"Need to Retrieve?:\n{response}")
        if "[Yes]" in response:
            return True
        elif "[No]" in response:
            return False
        else:
            return True

    def need_retrieve_prompt(self, input_text):
        return f"""The following input is from the user: "{input_text}"."""
    
        
