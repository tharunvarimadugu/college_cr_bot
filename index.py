import os
import asyncio
from flask import Flask, request
from telegram import Update
from bot import create_app

app = Flask(__name__)

# Initialize the bot application
application = create_app()

@app.route('/api/index', methods=['POST'])
def webhook():
    if request.method == "POST":
        # Retrieve the message in JSON and then transform it to Telegram object
        update = Update.de_json(request.get_json(force=True), application.bot)
        
        # Run the bot's processing loop
        asyncio.run(application.process_update(update))
        
        return "ok"
    return "ok"

@app.route('/', methods=['GET'])
def index():
    return "Bot is running!"
