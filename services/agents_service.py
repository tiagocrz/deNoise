import os
from google import genai
from google.genai import types
from langfuse import observe
from utils.prompt_manager import PromptLoader
from app_settings import GEMINI_API_KEY

# Service Dependencies
from services.cosmos_db_service import CosmosDBService

# Import the Tools
from tools.choosing_tavily import scrape_url_realtime
from tools.choosing_rag import rag_trigger
from tools.text_to_speech import convert_script_to_audio

class AgentsService:
    '''
    The main service layer that orchestrates the three agents:
    1. Conversational Agent
    2. Report Generator
    3. Podcast Generator
    '''

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = model
        self.prompts = PromptLoader()
        self.sessions = {}
        self.cosmos_db_service = CosmosDBService()
        
    
    # 1. Conversational Agent
    @observe(as_type="agent")
    def generate_chat_answer(self, prompt: str, user_id: str) -> str:
        '''
        Generates a chat response based on:
        - The tool chosen by the LLM (rag_trigger or scrape_url_realtime);
        - The full chat history for context;
        - The user's custom system instructions and display name from the database.
        - The system instructions template for the conversational agent.
        '''
        # Initialize history for user if not existing
        if user_id not in self.sessions:
            self.sessions[user_id] = []
        
        # Available tools
        agent_tools = [rag_trigger, scrape_url_realtime]

        # For non-logged in ("anonymous") users we skip the DB query, for the others we fetch the user data
        if user_id and user_id != "anonymous":
            user_profile = self.cosmos_db_service.retrieve_user_instructions(user_id)
        else:
            user_profile = None

        if user_profile:
            custom_instructions = user_profile["system_instructions"]
            display_name = user_profile["display_name"]
        else:
            # For non logged in users
            custom_instructions = ""
            display_name = ""

        # Joining all instructions
        base_system_instruction = self.prompts.format(
            "conversational_agent_system", 
            custom_instructions=custom_instructions
        )
        
        if display_name != "":
            full_system_instruction = f"{base_system_instruction}\n\nThe user's name is {display_name}. Address them by name when appropriate."
        else:
            full_system_instruction = base_system_instruction

        # Add user new message to history
        user_message = types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
        self.sessions[user_id].append(user_message)

        # Build answer with tool usage, history and system instructions
        response = self.gemini_client.models.generate_content(
            model=self.model,
            contents=self.sessions[user_id],
            config=types.GenerateContentConfig(
                temperature=0.3,
                system_instruction=full_system_instruction,
                tools=agent_tools,
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode=types.FunctionCallingConfigMode.AUTO
                    )
                )
            )
        )

        model_answer_text = response.text
        
        # Add LLM answer to history
        model_message = types.Content(
            role="model",
            parts=[types.Part(text=model_answer_text)]
        )
        self.sessions[user_id].append(model_message)

        return model_answer_text
    

    def clear_session_memory(self, user_id: str):
        '''
        Clears the chat history for a specific user.
        Call this when the user clicks 'Clear Chat', logs out or refreshes the page
        '''
        if user_id in self.sessions:
            del self.sessions[user_id]
            print(f"Memory cleared for user: {user_id}")
        return {"status": "success", "message": "Chat history cleared"}
    


    # 2. Report Generator
    @observe(as_type="agent")
    def generate_report(self, topics: str, time_range: str, structure: str, user_id: str) -> str:
        '''
        Generates a report based on:
        - Retrieved context from rag_trigger;
        - The user's custom system instructions from the database.
        - The report structure desired by the user.
        - The system instructions template for the report agent.
        '''
        # Retrieve context
        context = rag_trigger(query=topics, time_scope=time_range)

        if user_id and user_id != "anonymous":
            user_profile = self.cosmos_db_service.retrieve_user_instructions(user_id)
        else:
            user_profile = None

        if user_profile:
            custom_instructions = user_profile["system_instructions"]
        else:
            custom_instructions = ""
        
        full_system_instruction = self.prompts.format(
            "report_generator_system",
            structure=structure,
            custom_instructions=custom_instructions
        )
        
        # Build full contents
        full_contents = [
            f"Topic: {topics}",
            f"\n\n--- RAG CONTEXT ---\n{context}"
        ]

        response = self.gemini_client.models.generate_content(
            model=self.model,
            contents=full_contents,
            config=types.GenerateContentConfig(
                temperature=0.3, 
                system_instruction=full_system_instruction
            )
        )
        
        return response.text

    # 3. Podcast Generator
    @observe(as_type="agent")
    def generate_podcast(self, topics: str, time_range: str, structure: str, user_id: str) -> str:
        """
        Generates a podcast script based on:
        - Retrieved context from rag_trigger;
        - The user's custom system instructions from the database.
        - The podcast structure desired by the user.
        - The system instructions template for the podcast agent.

        Then uses the ElevenLabs tool to convert the script to audio and returns a Data URI.
        """
        # Retrieve context
        context = rag_trigger(query=topics, time_scope=time_range)
        
        if user_id and user_id != "anonymous":
            user_profile = self.cosmos_db_service.retrieve_user_instructions(user_id)
        else:
            user_profile = None

        if user_profile:
            custom_instructions = user_profile["system_instructions"]
        else:
            custom_instructions = ""

        full_system_instruction = self.prompts.format(
            "podcast_generator_system",
            structure=structure,
            custom_instructions=custom_instructions
        )

        full_contents = [
            f"Topic: {topics}",
            f"\n\n--- RAG CONTEXT ---\n{context}"
        ]

        # Build podcast script
        script_response = self.gemini_client.models.generate_content(
            model=self.model,
            contents=full_contents,
            config=types.GenerateContentConfig(
                temperature=0.3,
                system_instruction=full_system_instruction
            )
        )
        podcast_script = script_response.text

        # Convert script to audio
        return convert_script_to_audio(podcast_script)