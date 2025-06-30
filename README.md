# 🤖 discord-queue-bot

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![discord.py Version](https://img.shields.io/badge/discord.py-2.3.2-7289DA)
![Uptime](https://img.shields.io/badge/uptime-24/7-brightgreen)

A dynamic and intuitive bot that allows users in a Discord server to join a queue for events. Once started by an admin, the bot automatically cycles through participants, pinging the person at the front of the queue. When that person is finished with their turn, a simple reaction advances the queue to the next user.

Created to organize server-wide events with large groups of users, where each person takes a turn to do something and then passes it on to the next person. It was designed to provide easy, hands-free, automated tracking without requiring constant human input and organization from the event host.

[Invite it to your server here.](https://discord.com/oauth2/authorize?client_id=1388363429009690655&permissions=8&integration_type=0&scope=bot)

---

## 👑 Admin Commands
These commands are restricted to users with Administrator permissions.

| Command | Description |
| :--- | :--- |
| **`/newqueue`** | 🎬 Creates the main queue embed, pins it, and prepares it for users to join. |
| **`/startqueue`** | 🚀 Randomizes the user list, activates the queue, and pings the very first person. |
| **`/deletequeue`** | 🗑️ Shuts down the queue, unpins and deletes the main embed, and clears all data for that channel. |
| **`/queuemessage`**| 📝 Sets a custom message that appears in the embed when it's a user's turn. |
| **`/joinemoji`** | ✨ Sets a custom emoji that users must react with to join the queue. Must be used *before* `/newqueue`. |
| **`/nextemoji`** | ✅ Sets a custom emoji that the current user must react with to advance the queue. Must be used *before* `/startqueue`. |
| **`/queuenext`** | ⏩ Manually skips the current user and advances the queue to the next person. |
| **`/queueback`** | ⏪ Manually moves the queue back to the previous person, respecting the loop. |

---

## 🙋‍♂️ User Actions
Interacting with the queue is simple and intuitive for everyone.

*   **To Join:** React with the designated "join" emoji (⭐ by default) on the main queue message.
*   **To Leave:** Simply remove your reaction from the main queue message. The bot will automatically handle your departure, even if the queue is active.
*   **Your Turn:** When the bot pings you, react to **its message** with the "next" emoji (✅ by default) to pass the turn to the next person.

---

## ⚙️ Deployment

Bot currently has 24/7 uptime with implementation on a lightweight **Flask** website hosted on the free environment [**Render**](https://render.com), and kept awake with [**UptimeRobot**](https://uptimerobot.com) monitoring.
