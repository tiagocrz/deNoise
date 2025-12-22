import os
from google import genai
from google.genai import types
from langfuse import observe
from utils.prompt_manager import PromptLoader

# Service Dependencies
from services.cosmos_db_service import CosmosDBService

# Import the Tools
from tools.choosing_tavily import scrape_url_realtime
from tools.choosing_rag import rag_trigger
from tools.text_to_speech import convert_script_to_audio

class AgentsService:
    """
    The main service layer that orchestrates the three agents.
    """

    def __init__(self, model: str = "gemini-2.5-flash"):
        # 1. Initialize Core Dependencies
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = model
        self.prompts = PromptLoader()
        self.sessions = {}

        # 2. Initialize Service Dependencies
        self.cosmos_db_service = CosmosDBService()
        
    # ========================================================================
    # 1. CONVERSATIONAL AGENT (Chat Page)
    #    Strategy: Agentic RAG (Automatic Function Calling)
    # ========================================================================

    @observe(as_type="agent")
    def generate_chat_answer(self, prompt: str, user_id: str) -> str:
        """
        Generates a chat response while maintaining the session context.
        """
        # 1. Initialize History for User if not exists
        if user_id not in self.sessions:
            self.sessions[user_id] = []
        
        # 2. Define the Toolkit
        agent_tools = [rag_trigger, scrape_url_realtime]

        # For non-logged in user we skip the DB query
        if user_id and user_id != "anonymous":
            user_profile = self.cosmos_db_service.retrieve_user_instructions(user_id)
        else:
        # Skip DB entirely for anonymous users
            user_profile = None

        # 3. Prepare System Instructions (User Profile)
        if user_profile:
            custom_instructions = user_profile["system_instructions"]
            display_name = user_profile["display_name"]
        else:
            # For non logged in users
            custom_instructions = ""
            display_name = ""

        # Format the base system instruction
        base_system_instruction = self.prompts.format(
            "conversational_agent_system", 
            custom_instructions=custom_instructions
        )
        
        if display_name != "":
            full_system_instruction = f"{base_system_instruction}\n\nThe user's name is {display_name}. Address them by name when appropriate."
        else:
            full_system_instruction = base_system_instruction
        
        # 4. Add the NEW User Message to History
        # We create a structured 'Content' object for the user's prompt
        user_message = types.Content(
            role="user",
            parts=[types.Part(text=prompt)]
        )
        self.sessions[user_id].append(user_message)

        # 5. Call Gemini with FULL HISTORY
        # We pass the entire list of previous messages (self.sessions[user_id])
        # Gemini will see the whole conversation context.
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

        # 6. Extract Answer & Update History
        # The 'response.text' is the final natural language answer (after any tool usage)
        model_answer_text = response.text
        
        # Create a structured 'Content' object for the model's answer
        model_message = types.Content(
            role="model",
            parts=[types.Part(text=model_answer_text)]
        )
        self.sessions[user_id].append(model_message)

        return model_answer_text
    

    def clear_session_memory(self, user_id: str):
        """
        Clears the chat history for a specific user.
        Call this when the user clicks 'Clear Chat' or logs out.s
        """
        if user_id in self.sessions:
            del self.sessions[user_id]
            print(f"Memory cleared for user: {user_id}")
        return {"status": "success", "message": "Chat history cleared"}
    


    # ========================================================================
    # 2. REPORT GENERATOR (Report Page)
    #    Strategy: Deterministic RAG (Manual Tool Call)
    # ========================================================================

    @observe(as_type="agent")
    def generate_report(self, topics: str, time_range: str, structure: str, user_id: str) -> str:
        """
        Generates a structured report. 
        We explicitly call the 'rag_trigger' tool to ensure
        the report is grounded in the exact data requested.
        """
        # 1. Retrieve Context (Manual Tool Execution)
        # We reuse the same tool logic, but we force it to run now.
        context = rag_trigger(query=topics, time_scope=time_range)
        print("RAG CONTEXT:", context)

        # 2. System Instructions
        # For non-logged in user we skip the DB query
        if user_id and user_id != "anonymous":
            user_profile = self.cosmos_db_service.retrieve_user_instructions(user_id)
        else:
        # Skip DB entirely for anonymous users
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
        
        # 3. Call Gemini (Context injected into prompt)
        full_contents = [
            f"Topic: {topics}",
            f"\n\n--- NEWS (Source: Internal DB) ---\n{context}"
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

    # ========================================================================
    # 3. PODCAST GENERATOR (Podcast Page)
    #    Strategy: Deterministic RAG (Manual Tool Call) + TTS
    # ========================================================================

    @observe(as_type="agent")
    def generate_podcast(self, topics: str, time_range: str, structure: str, user_id: str) -> str:
        """
        Generates a podcast audio file.
        Step 1: Retrieve Data (Manual Tool Call).
        Step 2: Generate Script (LLM).
        Step 3: Generate Audio (TTS Tool).
        """
        # 1. Retrieve Context (Manual Tool Execution)
        context = rag_trigger(query=topics, time_scope=time_range)
        
        # 2. Generate Script
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
            f"\n\n--- PODCAST SOURCE MATERIAL ---\n{context}"
        ]

        script_response = self.gemini_client.models.generate_content(
            model=self.model,
            contents=full_contents,
            config=types.GenerateContentConfig(
                temperature=0.3,
                system_instruction=full_system_instruction
            )
        )
        podcast_script = script_response.text

        # 3. Convert Script to Audio (ElevenLabs Tool)
        return convert_script_to_audio(podcast_script)