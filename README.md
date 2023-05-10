### AICorp
Experiments with creating various "role playing" scenarios and then let GPT play them out. Currently, this has been quite useful for doing initial research into a topic and getting various perspectives on how to approach a problem.

Discord is used as a frontend, where a discord bot creates the role playing scenarios. Each new role playing scenario is played out in a new thread and a summary is posted back to the main channel.

Currently available role playing scenarios are:

- Research topic: Write a prompt about a topic you want researched and then GPT will create a series of questions regarding the topic. These questions will in turn be asked GPT.
- Council: Write a prompt about the topic you want discussed and optionally provide some discord message ids that will be used a background context and specify the number of discussion rounds. The council members specified in the code will then convene on the topic.

