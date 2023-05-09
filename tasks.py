from langchain.chat_models import ChatOpenAI
from langchain.schema import (
    BaseMessage,
    AIMessage,
    HumanMessage,
    SystemMessage,
)
from dotenv import load_dotenv
import re
from utils import ask_gpt4
from characters import elon_llm, gwynne_llm, marc_llm, steve_llm

load_dotenv()


def llm(messages: list, temperature=0, stop: str = None, model="gpt-3.5-turbo") -> str:
    LLM = ChatOpenAI(temperature=temperature, model_name=model)
    ai_msg = LLM.generate(
        messages=[messages],
        stop=stop if stop else None,
    )
    return ai_msg.generations[0][0].message.content


### Helper functions ###
def create_title_from_content(content: str) -> str:
    prompt = f"""
    Your task is to generate a fitting title for a topic of discussion. 

    Create a title for topic descriptio below, delimited by triple \
    backticks, in at most 6 words.

    Topic description: ```{content}```
    """
    title = llm(messages=[HumanMessage(content=prompt)])
    return title


def summarize_thread(messages: list[str]) -> str:
    system_prompt = """
    Please provide a comprehensive and accurate summary of the conversation \
    that includes key points, important details, and relevant context from each message. \
    Your response should be well-organized and present the information in a clear \
    and logical manner.
    """
    messages = [HumanMessage(content=message) for message in messages]
    messages.append(SystemMessage(content=system_prompt))
    summary = llm(messages=messages, model="gpt-4", temperature=0.3)
    return summary


def research_topic(prompt: str, max_questions: int = 5) -> str:
    def _remove_numbered_bullet(text: str) -> str:
        # Define a regular expression pattern to match the number and bullet
        pattern = r"^\d+\.\s+"
        # Use the re.sub() function to remove the pattern from the beginning of the string
        return re.sub(pattern, "", text)

    system_prompt = f"""
    As a world-renowned researcher, research the topic stated in the inital message \
    and engage with chatGPT to gather valuable information on that subject. Your task \
    is to ask insightful and thought-provoking questions that will help you gain a deeper \
    understanding of the topic. Craft well-structured, clear, and relevant queries that \
    demonstrate your critical thinking skills and deep knowledge of the subject.

    Consider utilizing open-ended questions that encourage detailed explanations from \
    chatGPT, as well as follow-up questions based on its responses. This approach will \
    allow you to explore various aspects of the topic more thoroughly and promote an \
    engaging conversation.

    Begin by stating the research topic you have selected. Then, create at least five \
    unique and creative inquiries related to the topic, ensuring they are designed to \
    elicit informative answers from chatGPT.

    List your questions seperated by newlines. Only write questions.
    """
    max_questions = max_questions if max_questions else 5
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=prompt)]
    questions = llm(messages=messages, temperature=0.7, model="gpt-4")
    questions = [
        _remove_numbered_bullet(q)
        for q in questions.split("\n")
        if q and "research" not in q.lower()
    ]  # GPT has a tendency to let the first line be "Research topic: ..."
    for question in questions[:max_questions]:
        answer = ask_gpt4(question)
        messages += [HumanMessage(content=question), AIMessage(content=answer)]
        yield (question, answer)


def council_meeting(prompt: str, context_msg: str, n_rounds: int = 1):
    n_rounds = n_rounds if n_rounds else 1
    BOARD_MEMBERS = [
        ("Elon Musk", elon_llm),
        ("Steve Jobs", steve_llm),
        ("Marc Andreessen", marc_llm),
    ]
    messages = (
        [
            HumanMessage(content=f"Background context: {context_msg}"),
            HumanMessage(content=prompt),
        ]
        if context_msg
        else [HumanMessage(content=prompt)]
    )
    for i in range(n_rounds):
        for name, llm in BOARD_MEMBERS:
            message = llm(messages=messages)
            message = f"{name}: {message}"
            messages.append(HumanMessage(content=message))
            yield (name, message)
