import os
from pathlib import Path

class PromptLoader:
    '''
    Load and manage prompt templates from files.
    '''
    def __init__(self, prompts_dir: str = None):
        if prompts_dir is None:
            current_dir = Path(__file__).parent
            prompts_dir = current_dir.parent / "prompts"
        self.prompts_dir = Path(prompts_dir)

    def load(self, prompt_name: str) -> str:
        '''
        Load a prompt template from file.
        '''
        prompt_path = self.prompts_dir / f"{prompt_name}.txt"

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def format(self, prompt_name: str, **kwargs) -> str:
        '''
        Load and format a prompt template with variables.
        '''
        template = self.load(prompt_name)
        return template.format(**kwargs)
