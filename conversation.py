import os
import traceback
from typing import AsyncGenerator, List, Dict

from openai import OpenAI, AsyncOpenAI, OpenAIError
from anthropic import Anthropic
from dotenv import load_dotenv


load_dotenv()


async def converse(messages: List[Dict[str, str]]=[], model: str=None, max_tokens: int=2048) -> AsyncGenerator[str, None]:
    """
    Given a conversation history, generate an iterative response of strings from the OpenAI or Anthropic API.

    :param messages: a conversation history with the following format:
    `[ { "role": "user", "content": "Hello, how are you?" },
       { "role": "assistant", "content": "I am doing well, how can I help you today?" } ]`

    :return: a generator of delta string responses
    """

    # openai_client = OpenAI(
    #     api_key=os.getenv("OPENAI_API_KEY")
    # )

    openai_client = AsyncOpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    anthropic_client = Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    if "claude" in model:
        client = anthropic_client
        try:
            if len([m for m in messages if m["role"] == "system"]) > 0:
                system_prompt = ' '.join([m["content"] for m in messages if m["role"] == "system"])
            with client.messages.stream(
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[m for m in messages if m["role"] != "system"],
                model=model,
            ) as stream:
                for text in stream.text_stream:
                    if text:
                        yield text
        except Exception as e:
            traceback.print_exc()
            yield f"EXCEPTION {str(e)}"
            

    elif "gpt" in model:
        client = openai_client
        try:
            async for chunk in await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                stream=True
            ):
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        except OpenAIError as e:
            traceback.print_exc()
            yield f"oaiEXCEPTION {str(e)}"
        except Exception as e:
            yield f"EXCEPTION {str(e)}"
    else:
        raise ValueError(f"{model} is not supported currently.")
