from revChatGPT.V1 import Chatbot
from dotenv import dotenv_values

config = dotenv_values()


def ask_gpt4(question):
    chatbot = Chatbot(
        config={"access_token": config["CHAT_OPENAI_ACCESS_TOKEN"], "model": "gpt-4"}
    )
    answer = list(chatbot.ask(question))[-1]["message"]
    return answer
