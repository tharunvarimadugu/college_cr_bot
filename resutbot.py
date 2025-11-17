import logging
from ExamTimeTable import results_checking, exam_timetable
from resutbot import result_bot
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# --- Configuration ---
# FIX 1: Defined the bot token
TOKEN="8560319193:AAFXsjL5n6td-HnG_nzqZ2WF_NmZWYi7hXs"
# --- Constants ---
# States for ConversationHandler
(
    GET_REGULATION,  # Waiting for user to select regulation (R18, R20, R23)
    GET_YEAR,        # Waiting for user to select year (1, 2, 3, 4)
    GET_SEM,         # Waiting for user to select semester (1, 2)
    GET_OPTION,
    GET_DEPARTMENT,    # NEW STATE
    CONFIRM_DEPARTMENT, # NEW STATE
    GET_ROLL,        # Waiting for user to type their roll number
    CONFIRM_ROLL,    # Waiting for user to confirm roll number (Yes/No)
    GET_DOB,         # Waiting for user to type their date of birth
    CONFIRM_DOB,     # Waiting for user to confirm date of birth (Yes/No)
) = range(10)

MAX_TIMETABLE_ENTRIES = 10

# --- Logging Setup ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Global Class Instance ---
try:
    a = results_checking()
    b = result_bot()
    
except Exception as e:
    logger.critical(f"Failed to instantiate helper classes: {e}", exc_info=True)
    a = None
    b = None
# --- Bot Handlers ---


# --- 1. Simple Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hi! I'm a bot. You can use:\n"
             "/examtimetable - To check exam timetables\n"
             "/resultscheck - To get your results"
    )

async def examtimetable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts the /examtimetable flow by asking for Regulation."""
    keyboard = [
        [InlineKeyboardButton("R23", callback_data='R23')],
        [InlineKeyboardButton("R20", callback_data='R20')],
        [InlineKeyboardButton("R18", callback_data='R18')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Choose Regulation for Exam Timetable:",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the button press from the /examtimetable flow."""
    query = update.callback_query
    await query.answer()
    regulation = query.data
    
    try:
        notice = exam_timetable(regulation)
        msg = "\n\n".join(notice[:MAX_TIMETABLE_ENTRIES])
        if not msg:
             msg = "No timetable found for that regulation."
    except Exception as e:
        logger.error(f"Error in exam_timetable function: {e}")
        msg = "Sorry, an error occurred while fetching the timetable."

    await query.edit_message_text(text=msg)


# --- 2. ConversationHandler for /resultscheck ---

