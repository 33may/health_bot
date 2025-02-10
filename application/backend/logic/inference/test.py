import asyncio
import json
import time
import requests

from app.database.database_functions import retrieve_similar_documents
from huggingface_hub import InferenceClient

from app.inference.chat import chat_model


async def main():
     # start = time.time()
    #
    # url = "https://openrouter.ai/api/v1/chat/completions"
    # headers = {
    #     "Content-Type": "application/json"
    # }
    # payload = {
    #     "model": "google/gemini-2.0-flash-thinking-exp:free",
    #     "messages": [
    #         {"role": "user", "content": "У мене болить голова, що може бути причиною?"}
    #     ],
    #     "include_reasoning": True,
    #     "stream": True
    # }
    #
    # response = requests.post(url, headers=headers, json=payload, stream=True)
    # response.encoding = 'utf-8'
    #
    # buffer = ""
    # for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
    #     buffer += chunk
    #     while True:
    #         line_end = buffer.find('\n')
    #         if line_end == -1:
    #             break
    #         line = buffer[:line_end].strip()
    #         buffer = buffer[line_end + 1:]
    #         if line.startswith('data: '):
    #             data = line[6:]
    #             if data == '[DONE]':
    #                 break
    #             try:
    #                 data_obj = json.loads(data)
    #                 content = data_obj["choices"][0]["delta"].get("content")
    #                 if content:
    #                     print(content, end="", flush=True)
    #             except json.JSONDecodeError:
    #                 pass
    #
    # print(time.time() - start)
    # # print(completion.choices[0].message.content)

    chat_model()



if __name__ == '__main__':
    asyncio.run(main())
