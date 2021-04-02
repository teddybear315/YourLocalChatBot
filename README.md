# YourLocalChatBot

Your local chatbot is an easy to use, modifiable, and beginner friendly Chat Bot. YLCB is developed by [Teddy.](https://solo.to/depressionscr)

---

## Why should I use YLCB?
Because it is easy to use, frequently updated, we pay attention to user requests, and it is highly modifiable due to the use of discord.py's cog system


## What is the Cog System?

It is an easy way to load, reload, and unload files from use with the Discord API.


## Why do you use a database?

We don't store personal data on our databases, only information you give us or information used internally within the bot itself (ex: your point balance or discord id)


## This is it?

No! We host and maintain all our plugins you can find them [here](https://github.com/teddybear315/YLCB-Extensions)


## Version scheme?

We use (as far as we're aware) a custom version scheme that follows this format

`v{api}.{major}.{minor}b{patch}`

- `api`: wont change until the core of the bot and extensions needs to be reworked, due to me being a bad programmer or due to any major dependency updates
- `major`: whenever `main.py` or `modules/` files are updated/added and big or a lot of changes are made
- `minor`: whenever `main.py` or `modules/` files recieve smaller updates that only add a few things
- `patch`: similar to minor but when update only affects a few lines or edits comments or docstrings

So for example `v1.2.3b4`

- Uses api and dependency verions that are compatible with `v1.x`
- Extensions may not be compatible with any version that isnt `v1.2.x`
- `minor` and `patch` mainly just show how much code I've written since the last `major` update