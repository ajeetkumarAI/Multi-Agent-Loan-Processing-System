from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AgentConfig:
    model_id: str = os.getenv("MODEL_ID", "gpt-4o-mini")
    temperature: float = float(os.getenv("TEMPERATURE", "0.3"))
    top_p: float = float(os.getenv("TOP_P", "0.8"))
