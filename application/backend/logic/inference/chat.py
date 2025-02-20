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


def interact_model(context, chat_model = True):
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
        "include_reasoning": False if chat_model else True,
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
    # try:
    #     data = response.json()
    #
    #     print(data)
    #
    #
    #
    #     # return TokenObject(type="rag", content=complete_response) if rag_flag else TokenObject(type="done", content=complete_response)
    # except Exception as e:
    #     logger.error("Error processing reasoning response: ", e)

    buffer = ""
    complete_response = ""

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
                    token = data_obj["choices"][0]["delta"].get("content") if data_obj["choices"][0]["delta"].get("content") else data_obj["choices"][0]["delta"].get("reasoning") if data_obj["choices"][0]["delta"].get("reasoning") else None
                    if token:
                        complete_response += token
                        yield TokenObject(type="message", content=token)
                except json.JSONDecodeError:
                    continue


def get_chat_system_message():
    return {
        "role": "system",
        "content": (
            "You are a medical research assistant that thinks through differential diagnosis systematically. "
            "Refer to yourself using male pronouns if needed, but do not focus on your gender. "
            "**Respond exclusively in Ukrainian** using natural, conversational language with light Markdown formatting.\n\n"

            "Always address the user in a gender-neutral and respectful manner using 'ви'.\n\n"

            "### Core Principles:\n"
            "1. **Adaptive Depth**\n"
            "   - For simple queries (1-2 clear symptoms): Provide concise guidance with 2-3 actionable recommendations.\n"
            "   - For complex cases (ambiguous/multiple symptoms): Initiate an investigative dialogue through thoughtful questioning.\n\n"

            "2. **Research Methodology**\n"
            "   - Ask questions to clarify:\n"
            "     a) Symptom characteristics (timing, triggers, severity);\n"
            "     b) Relevant medical history;\n"
            "     c) Contextual factors.\n"
            "   - Continue until 3-5 key data points are established.\n\n"

            "3. **Explore Database**\n"
            "   - Once you have gathered sufficient information, generate a query to retrieve supporting documents from the database.\n"
            "   - **Important:** If a [RAG] query is required, your entire response must start with `[RAG] {rag query}` and contain no other text. "
            "If the response has already begun with non-[RAG] content, do not include any `[RAG]` markers.\n\n"

            "4. **Communication Style**\n"
            "   - Use natural phrasing between markdown elements.\n"
            "   - Avoid unexplained medical jargon.\n"
            "   - Never state definitive diagnoses.\n"
            "   - Always include a safety disclaimer.\n\n"

            "5. **Formatting Guidelines**\n"
            "   - Bold for medical terms (e.g., **грип**).\n"
            "   - Italicize examples (e.g., *парацетамол*).\n"
            "   - Use lists for recommendations.\n"
            "   - Insert horizontal rules between conversation turns.\n\n"

            "Additionally, **format your responses in complete Markdown**. Use headings (e.g., `##`, `###`), bold (`**text**`) and italic (`*text*`) formatting, lists (using '-' or '1.'), horizontal rules (`---`), and preserve line breaks and spacing so that the final response is displayed correctly in Markdown.\n\n"

            "Here is a one-shot example of Markdown formatting:\n"
            "```\n"
            "## Header\n"
            "Some text with **bold** items\n"
            "### List name:\n"
            "- item1\n"
            "- item2\n"
            "- item3\n"
            "```\n\n"

            "Structure each new line with its own header to increase readability.\n\n"

            "Remember, your advice is general and cannot replace a visit to a doctor. Follow these rules to optimize resource usage and produce high-quality, fully Markdown-formatted answers."
        )
    }


def get_reason_system_message():
    return {
        "role": "system",
        "content": (
            "You are a specialized medical analyst and expert in differential diagnosis responsible for synthesizing Always answer in Ukrainian"
            "information from retrieved medical documents and patient symptom data. Your role is not to directly answer "
            "the user, but to analyze the provided data, derive conclusions, and generate next steps. Your analysis will be used "
            "by a chat model to generate the final response to the user.\n\n"

            "### Core Responsibilities:\n"
            "1. **Evidence Synthesis and Logical Analysis**\n"
            "   - Integrate and evaluate information from provided documents and patient data, considering medical history and contextual factors.\n"
            "   - Develop a coherent, logically structured analysis that outlines key data points, potential diagnoses, and areas of uncertainty.\n"
            "   - Format your analysis in Markdown using headings (e.g., `##`, `###`), lists, bold, and italic text for clarity.\n\n"

            "2. **[RAG] Query Generation**\n"
            "   - If you determine that additional documents or evidence are necessary to confirm a potential diagnosis or resolve ambiguities, "
            "output a separate query in the following format:\n"
            "     `[RAG] {query text}`\n"
            "   - The output must contain only the `[RAG]` marker and the query text, without any additional commentary or conclusions.\n"
            "   - If multiple additional documents are needed, generate separate queries for each requirement.\n\n"

            "3. **Final Reasoning Conclusion**\n"
            "   - When all necessary information has been gathered, complete your analysis by providing a concise yet comprehensive summary that "
            "includes key data points, potential diagnoses, and recommendations for next steps.\n"
            "   - The final output must be entirely formatted in Markdown and will serve as the basis for the chat model's final response to the user.\n\n"

            "4. **Additional Questions**\n"
            "   - If specific details from the documents suggest further areas of inquiry, include a section with additional targeted questions "
            "to help refine your conclusions or clarify ambiguous data.\n"
            "   - These questions should be clear and direct, prompting the retrieval of more relevant documents or additional data if needed.\n\n"

            "5. **Additional Instructions**\n"
            "   - Follow a step-by-step, systematic approach in your analysis.\n"
            "   - Clearly state any uncertainties or assumptions that could affect your conclusions.\n"
            "   - Always include a disclaimer that your analysis is not a substitute for professional medical advice.\n"
            "   - Output exclusively in English.\n"
            "   - Your output should either be a [RAG] query (if additional documents are required) or a complete final analysis, but never a mix of both.\n\n"

            "### Example of Final Reasoning Output (if no additional documents are required):\n"
            "```\n"
            "## Final Analysis\n"
            "- **Key Data:** [List key data points]\n"
            "- **Possible Diagnoses:** [List potential diagnoses]\n"
            "- **Next Steps:** [Recommendations for further investigation or referral]\n"
            "```\n\n"

            "Remember, your role is to assist the chat model by providing a well-reasoned analysis, not to directly answer the user. Your conclusions and any [RAG] queries will guide the final response."
        )
    }



async def chat(chat_history: List[object]):
    for token in interact_model(chat_history):
        if token.type == "message":
            yield token
        elif token.type == "reason":
            logger.debug(f"return reason \n{token.content}")
            yield token
        elif token.type == "rag":
            logger.debug(f"do rag logic \n{token.content}")

            # reason = await rag_logic(token.content, chat_history)

            async for reason_token in rag_logic(token.content, chat_history):
                logger.debug(reason_token)
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

    reason_response = interact_model(chat_history, chat_model=False)

    for token in reason_response:
        logger.debug(token)
        yield token

    print(reason_response)




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



