import json
import requests
import os
from dotenv import load_dotenv

def interact_chat_model(context, stream=True):
    url = "https://openrouter.ai/api/v1/chat/completions"

    # Загружаем переменные окружения
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
        "stream": stream
    }

    if stream:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.encoding = 'utf-8'
        buffer = ""
        content = ""
        # Читаем ответ частями
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
                        break
                    try:
                        data_obj = json.loads(data)
                        # Извлекаем "токен" из дельты
                        token = data_obj["choices"][0]["delta"].get("content")
                        if token:
                            print(token, end="", flush=True)
                            content += token
                    except json.JSONDecodeError:
                        # Если не получилось распарсить JSON, пропускаем строку
                        pass
        print()  # Добавляем перевод строки после завершения потока
        return content
    else:
        response = requests.post(url, headers=headers, json=payload)
        response.encoding = 'utf-8'
        data_obj = response.json()
        content = data_obj["choices"][0]["message"]["content"]
        return content

def chat_model():
    system_message = {
        "role": "system",
        "content": (
            "Ви є досвідченим фахівцем в галузі охорони здоров'я. "
            "Ваші відповіді повинні бути виключно українською мовою, "
            "природними, детальними та доброзичливими. Не відповідайте лише "
            "списками чи короткими пунктами, а розгорнуто пояснюйте, надавайте приклади та рекомендації. "
            "Якщо користувач задає питання про симптоми або стан здоров'я, обов’язково наголошуйте, "
            "що ваші поради є загальними і не замінюють консультацію з лікарем. "
            "Також, намагайтеся створювати компактні та лаконічні відповіді, уникати надмірної довготи, "
            "якщо це можливо, зберігаючи при цьому всі важливі деталі."
        )
    }

    chat_history = [system_message]

    print("Вітаємо у чаті! Для виходу введіть 'exit'.")
    while True:
        user_message = input("Ви: ")
        if user_message.lower() == "exit":
            break

        chat_history.append({"role": "user", "content": user_message})

        print("Ассистент:", end=" ")
        # Вызываем функцию с параметром stream=True, чтобы ответ выводился постепенно
        answer = interact_chat_model(chat_history, stream=True)
        chat_history.append({"role": "assistant", "content": answer})
        print()  # Пустая строка для разделения диалогов


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