async def resultscheck(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the /resultscheck conversation."""
    if a is None or b is None:
        await update.message.reply_text("Sorry, the bot is not configured correctly. Please contact the admin.")
        return ConversationHandler.END
        
    context.user_data.clear()
    keyboard = [
        [
            InlineKeyboardButton("R18", callback_data="reg_R18"),
            InlineKeyboardButton("R20", callback_data="reg_R20"),
            InlineKeyboardButton("R23", callback_data="reg_R23"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Hi! Let's get your results.\n\n"
        "Please select your Regulation:",
        reply_markup=reply_markup
    )
    return GET_REGULATION

async def get_regulation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores Regulation (e.g., "R18") and asks for Year."""
    query = update.callback_query
    await query.answer()
    regulation = query.data.split('_')[1]
    context.user_data["regulation"] = regulation
    
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data="1"),
            InlineKeyboardButton("2", callback_data="2"),
        ],
        [
            InlineKeyboardButton("3", callback_data="3"),
            InlineKeyboardButton("4", callback_data="4"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"Regulation: {regulation}\n\nPlease select your Year:",
        reply_markup=reply_markup
    )
    return GET_YEAR

async def get_year(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores Year (e.g., "3") and asks for Semester."""
    query = update.callback_query
    await query.answer()
    
    year = query.data
    context.user_data["year"] = year
    
    keyboard = [
        [
            InlineKeyboardButton("Semester 1", callback_data="1"),
            InlineKeyboardButton("Semester 2", callback_data="2"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    reg = context.user_data['regulation']
    await query.edit_message_text(
        text=f"Regulation: {reg}\n"
             f"Year: {year}\n\n"
             f"Please select your Semester:",
        reply_markup=reply_markup
    )
    return GET_SEM

async def get_sem(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores Semester, calls a.get_results_link, and shows options."""
    query = update.callback_query
    await query.answer()
    
    sem = query.data
    context.user_data["sem"] = sem
    
    reg = context.user_data['regulation']
    year = context.user_data['year']
    all_collected_data = [reg, year, sem]
    
    link_options = a.get_results_link(all_collected_data)
    
    context.user_data["link_options"] = link_options
    
    keyboard = []
    for index, option in enumerate(link_options):
        keyboard.append([InlineKeyboardButton(option[14:], callback_data=f"{index}")])
        
    if not link_options:
        logger.warning(f"No link options found for {reg}-{year}-{sem}.")
        await query.edit_message_text(
            text=f"✅ Selections complete:\n"
                 f"Regulation: {reg}\n"
                 f"Year: {year}\n"
                 f"Semester: {sem}\n\n"
                 f"Sorry, no result links were found for these options. "
                 f"Please type /cancel or start over with /resultscheck."
        )
        context.user_data.clear()
        return ConversationHandler.END
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text=f"✅ Selections complete:\n"
             f"Regulation: {reg}\n"
             f"Year: {year}\n"
             f"Semester: {sem}\n\n"
             f"Please choose your result link:",
        reply_markup=reply_markup
    )
    return GET_OPTION

async def get_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Stores the chosen option, calls a.print_options, 
    and then asks for Department.
    """
    query = update.callback_query
    await query.answer()
    
    link_from_print_options = None # Initialize variable
    
    try:
        option_index_str = query.data
        option_index = int(option_index_str)
        
        link_options = context.user_data.get("link_options")
        
        if not link_options:
            logger.error("User context is missing 'link_options'. Bot stuck.")
            await query.edit_message_text(
                text="An error occurred (missing context). Please start over with /resultscheck."
            )
            context.user_data.clear()
            return ConversationHandler.END

        if 0 <= option_index < len(link_options):
            selected_option_text = link_options[option_index]
            
            logger.info(f"User selected option index: {option_index}, text: {selected_option_text}")
            
            reg = context.user_data['regulation']
            year = context.user_data['year']
            sem = context.user_data['sem']
            
            all_new_collected_data = [reg, year, sem, option_index]
            
            logger.info(f"Calling a.print_options with: {all_new_collected_data}")
            link_from_print_options = a.print_options(all_new_collected_data)
            
            if link_from_print_options is None:
                logger.error("a.print_options returned None. Cannot proceed.")
                await query.edit_message_text(text="An error occurred while selecting the link. Please start over.")
                context.user_data.clear()
                return ConversationHandler.END
                
            context.user_data['final_link'] = link_from_print_options
            logger.info(f"Storing 'final_link': {link_from_print_options}")
            
            await query.edit_message_text(text=f"You selected: {selected_option_text}")
        
        else:
            logger.warning(f"Invalid option index: {option_index} for link_options of length {len(link_options)}")
            await query.edit_message_text(
                text="An error occurred (invalid index). Please start over with /resultscheck."
            )
            context.user_data.clear()
            return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error in get_option: {e}", exc_info=True)
        await query.edit_message_text(
            text="A critical error occurred. Please start over with /resultscheck."
        )
        context.user_data.clear()
        return ConversationHandler.END
        
    # --- NEW STEP: Ask for Department ---
    try:
        # Pass the link to bot_work to get departments
        all_new_collected_data = [link_from_print_options]
        logger.info(f"Calling b.bot_work with: {all_new_collected_data}")
        
        # This call must be for getting the list
        departments = b.bot_work(all_new_collected_data) 
        
        if not departments:
            logger.error("b.bot_work() returned no departments.")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Could not find any departments for this result link. Please contact the admin."
            )
            context.user_data.clear()
            return ConversationHandler.END

        keyboard = []
        # Create a button for each department
        # Using "dept_{index}" as callback data
        for index, dept in enumerate(departments):
             keyboard.append([InlineKeyboardButton(dept, callback_data=f"dept_{index}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please select your department:",
            reply_markup=reply_markup
        )
        return GET_DEPARTMENT

    except Exception as e:
        logger.error(f"Error calling b.bot_work(): {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="A critical error occurred while fetching departments. Please start over with /resultscheck."
        )
        context.user_data.clear()
        return ConversationHandler.END

async def get_department(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the chosen department index and asks for confirmation."""
    query = update.callback_query
    await query.answer()
    
    # query.data will be "dept_0", "dept_1", etc.
    department_index = query.data.split('_', 1)[1] 
    context.user_data["department"] = int(department_index)
    department=context.user_data["department"]
    
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="confirm_dept_ok"),
            InlineKeyboardButton("No", callback_data="confirm_dept_no"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # We can't show the department name easily, so we just show the index.
    # A better way would be to store the departments list in user_data.
    context.user_data["departments"] = departments = b.bot_work([context.user_data.get("final_link")])
    department_name = departments[int(department_index)] if departments and 0 <= int(department_index) < len(departments) else "Unknown"  
    context.user_data["department_name"] = department_name
    await query.edit_message_text(
        text=f"Department selected (department_name: {department_name}).\nIs this correct?",
        reply_markup=reply_markup
    )
    return CONFIRM_DEPARTMENT

async def confirm_department(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirms Department (or asks again) and moves to ask for Roll Number."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_dept_ok":
        await query.edit_message_text(text=f"Department (department_name: {context.user_data['department_name']}) confirmed.")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Great. Now, please enter your Roll Number:"
        )
        return GET_ROLL
    else:
        # Re-send department list
        try:
            # We need the link again to re-fetch departments
            link = context.user_data.get("final_link")
            if not link:
                logger.error("User context missing 'final_link' in confirm_department.")
                await query.edit_message_text(text="An error occurred (missing context). Please start over with /resultscheck.")
                context.user_data.clear()
                return ConversationHandler.END
            
            departments = b.bot_work([link]) # Re-call with link
            keyboard = []
            for index, dept in enumerate(departments):
                 keyboard.append([InlineKeyboardButton(dept, callback_data=f"dept_{index}")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                text="Okay, please select your department again:",
                reply_markup=reply_markup
            )
            return GET_DEPARTMENT
        except Exception as e:
            logger.error(f"Error re-fetching departments in confirm_department: {e}", exc_info=True)
            await query.edit_message_text(text="An error occurred. Please start over with /resultscheck.")
            context.user_data.clear()
            return ConversationHandler.END

async def get_roll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the roll number and asks for confirmation."""
    roll = update.message.text.strip()
    context.user_data["roll"] = roll
    
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="roll_ok"),
            InlineKeyboardButton("No", callback_data="roll_no"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Roll entered: {roll}\nIs this correct?",
        reply_markup=reply_markup
    )
    return CONFIRM_ROLL

async def confirm_roll(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirms Roll Number (or asks again) and asks for Date of Birth."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "roll_ok":
        await query.edit_message_text(text=f"Roll number {context.user_data['roll']} confirmed.")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Finally, please enter your Date of Birth (MM/DD/YYYY):"
        )
        return GET_DOB
    else:
        await query.edit_message_text(text="Okay, please enter your Roll Number again:")
        return GET_ROLL

async def get_dob(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the Date of Birth and asks for confirmation."""
    dob = update.message.text.strip()
    context.user_data["dob"] = dob
    
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="dob_ok"),
            InlineKeyboardButton("No", callback_data="dob_no"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Date of Birth entered: {dob}\nIs this correct?",
        reply_markup=reply_markup
    )
    return CONFIRM_DOB

async def confirm_dob(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirms DOB (or asks again), processes results, and ends conversation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "dob_ok":
        await query.edit_message_text(text=f"Date of Birth {context.user_data['dob']} confirmed.")
        
        # Get all the data collected and stored in context
        link = context.user_data.get("final_link")
        # Get the new department data
        department = context.user_data.get("department") # This is the index
        roll = context.user_data.get("roll")
        dob = context.user_data.get("dob")
        
        # Final data list to pass to the processing function
        all_collected_data = [link, department, roll, dob]
        
        logger.info(f"Final data collected: {all_collected_data}")
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="✅ **All data collected!**\n\n"
                 f"Processing your request...\n\n"
                 "Please wait...",
            parse_mode="Markdown"
        )
        
        try:
            # Final call to b.select_department
            logger.info(f"Calling b.select_department with: {all_collected_data}")
            all_collected_data=[link, department, roll, dob]
            results = b.select_department(all_collected_data)
            
            if isinstance(results, str) and results.endswith('.png'):
                logger.info(f"Sending photo: {results}")
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=open(results, 'rb'),
                    caption="Here is your result."
                )
            else:
                logger.info(f"Sending text result: {results}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Here is your result link/data: {results}"
                )
                
        except Exception as e:
            logger.error(f"Error in b.select_department function: {e}", exc_info=True)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, an error occurred while processing your results."
            )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    else: 
        await query.edit_message_text(text="Okay, please enter your Date of Birth again (MM/DD/YYYY):")
        return GET_DOB

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text(
        "Results check cancelled. Type /resultscheck to begin again."
    )
    context.user_data.clear()
    return ConversationHandler.END


