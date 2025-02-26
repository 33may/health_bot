import re
from typing import List

import json
import os
import requests
from dotenv import load_dotenv
from loguru import logger

from application.backend.Models.TokenObject import TokenObject
from application.backend.database.database_functions import retrieve_similar_documents



def interact_model(context, system_prompt, chat_model = True):
    """
    Отправляет контекст разговора на OpenRouter API с параметром stream=True
    и генерирует (yield) полученные токены по мере их поступления.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"

    load_dotenv()
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    context.insert(0, system_prompt)

    model = "google/gemini-2.0-flash-thinking-exp:free" if chat_model else "deepseek/deepseek-r1"

    payload = {
        "model": model,
        "messages": context,
        "include_reasoning": False if chat_model else True,
        "stream": True,
        'provider': {
            'sort': 'throughput'
        }
    }

    logger.debug(f"Отправка запроса к OpenRouter: {json.dumps(payload, ensure_ascii=False, indent=2)}")

    response = requests.post(url, headers=headers, json=payload, stream=True)
    response.encoding = 'utf-8'

    if chat_model:
        return process_chat_response(response)
    else:
        return process_reason_response(response)


def process_chat_response(response):
    buffer = ""
    complete_response = ""

    rag_flag = None

    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        buffer += chunk
        while True:
            line_end = buffer.find('\n')
            if line_end == -1:
                break
            line = buffer[:line_end].strip()
            buffer = buffer[line_end + 1:]

            if line.startswith('data: '):
                data = line[6:]
                if data == '[DONE]':
                    logger.debug(f"Response Type: {"RAG" if rag_flag else "Chat Response"}")
                    logger.debug(f"Полный ответ от OpenRouter:\n{complete_response}")

                    if "RAG" in complete_response:
                        rag_flag = True
                        match = re.search(r"\[RAG\] \{(.*?)\}", complete_response)
                        complete_response = match.group(0) if match else complete_response

                    yield TokenObject(type="rag", content=complete_response) if rag_flag else TokenObject(type="done",
                                                                                                          content=complete_response)

                try:
                    data_obj = json.loads(data)
                    token = data_obj["choices"][0]["delta"].get("content")
                    # check first  chunk to determine if it is chat response or RAG
                    if rag_flag is None:
                        rag_flag = True if "[RAG]" in token else False
                    if token:
                        complete_response += token
                        if not rag_flag:
                            yield TokenObject(type="message", content=token)
                except json.JSONDecodeError:
                    continue


def process_reason_response(response):
    buffer = ""
    complete_thinking = ""
    complete_message = ""

    for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
        buffer += chunk
        while True:
            line_end = buffer.find('\n')
            if line_end == -1:
                break
            line = buffer[:line_end].strip()
            buffer = buffer[line_end + 1:]

            if line.startswith('data: '):
                data = line[6:]
                if data == '[DONE]':
                    logger.debug(f"Полный ответ от OpenRouter:\n{complete_thinking + complete_message}")
                    if "[RAG}" in complete_message:
                        yield TokenObject(type="rag", content=complete_message)
                    yield TokenObject(type="done", content=complete_thinking + complete_message)

                try:
                    data_obj = json.loads(data)
                    token_type = "message" if data_obj["choices"][0]["delta"].get("content") else "think" if data_obj["choices"][0]["delta"].get("reasoning") else None
                    token = data_obj["choices"][0]["delta"].get("content") if token_type == "message" else data_obj["choices"][0]["delta"].get("reasoning") if token_type == "think" else None
                    if token and token_type:
                        if token_type == "message":
                            complete_message += token
                        elif token_type == "think":
                            complete_thinking += token

                        yield TokenObject(type="think", content=token)
                except json.JSONDecodeError:
                    continue


def get_chat_system_message():
    return {
        "role": "system",
        "content": (
            "You are a medical researcher performing systematic differential diagnosis analysis. "
            "Use masculine gender for self-reference when needed but avoid emphasizing gender/personality. "
            "**Respond exclusively in Ukrainian** using natural conversational language with Markdown, make the conversation natural chat with emphatic behavior, if greeting is already present in your previous responses, dont repeat it. .\n\n"

            "### **STRICT RULES FOR RAG USAGE:**\n"
            "1. **RAG queries must be separate**\n"
            "   - If additional lookup is required, respond **ONLY** with `[RAG] {query}` and NOTHING else.\n"
            "   - **DO NOT** mix `[RAG]` with explanations, summaries, or any other text.\n"
            "   - **If generating a normal response, DO NOT include `[RAG]` at all.**\n\n"

            "2. **Response Depth & Adaptability:**\n"
            "   - Simple cases (1-2 clear symptoms): Provide concise recommendations (2-3 key points).\n"
            "   - Complex cases (ambiguous/multiple symptoms): Ask clarifying questions before suggesting conclusions.\n\n"

            "3. **Safety Guidelines:**\n"
            "   - Never provide definitive diagnoses.\n"
            "   - Always advise the user to consult a doctor for proper evaluation.\n\n"

            "4. **Response Formatting:**\n"
            "   - Use different headers (##, ###) to separate logical parts of response and make it readable\n"
            "   - Use **bold** for medical terms (e.g., **мігрень**)\n"
            "   - Maintain gender-neutral 'ви' address\n\n"

            "Failure to follow these rules will cause system errors."
        )
    }



def get_reason_system_message():
    return {
        "role": "system",
        "content": (
            "You are a medical data analyst responsible for processing patient information and generating structured assessments. "
            "Your task is to analyze available data systematically, incorporating retrieved medical documents where applicable, "
            "to prepare a comprehensive final report.\n\n"

            "### **STRICT RULES FOR RAG USAGE:**\n"
            "1. **RAG queries must be SEPARATE:**\n"
            "   - If additional information is required, respond with **ONLY** `[RAG] {query}` and NOTHING else.\n"
            "   - **DO NOT** mix `[RAG]` queries with explanations, summaries, or any other text.\n"
            "   - **If generating a normal analysis, DO NOT include `[RAG]` at all.**\n\n"

            "2. **Analysis Protocol:**\n"
            "   - Process and interpret patient symptoms and context.\n"
            "   - Reference **retrieved medical documents** directly, linking relevant findings.\n"
            "   - If 3-5 key data points are sufficient, proceed to conclusions.\n"
            "   - Format the response in **Markdown** with clear sections.\n\n"

            "3. **Language Requirements:**\n"
            "   - **ALL** analysis must be in English.\n"
            "   - Maintain a natural and conversational tone.\n\n"

            "4. **Final Summary Format:**\n"
            "   - **Structured Patient Case Summary:**\n"
            "     * **Known Patient Symptoms** (based on available data).\n"
            "     * **Possible Diagnostic Considerations** (without definitive diagnosis).\n"
            "     * **Key Follow-Up Questions** (to refine potential causes) IMPORTANT the additional questions hould only be added if the reasoning process identifies there is not enough information to help with diagnosis..\n\n"

            "5. **If more data is needed:**\n"
            "   - Respond **ONLY** with `[RAG] {query}` without any additional text.\n\n"

            "### **Example of a Structured Final Analysis:**\n"
            "```\n"
            "## Symptom Assessment\n"
            "- **Primary Symptoms:** [List of reported symptoms]\n"
            "- **Onset & Progression:** [Description of symptom development]\n"
            "- **Relevant Context:** [Stress, medications, lifestyle factors]\n"
            "\n"
            "## Potential Causes\n"
            "- **Possibility 1:** [Explanation]\n"
            "- **Possibility 2:** [Explanation]\n"
            "\n"
            "## Key Follow-Up Questions\n"
            "- Has the patient experienced [symptom X] before?\n"
            "- Are there any changes in [factor Y]?\n"
            "\n"
            "## Recommended Next Steps\n"
            "- **Consultation with a physician** is advised.\n"
            "- **Warning signs requiring immediate attention:** [List of critical symptoms]\n"
            "```\n\n"
            
            "IMPORTANT ALWAYS REASON IN UKRAINIAN"
            
            "### **Example of a Structured Final RAG request:**\n"
            "[RAG] Patient reports persistent headache with visual disturbances. Retrieve relevant medical literature on migraine differentials and potential neurological causes."
            "Very important to always reason in Ukrainian to ensure the reasoning is interpretable for Ukrainian users"
            "**Your goal is to critically evaluate data and generate a well-structured medical report.** "
            "If additional data is required, respond **ONLY** with `[RAG] {query}` and nothing else."
        )
    }


def get_final_chat_system_message():
    return {
        "role": "system",
        "content": (
            "You are a medical chat assistant responsible for delivering the final patient-facing response "
            "based on the analysis provided by the reasoning model. Your job is to ensure that the patient receives "
            "a clear, structured, and actionable response in Ukrainian.\n\n"

            "### **Key Responsibilities:**\n"
            "1. **Processing Analyst’s Input:**\n"
            "   - You **DO NOT** generate or process `[RAG]` queries.\n"
            "   - If the analyst provides a detailed reasoning output, you must **convert it into a patient-friendly response** in natural, conversational Ukrainian.\n"
            "   - Ensure that all provided medical details are **explained in simple terms**, avoiding unexplained medical jargon.\n\n"

            "2. **Ensuring Clarity and Guidance:**\n"
            "   - Organize the response into **logical sections** (e.g., summary of symptoms, possible explanations, recommendations).\n"
            "   - If the analyst includes **open questions or areas of uncertainty**, guide the patient with specific clarifying questions.\n"
            "   - If the case is conclusive, provide **clear next steps** (e.g., home care measures, urgency of visiting a doctor, signs to monitor).\n\n"

            "3. **Maintaining Medical Safety Standards:**\n"
            "   - **ALWAYS** remind the patient that your response is for informational purposes only and does not replace a consultation with a healthcare professional.\n"
            "   - If symptoms are severe or suggest an emergency, strongly **recommend seeking immediate medical attention**.\n\n"

            "4. **Response Formatting Guidelines:**\n"
            "   - Use different headers (##, ###) to separate logical parts of response and make it readable\n"
            "   - Respond **exclusively in Ukrainian**.\n"
            "   - Use **Markdown formatting** for readability:\n"
            "     * **Bold** for key terms (e.g., **мігрень**, **температура**).\n"
            "     * *Italic* for examples (e.g., *парацетамол*).\n"
            "     * Lists to structure recommendations.\n"
            "     * `---` to separate sections in longer messages.\n"
            "   - Keep the response natural and conversational, without excessive formality.\n\n"

            "**Your role is to ensure the patient receives a well-structured, clear, and safe response based on the analyst’s reasoning, while maintaining professional medical communication standards.**"
        )
    }




async def chat(chat_history: List[dict]):
    chat_chunks = interact_model(chat_history, get_chat_system_message(), chat_model=True)
    for token in response_loop(chat_chunks, chat_history):
        yield token


def response_loop(chunk_generator, chat_history: List[dict]):
    # Process each token in the generator asynchronously
    for token in chunk_generator:
        if token.type in ("message", "think"):
            # Yield direct response tokens immediately
            yield token
        elif token.type == "rag":
            logger.debug(f"Starting RAG processing for: {token.content}")

            complete_reasoning = ""

            # Process RAG sequence
            for reason_token in rag_logic(token.content, chat_history.copy()):
                if reason_token.type in ("think", "sup_docs"):
                    yield reason_token
                elif reason_token.type == "done":
                    complete_reasoning = reason_token.content
                    logger.debug("Reasoning ended", complete_reasoning)

            chat_history.append({
                "role": "system",
                "content": complete_reasoning
            })

            # Generate final answer after RAG processing
            final_chunks = interact_model(chat_history, get_final_chat_system_message(), chat_model=True)
            for final_token in response_loop(final_chunks, chat_history):
                yield final_token

def rag_logic(rag_query, chat_history: List[object]):

    retrieved_documents = retrieve_docs(rag_query)

    doc_ids = [str(doc["name"]) for doc in retrieved_documents]

    yield TokenObject(type="sup_docs", content=json.dumps(doc_ids))

    add_documents_to_chat_history(retrieved_documents, chat_history)

    logger.debug(f"Chat history: {chat_history}")

    reason_response = interact_model(chat_history, get_reason_system_message(), chat_model=False)

    complete_reasoning = "<think>"

    for token in reason_response:
        complete_reasoning += token.content
        if token.type == "think":
            yield token
        elif token.type == "rag":

            chat_history.append({
                "role": "system",
                "content": complete_reasoning
            })

            additional_rag_query = token.content
            additional_documents = retrieve_docs(additional_rag_query)

            existing_doc_names = {doc["name"] for doc in retrieved_documents}

            use_documents = [doc for doc in additional_documents if doc["name"] not in existing_doc_names]

            add_documents_to_chat_history(use_documents, chat_history)

            additional_reason_response = interact_model(chat_history, get_reason_system_message(), chat_model=False)

            for additional_token in additional_reason_response:
                if additional_token.type == "think":
                    yield additional_token

    complete_reasoning += "</think>"

    yield TokenObject(type="done", content=complete_reasoning)


def add_documents_to_chat_history(documents: List[dict], chat_history: List[object]):
    document_context = [f"Document Name: {document["name"]} \n Document Content: {document["content"]}" for document in documents]

    supporting_documents = "Supporting Documents:\n" + "\n\n".join(document_context)

    chat_history.append({"role": "system", "content": supporting_documents})


def retrieve_docs(rag_query) -> List[dict]:
    rag_query = rag_query[5:]

    return retrieve_similar_documents(rag_query)


