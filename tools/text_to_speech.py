import base64
import os
from langfuse import observe
from elevenlabs.client import ElevenLabs
from app_settings import ELEVENLABS_API_KEY

@observe(as_type="tool")
def convert_script_to_audio(script: str) -> str:
    '''
    Converts the generated podcast script to audio using ElevenLabs
    and returns a playable Data URI.
    '''
    elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)

    audio_generator = elevenlabs.text_to_speech.convert(
        text=script,
        voice_id="q0IMILNRPxOgtBTS4taI",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )

    audio_bytes = b"".join(audio_generator)

    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

    # Create data URI
    audio_data_uri = f"data:audio/mpeg;base64,{audio_base64}"

    return audio_data_uri