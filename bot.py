from twilio.rest import Client
from flask import Flask, request
from datetime import datetime, timedelta
import re
from threading import Thread
import time
from dotenv import load_dotenv
import os

load_dotenv()
# Initialize Flask and Twilio client
app = Flask(__name__)

# Twilio credentials
ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")

# Hardcoded group members (replace with actual WhatsApp numbers)
GROUP_MEMBERS = [
    'whatsapp:+1234567890',  # Example: Replace with actual numbers
    'whatsapp:+1987654321',
    'whatsapp:+1567891234'
]

# Keep track of registered users who've interacted with the system
registered_users = set(GROUP_MEMBERS)  # Pre-populate with hardcoded members

client = Client(ACCOUNT_SID, AUTH_TOKEN)
# To store laundry tasks (washer and dryer)
laundry_tasks = {
    'washer': {'task': None, 'notified': False},
    'dryer': {'task': None, 'notified': False}
}

# Message history for the bulletin board approach
message_history = []
MAX_HISTORY = 10  # Keep only the last 10 messages in history

def broadcast_message(message):
    """Send a message to all members of the virtual group"""
    for member in registered_users:
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE,
            to=member
        )
    # Add message to history
    message_history.append({
        'timestamp': datetime.now(),
        'message': message
    })
    # Trim history if needed
    if len(message_history) > MAX_HISTORY:
        message_history.pop(0)

def get_user_name(request_values):
    profile_name = request_values.get('ProfileName')
    from_number = request_values.get('From')
    return profile_name if profile_name else from_number

# Helper function to get task details from the message
def get_task_details(request_values):
    task_details = request_values.get('Body', '')
    task_parts = task_details.split(" ")

    if len(task_parts) == 3:
        task_type = task_parts[0].lower()  # 'washer' or 'dryer'
        task_action = task_parts[1].lower()  # 'start'
        task_unit = task_parts[2]

        # Check if the machine is available
        if task_type == 'washer' and laundry_tasks['washer']['task'] is not None:
            return None, "The washer is currently in use. Please wait until it becomes available.", None
        if task_type == 'dryer' and laundry_tasks['dryer']['task'] is not None:
            return None, "The dryer is currently in use. Please wait until it becomes available.", None

        # Parse duration: handling hours and minutes (e.g., "2 hours 30 minutes" or "2h 30m")
        total_minutes = 0
        hours_match = re.search(r'(\d+)\s*h|\b(\d+)\s*hours?', task_unit)
        minutes_match = re.search(r'(\d+)\s*m|\b(\d+)\s*minutes?', task_unit)

        if hours_match:
            total_minutes += int(hours_match.group(1) or hours_match.group(2)) * 60
        if minutes_match:
            total_minutes += int(minutes_match.group(1) or minutes_match.group(2))

        # If the user specifies only minutes without units like "1m"
        if total_minutes == 0 and task_unit.isdigit():
            total_minutes = int(task_unit)

        # Get the current time
        current_time = datetime.now()

        # Calculate the finish time based on durations
        finish_time = current_time + timedelta(minutes=total_minutes)

        # Format finish time into a readable string
        finish_time_str = finish_time.strftime("%I:%M %p")  # Format: 7:30 PM

        user_name = get_user_name(request_values)

        # Store the task in the laundry_tasks dictionary
        laundry_tasks[task_type] = {
            'task': {
                'user_name': user_name,
                'finish_time': finish_time,
                'phone_number': request_values.get('From')
            },
            'notified': False
        }

        return user_name, task_type, finish_time_str

    return None, None, None

# Background thread to check and send notifications
def notify_task_completion():
    while True:
        current_time = datetime.now()
        for machine in ['washer', 'dryer']:
            task_info = laundry_tasks.get(machine)
            task = task_info['task']  # The actual task details (user, time, etc.)
            notified = task_info['notified']
            
            if task and current_time >= task['finish_time'] and not notified:
                # Personal notification to the user
                personal_message = f"⏰ Hey {task['user_name']}, your {machine} cycle is done! Please take out your clothes."
                
                # Send a private message to the user's personal phone number
                client.messages.create(
                    body=personal_message,
                    from_=TWILIO_PHONE,
                    to=task['phone_number']  # Send to the user's personal phone number directly
                )
                
                # Public notification to the "group"
                public_message = f"⏰ {task['user_name']}'s {machine} cycle is now complete."
                broadcast_message(public_message)
                
                # Mark that the user has been notified
                task_info['notified'] = True  # No further notifications until user removes laundry
                
        time.sleep(60)  # Check every minute

# Start the background thread
Thread(target=notify_task_completion, daemon=True).start()

