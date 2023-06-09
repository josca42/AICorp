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
import asyncio

# from db import crud, db, models #FIXME Uncomment, when dumping data to db
# import importlib
from tasks import (
    create_title_from_content,
    summarize_thread,
    research_topic,
    council_meeting,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from characters import gwynne_llm
from dotenv import dotenv_values
from interactions.models.discord.webhooks import Webhook

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
webhook = Webhook.from_url(
    url=config["DISCORD_GENERAL_WEBHOOK"],
    client=bot,
)


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
    title = await create_title_from_content(content=prompt)
    # Fetch the channel
    channel = await bot.fetch_channel(channel_id=config["GENERAL_CHANNEL_ID"])
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
        await send_message(
            f"Research prompt: {prompt}", channel=new_thread, user="Investigator"
        )
        messages = []
        research_session = research_topic(prompt=prompt, max_questions=n_rounds)
        async for question, answer in research_session:
            messages += [question, answer]
            await send_message(question, channel=new_thread, user="Investigator")
            await send_message(answer, channel=new_thread, user="GPT")
    elif session_type == "council":
        await send_message(
            f"Council prompt: {prompt}\n\n Background context msgs: {message_ids}",
            channel=new_thread,
            user="Investigator",
        )
        messages = []
        council_session = council_meeting(prompt=prompt, context_msg=msg)
        async for member, message in council_session:
            messages.append(message)
            await send_message(message, channel=new_thread, user=member)
    else:
        action_plan = gwynne_llm(messages=messages + [prompt])
        await send_message(action_plan, user="Gwynne Shotwell")

    if session_type in ["research", "council"]:
        # Post summary back to channel
        summary = await summarize_thread(messages=messages)
        await send_message(
            f"Summary of the thread {title} \n\n{summary}", user="Summary"
        )


async def send_message(message, channel=None, user=None):
    # Split message into chunks so as to avoid discord 2000 character limit
    msg_chunks = text_splitter.split_text(message)
    for msg_chunk in msg_chunks:
        await webhook.send(
            content=msg_chunk,
            username=user,
            avatar_url=AVATAR_URLS[user] if user in AVATAR_URLS else None,
            thread=channel if channel else None,
        )


bot.start(bot_token)
