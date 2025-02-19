import json
from typing import List

import requests
import os
from dotenv import load_dotenv

import json
import os
import requests
from dotenv import load_dotenv
from loguru import logger

from application.backend.Models.TokenObject import TokenObject
from application.backend.database.database_functions import retrieve_similar_documents
from application.backend.database.tables import Documents
from application.backend.logic.embeddings.model import compute_embedding


def interact_model(context, chat_model = True, stream=True):
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

    context.insert(0, get_chat_system_message() if chat_model else get_reason_system_message())

    model = "google/gemini-2.0-flash-thinking-exp:free" if chat_model else "deepseek/deepseek-r1:free"

    payload = {
        "model": model,
        "messages": context,
        "include_reasoning": True,
        "stream": True
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


def get_chat_system_message():
    return {
        "role": "system",
        "content": (
            "You are a medical research assistant that thinks through differential diagnosis systematically. refer to you like male but not focus on it, just in case "
            "**Respond exclusively in Ukrainian** using natural, conversational human kike language with light Markdown formatting.\n\n"
            
            "always refer to user with gender neutral and respect in Ukrainian use ви"

            "### Core Principles:\n"
            "1. **Adaptive Depth**\n"
            "   - For simple queries (1-2 clear symptoms): Provide concise guidance with 2-3 actionable recommendations\n"
            "   - For complex cases (ambiguous/multiple symptoms): Initiate investigative dialogue through thoughtful questioning\n\n"

            "2. **Research Methodology**\n"
            "   - Ask questions to clarify:\n"
            "     a) Symptom characteristics (timing, triggers, severity)\n"
            "     b) Relevant medical history\n"
            "     c) Contextual factors\n"
            "   - Continue until 3-5 key data points are established\n"
            
            "3. Explore Database, when you get ENOUGH, this means you already asked some questions and user provided information and details about case context instead of complete response with defined structure, you need to give the query to the database"
            "- Firstly when we start this message, the whole response should start from [RAG], only when we already got information needed to make decisions. In the [RAG] response NOTHING except [RAG] {rag query} should be present In the "
            r"rag query you need to make a detailed summary of all the information gathered from user, but keep it short. After the response immediately after finishing RAG query, nothing else should be in RAG response. "
            
            "3. **Communication Style**\n"
            "   - Use natural phrasing between markdown elements\n"
            "   - Avoid medical jargon without explanation\n"
            "   - Never state definitive diagnoses\n"
            "   - Always include safety disclaimer\n\n"

            "4. **Formatting Guidelines**\n"
            "   - Bold for medical terms (**грип**)\n"
            "   - Italics for examples (*парацетамол*)\n"
            "   - Lists for recommendations\n"
            "   - Horizontal rules between conversation turns\n"

            "Additionally, **format your responses in complete Markdown**. Use headings (e.g., `##`, `###`), bold (`**text**`) and italic (`*text*`) formatting, lists (using '-' or '1.'), horizontal rules (`---`), and preserve line breaks and spacing so that the final response is displayed correctly in Markdown. Your answer should be entirely formatted in Markdown, following these guidelines.\n\n"

            "Here is one-shot example of markdown formating"
            "## Header"
            "some text with **bold** items"
            "### List name:"
            "- item1"
            "- iem2"
            "- item3"

            "### Second list name:"
            "1. item1"
            "2. iem2"
            "3. item3"

            "Structure each new line with own header to increase readability"

            "Remember, your advice is general and cannot replace a visit to a doctor. Follow these rules to optimize resource usage and produce high-quality, fully Markdown-formatted answers."

        )
    }



def get_reason_system_message():
    return {
        "role": "system",
        "content": (
            "reasoner model prompt"
        )
    }


# def get_system_message():
#     return {
#         "role": "system",
#         "content": (
#             "You are an experienced healthcare specialist. Your responses must be provided exclusively in Ukrainian, "
#             "in a natural, detailed, and friendly manner. Do not answer with mere lists or short bullet points; instead, provide comprehensive explanations with examples and recommendations. If the user asks questions about symptoms or health conditions, be sure to emphasize that your advice is general and does not replace consultation with a doctor. Strive to produce concise yet complete answers that capture all important details without unnecessary length.\n\n"
#
#             "When processing a user's query, follow these guidelines:\n"
#             "– If the query is simple—containing a limited number of symptoms or not requiring in-depth analysis—generate a final answer in a natural, human-like manner using complete Markdown formatting.\n"
#             "– If the query is complex—containing many details, multiple symptoms, or requiring an in-depth analysis of possible pathologies—do not generate a final human-like answer. Instead, produce a concise summary prompt that aggregates all relevant details from the entire conversation into a single query. This summary prompt must begin with the marker [RAG] and include only the essential details required for document retrieval, without any extra commentary.\n\n"
#
#             "Additionally, **format your responses in complete Markdown**. Use headings (e.g., `##`, `###`), bold (`**text**`) and italic (`*text*`) formatting, lists (using '-' or '1.'), horizontal rules (`---`), and preserve line breaks and spacing so that the final response is displayed correctly in Markdown. Your answer should be entirely formatted in Markdown, following these guidelines.\n\n"
#
#             "Here is one-shot example of markdown formating"
#             "## Header"
#             "some text with **bold** items"
#             "### List name:"
#             "- item1"
#             "- iem2"
#             "- item3"
#
#             "### Second list name:"
#             "1. item1"
#             "2. iem2"
#             "3. item3"
#
#             "Structure each new line with own header to increase readability"
#
#             "Remember, your advice is general and cannot replace a visit to a doctor. Follow these rules to optimize resource usage and produce high-quality, fully Markdown-formatted answers."
#         )
#     }


async def chat(chat_history: List[object]):
    for token in interact_model(chat_history, stream=True):
        if token.type == "message":
            yield token
        elif token.type == "reason":
            logger.debug(f"return reason \n{token.content}")
            yield token
        elif token.type == "rag":
            logger.debug(f"do rag logic \n{token.content}")

            async for reason_token in rag_logic(token.content, chat_history):
                yield reason_token
        elif token.type == "done":
            logger.debug(f"Execution finished successfully \n{token.content}")

test_rag_query = "[RAG] High temperature, headaches, more then 39"

async def rag_logic(rag_query, chat_history: List[object]):

    retrieved_documents = await retrieve_docs(rag_query)

    document_context = [f"Document Name: {document.name} \n Document Content: {document.content}" for document in retrieved_documents]

    supporting_documents = "Supporting Documents:\n" + "\n\n".join(document_context)

    chat_history.append({"role": "system", "content": supporting_documents})

    logger.debug(f"Chat history: {chat_history}")

    for token in interact_model(chat_history, chat_model=False, stream=True):
        if token.type == "message":
            yield token



async def retrieve_docs(rag_query) -> List[Documents]:
    rag_query = rag_query[5:]

    return await retrieve_similar_documents(rag_query)






def reasoning_model(prompt):
    """
    Функция модели рассуждения.
    Принимает промпт с запросом и документами, возвращает вывод/рассуждение.
    """
    # Здесь должна быть логика обработки промпта и генерации рассуждения.
    # Для примера возвращаем строку с результатом рассуждения.
    return "[Рассуждение с извлечёнными документами]"



