import anthropic
import json
from generate_audio import Podcast

class Chat:
    def __init__(self, api_key, tools=True):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.conversation_history = []
        self.loaded_documents = []  # Track loaded docs

        if tools:
            self.tools =  [ # descriptions were created by Claude
                {
                    "name": "generate_podcast_audio",
                    "description": """Generates audio files for a podcast dialogue using Amazon Polly text-to-speech.
                    
                    This tool takes a podcast script with multiple speakers and creates separate audio files
                    for each dialogue segment using different voices. Supported speakers include:
                    - host (male voice)
                    - guest (female voice)
                    
                    The tool will create an MP3 file that will be hosted in the cloud. It returns a URL to the MP3 file""",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "dialogue_json": {
                                "type": "string",
                                "description": """JSON string containing an array of dialogue segments.
                                Each segment must have 'speaker' and 'text' fields.
                                Example: '[{"speaker":"host","text":"Welcome to the show!"},{"speaker":"guest","text":"Thanks for having me!"}]'"""
                            },
                            "podcast_name": {
                                "type": "string",
                                "description": """An attention-grabbing podcast title that clearly describes the episode content while capturing audience interest like a YouTube thumbnail.
                                
                                The name should be:
                                - DESCRIPTIVE of the main topic and key points discussed
                                - BOLD and eye-catching with emotional hooks (use caps for emphasis on 1-2 key words)
                                - Clear about what listeners will learn or discover
                                - Short and punchy (5-10 words ideal)
                                - Uses specific details rather than vague language
                                - Incorporates power words strategically (SHOCKING, TRUTH, SECRET, EXPOSED, REVEALED, etc.)
                                
                                Examples:
                                - "How AI Transformers REVOLUTIONIZED Language Models"
                                - "The Hidden Cost of Fast Fashion: Environmental TRUTH"
                                - "Why Bitcoin's Halving Could Change Everything in 2024"
                                - "The Science Behind Sleep: Why 8 Hours ISN'T Enough"
                                - "3 Python Libraries That Will 10x Your Data Analysis"
                                
                                Balance clickability with clarity - the title must accurately convey what the episode covers while still being compelling. Avoid misleading clickbait that doesn't match the content."""
                            }
                        },
                        "required": ["dialogue_json", "podcast_name"]
                    }
                }
            ]

    
    # def load_document(self, file_content, filename):
    #     """Load a document into the conversation context"""
    #     # Add document to tracking
    #     self.loaded_documents.append(filename)
        
    #     # Create a system-style message explaining the document
    #     doc_message = f"""I've loaded the document "{filename}" for you. Here's the content:
    #     <document name="{filename}">
    #     {file_content}
    #     </document>

    #     I've analyzed this document and I'm ready to discuss it or create a podcast about it. What would you like to do?"""
        
    #     return doc_message

    
    # def get_loaded_docs_summary(self):
    #     """Return summary of loaded documents"""
    #     if not self.loaded_documents:
    #         return "No documents loaded yet."
    #     return f"Loaded documents: {', '.join(self.loaded_documents)}"

        
    def clear_chat(self):
        self.conversation_history = []
        self.loaded_documents = []


    def chat_stream(self, message):
        """Stream chat responses - returns a generator for streaming text"""
        '''Vibe Code.  Used function manually created chat() as template'''
        self.add_message("user", message)
        
        try:
            with self.client.messages.stream(
                model="claude-sonnet-4-5-20250929",
                max_tokens=5012,
                tools=self.tools,
                messages=self.conversation_history
            ) as stream:
                # Yield text chunks as they come
                for text in stream.text_stream:
                    yield text
                
                # After streaming, handle tool calls
                final_message = stream.get_final_message()
                self.add_message("assistant", final_message.content)
                
                # Process tools if needed
                if final_message.stop_reason == "tool_use":
                    for block in final_message.content:
                        if block.type == "tool_use":
                            yield f"\n\n🔧 Using tool: {block.name}...\n\n"
                            
                            result = self.process_tool_call(block.name, block.input)
                            
                            self.add_message("user", [{
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result)
                            }])
                            
                            # Get follow-up response
                            follow_up = self.client.messages.create(
                                model="claude-sonnet-4-5-20250929",
                                max_tokens=5012,
                                tools=self.tools,
                                messages=self.conversation_history
                            )
                            
                            self.add_message("assistant", follow_up.content)
                            
                            for follow_block in follow_up.content:
                                if hasattr(follow_block, "text"):
                                    yield follow_block.text
                                    
        except Exception as e:
            yield f"\n\nError: {e}"


    def chat(self, message):
        # Legacy
        self.add_message("user", message)
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=5012,
                tools=self.tools,
                messages=self.conversation_history
            )
            
            while response.stop_reason == "tool_use":
                self.add_message("assistant", response.content)
                
                tool_results = []
                for block in response.content:
                    if block.type == "text":
                        print(f"\nClaude: {block.text}")
                    elif block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        
                        print(f"Calling tool: {tool_name}")
                        
                        result = self.process_tool_call(tool_name, tool_input)
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result)
                        })
                
                if tool_results:
                    self.add_message("user", tool_results)
                
                response = self.client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=5012,
                    tools=self.tools,
                    messages=self.conversation_history
                )
            
            self.add_message("assistant", response.content)
            for block in response.content:
                if hasattr(block, "text"):
                    print(f"\nClaude: {block.text}\n")
            
        except Exception as e:
            print(f"\nError: {e}\n")
            if self.conversation_history and self.conversation_history[-1]["role"] == "user":
                self.conversation_history.pop()


    def add_message(self, role, message):
        self.conversation_history.append({'role': role, "content": message})


    def process_tool_call(self, tool_name, tool_input):
        if tool_name == "generate_podcast_audio":
            pod = Podcast(tool_input['podcast_name'])
            url = pod.create_podcast(tool_input['dialogue_json'])
            return {"success": True, "url": url, "message": f"Podcast '{tool_input['podcast_name']}' created successfully!"}
            
        else:
            return {"error": f"Unknown tool '{tool_name}'"}



if __name__ == "__main__":
    '''Vibe Code'''
    import os
    import load_environment

    env = load_environment.load_env()
    api_key=env["API_KEY"]

    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it with: export ANTHROPIC_API_KEY='your-api-key'")
        exit(1)
    
    # Initialize chatbot
    chat = Chat(api_key=api_key, tools=True)
    
    print("=" * 60)
    print("Chatbot started! Type 'quit' or 'exit' to end.")
    print("Type 'clear' to clear conversation history.")
    print("Try: 'Generate a podcast with 2 segments about AI'")
    print("=" * 60)
    print()
    
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        # Check for exit command
        if user_input.lower() in ['quit', 'exit']:
            print("\nGoodbye!")
            break
        
        # Check for clear command
        if user_input.lower() == 'clear':
            chat.clear_chat()
            print("\n[Conversation history cleared]\n")
            continue
        
        # Skip empty input
        if not user_input:
            continue
        
        # Send message to chatbot
        print()
        chat.chat(user_input)
        print()