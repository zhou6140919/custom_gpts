from typing import List, Dict

from streamlit.delta_generator import DeltaGenerator

from conversation import converse


async def run_conversation(messages: List[Dict[str, str]]=[], model: str=None, message_placeholder: DeltaGenerator=None) -> List[Dict[str, str]]:
    full_response = ""
    message_placeholder.markdown(f"Thinking by {model}...")
    chunks = converse(messages, model)
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


async def conversation_starter(system_prompt: str="You are a helpful assistant", model: str=None, message_placeholder: DeltaGenerator=None) -> List[Dict[str, str]]:
    system_prompt = {"role": "system", "content": system_prompt}
    messages = await run_conversation(system_prompt, model, message_placeholder)
    return messages
    
