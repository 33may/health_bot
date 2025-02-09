import json
import requests
import os
from dotenv import load_dotenv

def interact_chat_model(context):
    url = "https://openrouter.ai/api/v1/chat/completions"

    load_dotenv()

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "google/gemini-2.0-flash-thinking-exp:free",
        "messages": context,
        "include_reasoning": True,
        "stream": False
    }

    response = requests.post(url, headers=headers, json=payload)
    response.encoding = 'utf-8'
    data_obj = response.json()
    content = data_obj["choices"][0]["message"]["content"]

    return content

def chat_model():
    chat_history = []
    print("Добро пожаловать в чат! Для выхода введите 'exit'.")

    while True:
        user_message = input("Вы: ")
        if user_message.lower() == "exit":
            break

        chat_history.append({"role": "user", "content": user_message})

        answer = interact_chat_model(chat_history)

        chat_history.append({"role": "assistant", "content": answer})

        print("Ассистент:", answer)


def reasoning_model(prompt):
    """
    Функция модели рассуждения.
    Принимает промпт с запросом и документами, возвращает вывод/рассуждение.
    """
    # Здесь должна быть логика обработки промпта и генерации рассуждения.
    # Для примера возвращаем строку с результатом рассуждения.
    return "[Рассуждение с извлечёнными документами]"


def retrieve_documents(query):
    """
    Функция RAG-системы для извлечения документов по запросу.
    """
    # Здесь можно реализовать поиск в базе данных или через API.
    # Для примера возвращаем строку с документами.
    return "[Документы, релевантные запросу: {}]".format(query)


def is_reasoning_sufficient(reasoning_output):
    """
    Функция для оценки, достаточно ли получено рассуждение.
    Можно анализировать длину ответа, наличие ключевых слов и т.п.
    Для простоты примера возвращаем True, если вывод не пуст.
    """
    return bool(reasoning_output and reasoning_output.strip())


def multi_agent_chat(user_message):
    # 1. Получаем начальный ответ от чат-агента
    initial_response, need_reasoning = chat_model(user_message)

    # Если чат-агент уверен, что может ответить, возвращаем ответ
    if not need_reasoning:
        return initial_response

    # 2. Если требуется дополнительное рассуждение, запускаем агента рассуждения с максимум 2 попытками
    reasoning_attempts = 0
    reasoning_output = ""

    while reasoning_attempts < 2:
        # Извлекаем документы через RAG-систему
        documents = retrieve_documents(user_message)

        # Формируем промпт для агента рассуждения: добавляем исходный запрос и извлечённые документы
        prompt_for_reasoning = (
            f"User query: {user_message}\n"
            f"Documents: {documents}\n"
            f"Provide reasoning or a better prompt."
        )

        # Получаем вывод от модели рассуждения
        reasoning_output = reasoning_model(prompt_for_reasoning)

        # Проверяем, достаточно ли рассуждение для генерации ответа
        if is_reasoning_sufficient(reasoning_output):
            break

        reasoning_attempts += 1

    # 3. Формируем итоговый промпт для чат-агента, добавляя вывод рассуждения
    final_prompt = (
        f"User query: {user_message}\n"
        f"Reasoning output: {reasoning_output}\n"
        f"Answer accordingly, considering the above context."
    )

    final_response, _ = chat_model(final_prompt, additional_context=True)
    return final_response


# Пример использования:
if __name__ == "__main__":
    user_message = "У меня болит голова, что может быть причиной?"
    response = multi_agent_chat(user_message)
    print("Ответ:", response)
