from interactions import (
    Client,
    Intents,
    listen,
    slash_command,
    slash_option,
    SlashCommandChoice,
    SlashContext,
    OptionType,
)
import time

# from db import crud, db, models #FIXME Uncomment, when dumping data to db
import importlib
from tasks import (
    create_title_from_content,
    summarize_thread,
    research_topic,
    council_meeting,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
import requests
from characters import gwynne_llm
from dotenv import dotenv_values

config = dotenv_values()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1_900,
    chunk_overlap=0,
    length_function=len,
)
AVATAR_URLS = {
    "Elon Musk": "https://i.imgur.com/A4VeMXJ.jpeg",
    "Steve Jobs": "https://i.imgur.com/JCXnhcv.jpeg",
    "Marc Andreessen": "https://golden-media.s3.amazonaws.com/topics/642879e8-fee7-4818-9e59-dea9594f5dd5.png",
    "GPT": "https://logos-world.net/wp-content/uploads/2023/02/ChatGPT-Logo-500x281.png",
    "Investigator": "https://hips.hearstapps.com/esquire/assets/17/24/1497710831-anchorman.png",
    "Summary": "https://i.imgur.com/pKd3v73.jpeg",
    "Gwynne Shotwell": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Gwynne_Shotwell_at_2018_Commercial_Crew_announcement.jpg/1200px-Gwynne_Shotwell_at_2018_Commercial_Crew_announcement.jpg",
}
GENERAL_CHANNEL_ID = 1102855356415213640

bot_token = dotenv_values()["DISCORD_BOT_TOKEN"]
bot = Client(intents=Intents.ALL, sync_interactions=True, asyncio_debug=True)


@listen()
async def on_ready():
    print("Ready")
    print(f"This bot is owned by {bot.owner}")


@slash_command(
    name="gpt_session",
    description="Start a thread that contains a GPT thinking session",
)
@slash_option(
    name="session_type",
    description="Number of inputs from each board member",
    required=True,
    opt_type=OptionType.STRING,
    choices=[
        SlashCommandChoice(name="Council meeting", value="council"),
        SlashCommandChoice(name="Research topic", value="research"),
        SlashCommandChoice(name="Gwynne", value="gwynne"),
    ],
)
@slash_option(
    name="prompt",
    description="Detailed description of topic for discussion",
    required=True,
    opt_type=OptionType.STRING,
)
@slash_option(
    name="message_ids",
    description="Include summary message(s) as context",
    required=False,
    opt_type=OptionType.STRING,
)
@slash_option(
    name="n_rounds",
    description="Number of reasoning rounds (1 question/answer or 1 council round)",
    required=False,
    opt_type=OptionType.INTEGER,
)
async def gpt_session(
    ctx: SlashContext,
    session_type: str,
    prompt: str,
    message_ids: str = None,
    n_rounds: int = None,
):
    await ctx.send(f"GPT {session_type} session has started!")
    title = create_title_from_content(content=prompt)

    # Fetch the channel
    channel = await bot.fetch_channel(channel_id=GENERAL_CHANNEL_ID)
    if message_ids:
        msg = ""
        for message_id in message_ids.split(","):
            msg_obj = await channel.fetch_message(message_id=message_id)
            msg += "\n\n" + msg_obj.content
        msg = msg.strip()
    else:
        msg = None
    # Create a new public thread in the channel
    if session_type in ["research", "council"]:
        new_thread = await channel.create_thread(name=title)

    # Let the thinking session begin
    if session_type == "research":
        messages = []
        research_session = research_topic(prompt=prompt, max_questions=n_rounds)
        for question, answer in research_session:
            messages += [question, answer]
            send_message(question, thread_id=new_thread.id, user="Investigator")
            send_message(answer, thread_id=new_thread.id, user="GPT")
            time.sleep(3)
    elif session_type == "council":
        council_session = council_meeting(prompt=prompt, context_msg=msg)
        for member, message in council_session:
            messages.append(message)
            send_message(message, channel_id=new_thread, member=member)
            time.sleep(3)
    else:
        action_plan = gwynne_llm(messages=messages + [prompt])
        send_message(action_plan, user="Gwynne Shotwell")

    if session_type in ["research", "council"]:
        # Post summary back to channel
        summary = summarize_thread(messages=messages)
        send_message(summary, user="Summary")


def send_message(message, user, thread_id=None):
    # Split message into chunks of less than 2000 characters in order
    # to stay within Discord's message limit.
    msg_chunks = text_splitter.split_text(message)
    for msg_chunk in msg_chunks:
        response = requests.post(
            config["DISCORD_GENERAL_WEBHOOK"],
            data={
                "content": msg_chunk,
                "username": user,
                "avatar_url": AVATAR_URLS[user] if user in AVATAR_URLS else None,
            },
            params={"thread_id": thread_id if thread_id else None},
        )


# FIXME: Uncomment when dumping data to db
# @listen()
# async def on_message_create(event):
#     msg = event.message
#     author = msg.author.display_name
#     if author != "GPT":
#         msg_obj = models.DiscordMessage(
#             id=msg.id,
#             author=author,
#             channel_id=msg._channel_id,
#             content=msg.content,
#             timestamp=msg.timestamp,
#         )
#         crud.discord.create(msg_obj)


# @listen()
# async def on_message_update(event):
#     msg = event.after
#     msg_obj = models.DiscordMessage(
#         id=msg.id,
#         author=msg.author.display_name,
#         channel_id=msg._channel_id,
#         content=msg.content,
#         timestamp=msg.timestamp,
#     )
#     crud.discord.update(msg_obj)

#     print(f"message received: {event.message.content}")


bot.start(bot_token)
