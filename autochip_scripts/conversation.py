import os

class Conversation:
    """A class to manage conversation messages, supporting logging, retrieval, and modification."""
    
    def __init__(self, log_file=None):
        self.messages = []
        self.log_file = log_file

        # Initialize the log file by clearing it if it already exists
        if self.log_file and os.path.exists(self.log_file):
            open(self.log_file, 'w').close()

    def add_message(self, role, content):
        """Add a new message to the conversation and log it if a log file is set."""
        self.messages.append({'role': role, 'content': content})
        
        # Append the new message to the log file
        if self.log_file:
            with open(self.log_file, 'a') as file:
                file.write(f"{role}: {content}\n")

    def get_messages(self):
        """Retrieve all messages in the conversation."""
        return self.messages

    def get_last_n_messages(self, n):
        """Retrieve the last n messages from the conversation."""
        return self.messages[-n:] if n <= len(self.messages) else self.messages

    def remove_message(self, index):
        """Remove a specific message by index, if it exists."""
        if 0 <= index < len(self.messages):
            del self.messages[index]

    def get_message(self, index):
        """Retrieve a specific message by index, if it exists."""
        return self.messages[index] if 0 <= index < len(self.messages) else None

    def clear_messages(self):
        """Clear all messages from the conversation and reset the log file."""
        self.messages = []
        if self.log_file:
            open(self.log_file, 'w').close()

    def __str__(self):
        """Return the conversation as a formatted string."""
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.messages])
