from typing import List, Dict

from streamlit.delta_generator import DeltaGenerator
import streamlit as st

from conversation import converse


async def run_conversation(messages: List[Dict[str, str]]=[], model: str=None, message_placeholder: DeltaGenerator=None, new_prompt: str=None, max_tokens: int=2048) -> List[Dict[str, str]]:
    full_response = ""
    message_placeholder.markdown(f"Thinking by {model}...")
    if new_prompt:
        new_messages = messages[:-1] + [{"role": "user", "content": new_prompt}]
    else:
        new_messages = messages
    chunks = converse(new_messages, model, max_tokens)
    chunk = await anext(chunks, "END OF CHAT")
    while chunk != "END OF CHAT":
        #print(f"Received chunk from LLM service: {chunk}")
        if chunk.startswith("EXCEPTION"):
            full_response = ":red[We are having trouble generating advice.  Please wait a minute and try again.]"
            break
        full_response = full_response + chunk
        message_placeholder.markdown(full_response + "▌")
        chunk = await anext(chunks, "END OF CHAT")
    message_placeholder.markdown(full_response)
    messages.append({"role": "assistant", "content": full_response})
    return messages