# --- 3. Main function to build and run the bot ---

def main() -> None:
    """Run the bot."""
    
    if TOKEN == "YOUR_BOT_TOKEN" or not TOKEN:
        logger.critical("="*50)
        logger.critical("ERROR: TOKEN is not set.")
        logger.critical("Please replace 'YOUR_BOT_TOKEN' with your actual bot token.")
        logger.critical("="*50)
        return
    
    if a is None or b is None:
        logger.critical("Helper classes failed to initialize. Bot cannot start.")
        return

    application = Application.builder().token(TOKEN).build()

    # --- Setup ConversationHandler for /resultscheck ---
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("resultscheck", resultscheck)],
        states={
            GET_REGULATION: [CallbackQueryHandler(get_regulation, pattern="^reg_")],
            GET_YEAR: [CallbackQueryHandler(get_year, pattern=r"^(1|2|3|4)$")],
            GET_SEM: [CallbackQueryHandler(get_sem, pattern=r"^(1|2)$")],
            GET_OPTION: [CallbackQueryHandler(get_option, pattern=r"^\d+$")],
            # FIX 4: Added new handlers for department
            GET_DEPARTMENT: [CallbackQueryHandler(get_department, pattern="^dept_")],
            CONFIRM_DEPARTMENT: [CallbackQueryHandler(confirm_department, pattern="^confirm_dept_")],
            GET_ROLL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_roll)],
            CONFIRM_ROLL: [CallbackQueryHandler(confirm_roll, pattern="^roll_")],
            GET_DOB: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_dob)],
            CONFIRM_DOB: [CallbackQueryHandler(confirm_dob, pattern="^dob_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    application.add_handler(conv_handler)

    # --- Add Simple Handlers ---
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('examtimetable', examtimetable))
    
    application.add_handler(CallbackQueryHandler(button, pattern=r"^(R23|R20|R18)$"))

    print("Bot is running... Press Ctrl-C to stop.")
    application.run_polling()

if __name__ == "__main__":
    main()

