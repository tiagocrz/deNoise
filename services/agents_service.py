import os
from google import genai
from google.genai import types
from langfuse import observe
from utils.prompt_manager import PromptLoader

# Service Dependencies
from services.cosmos_db_service import CosmosDBService
from services.MOCK_cosmos_db_service import MockCosmosDBService

# Import the Tools
# We use these for BOTH the Agentic Chat (Auto) and the Deterministic Generators (Manual)
from tools.choosing_tavily import scrape_url_realtime
from tools.choosing_rag import rag_trigger
from tools.text_to_speech import convert_script_to_audio

from elevenlabs.play import play


class AgentsService:
    """
    The main service layer that orchestrates the three agents.
    """

    def __init__(self, model: str = "gemini-2.5-flash"):
        # 1. Initialize Core Dependencies
        self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = model
        self.prompts = PromptLoader()

        # 2. Initialize Service Dependencies
        self.cosmos_db_service = MockCosmosDBService()
        
    # ========================================================================
    # 1. CONVERSATIONAL AGENT (Chat Page)
    #    Strategy: Agentic RAG (Automatic Function Calling)
    # ========================================================================

    @observe(as_type="agent")
    def generate_chat_answer(self, prompt: str, user_id: str) -> str:
        """
        Generates a chat response. 
        Gemini automatically decides whether to use the internal DB tool, 
        the external scraper, or just chat.
        """
        # 1. Define the Toolkit (Actual Python functions)
        agent_tools = [rag_trigger, scrape_url_realtime]

        # 2. System Instructions
        custom_instructions = self.cosmos_db_service.retrieve_user_instructions(user_id)
        full_system_instruction = self.prompts.format(
            "conversational_agent_system", 
            custom_instructions=custom_instructions
        )
        
        # 3. Call Gemini (Auto Mode)
        response = self.gemini_client.models.generate_content(
            model=self.model,
            contents=prompt,
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

        return response.text

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

        # 2. System Instructions
        user_instructions = self.cosmos_db_service.retrieve_user_instructions(user_id)
        full_system_instruction = self.prompts.format(
            "report_generator_system",
            structure=structure,
            custom_instructions=user_instructions
        )
        
        # 3. Call Gemini (Context injected into prompt)
        full_contents = [
            f"Topic: {topics}",
            f"\n\n--- MARKET DATA (Source: Internal DB) ---\n{context}"
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
        user_instructions = self.cosmos_db_service.retrieve_user_instructions(user_id)
        full_system_instruction = self.prompts.format(
            "podcast_generator_system",
            structure=structure,
            custom_instructions=user_instructions
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
        audio = convert_script_to_audio(podcast_script)
        
        play(audio)