from enum import Enum
from dataclasses import dataclass
from pathlib import Path

BASE_PROMPT_DIR = Path(__file__).parent

@dataclass
class PromptBundle:
    system_path: str
    user_path: str

class PromptTemplate(Enum):
    SUMMARIZE_CLASS = PromptBundle(
        system_path="schema/class_summarization_system.md",
        user_path="schema/class_summarization_user.md"
    )

    GENERATE_XQUERY = PromptBundle(
        system_path="xquery/generate_xquery_system.md",
        user_path="xquery/generate_xquery_user.md"
    )

    SELECT_RELEVANT_CLASSES = PromptBundle(
        system_path="select_classes/select_classes_system.md",
        user_path="select_classes/select_classes_user.md"
    )

    RESPOND_TO_QUESTION = PromptBundle(
        system_path="response/response_system.md",
        user_path="response/response_user.md"
    )

    EXTRACT_KEYWORDS = PromptBundle(
        system_path="extract_keywords/extract_keywords_system.md",
        user_path="extract_keywords/extract_keywords_user.md"
    )

class PromptBuilder:
    @staticmethod
    def build_messages(procedure: PromptTemplate, variables: dict) -> tuple[str, str]:
        """
        Builds the system and user messages for a given procedure and variables.
        """
        
        sys_full_path = BASE_PROMPT_DIR / procedure.value.system_path
        user_full_path = BASE_PROMPT_DIR / procedure.value.user_path
        
        sys_template = sys_full_path.read_text(encoding="utf-8")
        user_template = user_full_path.read_text(encoding="utf-8")

        if not sys_full_path.exists():
            raise FileNotFoundError(f"System prompt missing at: {sys_full_path}")
        if not user_full_path.exists():
            raise FileNotFoundError(f"User prompt missing at: {user_full_path}")
        
        sys_template = sys_full_path.read_text(encoding="utf-8")
        user_template = user_full_path.read_text(encoding="utf-8")

        try:
            sys_content = sys_template.format(**variables)
            user_content = user_template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Missing required variable for prompt: {e}")
            
        return sys_content, user_content