@app.route("/whatsapp", methods=['POST'])
def whatsapp_reply():
    request_data = request.values.to_dict()
    incoming_msg = request_data.get('Body', '').strip()
    user_name = get_user_name(request_data)
    user_number = request_data.get('From')
    
    # Add user to registered users if not already there
    registered_users.add(user_number)

    # Handle the "Laundry Status" command (send private message)
    if incoming_msg.lower() == "laundry status":
        response = "🧺 **Laundry Status**:\n"
        for machine in ['washer', 'dryer']:
            task_info = laundry_tasks.get(machine)
            task = task_info.get('task')  # Get the actual task
            if task:
                if datetime.now() >= task['finish_time']:
                    response += f"- {task['user_name']}'s {machine} cycle is done. They have been notified to remove their laundry.\n"
                else:
                    time_left = task['finish_time'] - datetime.now()
                    minutes_left = int(time_left.total_seconds() / 60)
                    response += f"- {task['user_name']}'s {machine} will finish at {task['finish_time'].strftime('%I:%M %p')} ({minutes_left} minutes left)\n"
            else:
                response += f"- {machine.capitalize()} is available.\n"

        # Send the private message to the user (direct message)
        client.messages.create(
            body=response,
            from_=TWILIO_PHONE,
            to=user_number
        )

    # Handle "History" command to see recent bulletin board messages
    elif incoming_msg.lower() == "history":
        if not message_history:
            response = "No messages in history yet."
        else:
            response = "📋 **Recent Messages**:\n"
            for i, msg in enumerate(reversed(message_history)):
                timestamp = msg['timestamp'].strftime("%I:%M %p")
                response += f"{i+1}. [{timestamp}] {msg['message']}\n"
        
        client.messages.create(
            body=response,
            from_=TWILIO_PHONE,
            to=user_number
        )

    # Handle "Register" command
    elif incoming_msg.lower() == "register":
        if user_number in registered_users:
            response = "You are already registered to receive laundry notifications."
        else:
            registered_users.add(user_number)
            response = "You have been registered to receive laundry notifications."
        
        client.messages.create(
            body=response,
            from_=TWILIO_PHONE,
            to=user_number
        )

    # Handle "Unregister" command
    elif incoming_msg.lower() == "unregister":
        if user_number in registered_users:
            registered_users.remove(user_number)
            response = "You have been unregistered from laundry notifications."
        else:
            response = "You are not currently registered."
        
        client.messages.create(
            body=response,
            from_=TWILIO_PHONE,
            to=user_number
        )

    # Handle start of washer/dryer (check if machine is in use)
    elif incoming_msg.lower().startswith("washer start") or incoming_msg.lower().startswith("dryer start"):
        user_name, task_type, finish_time = get_task_details(request_data)
        
        if isinstance(task_type, str) and ("currently in use" in task_type):
            # Send an immediate response to the user if the machine is in use
            client.messages.create(
                body=task_type,
                from_=TWILIO_PHONE,
                to=user_number
            )
        elif user_name and task_type and finish_time:
            # Send a confirmation to the individual user
            personal_message = f"✅ You've started the {task_type}. It will finish at {finish_time}."
            client.messages.create(
                body=personal_message,
                from_=TWILIO_PHONE,
                to=user_number
            )
            
            # Broadcast to all registered users
            group_message = f"🧺 {user_name} started the {task_type}. It will finish at {finish_time}."
            broadcast_message(group_message)

    # Handle removal of laundry (public group notification)
    elif incoming_msg.lower() == "washer removed" or incoming_msg.lower() == "dryer removed":
        machine = incoming_msg.lower().split(' ')[0]
        task_info = laundry_tasks.get(machine)
        
        if task_info and task_info['task']:  # Ensure there's an active task
            # Reset the notification flag
            task_info['notified'] = False  # Allow notifications for the next cycle
            
            # Optionally, reset or remove the task from the machine if you want
            task_info['task'] = None
            
            # Broadcast to all registered users
            response = f"✅ {user_name} removed their laundry from the {machine}. The machine is free to use!"
            broadcast_message(response)
            
            # Send confirmation to the user
            client.messages.create(
                body=f"Thank you for marking your {machine} laundry as removed. All users have been notified.",
                from_=TWILIO_PHONE,
                to=user_number
            )
        else:
            client.messages.create(
                body=f"There doesn't seem to be any active task for the {machine}.",
                from_=TWILIO_PHONE,
                to=user_number
            )

    # Handle help command
    elif incoming_msg.lower() == "hi":
        help_text = """🧺 *Laundry Bot Commands*:
- "washer start 45m" - Start washer for 45 minutes
- "dryer start 30m" - Start dryer for 30 minutes
- "washer removed" - Mark washer as free
- "dryer removed" - Mark dryer as free
- "laundry status" - Check current status
- "history" - See recent notifications
- "register" - Sign up for notifications
- "unregister" - Stop receiving notifications
- "hi" - Show this message"""

        client.messages.create(
            body=help_text,
            from_=TWILIO_PHONE,
            to=user_number
        )

    return "OK", 200  # Respond with status 200 to Twilio


if __name__ == "__main__":
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)