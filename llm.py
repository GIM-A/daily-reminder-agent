import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model="qwen3.7-flash",
    api_key=os.getenv("DASHSCOPE_API_KEY", ""),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

if __name__ == "__main__":
    response = llm.invoke("你好，请用一句话介绍你自己")
    print(response.content)