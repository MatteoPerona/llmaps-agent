import os
from dataclasses import dataclass, fields
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from dataclasses import dataclass

from enum import Enum

class SearchAPI(Enum):
    PERPLEXITY = "perplexity"
    TAVILY = "tavily"

@dataclass(kw_only=True)
class Configuration:
    """The configurable fields for the meal planning assistant."""
    max_web_research_loops: int = 3
    model_name: str = "gpt-4-0125-preview"
    search_api: SearchAPI = SearchAPI.TAVILY
    max_store_recommendations: int = 3  # Maximum number of stores to recommend
    include_price_estimates: bool = True  # Whether to include price estimates
    max_recipe_alternatives: int = 2  # Number of alternative recipes to suggest

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }
        return cls(**{k: v for k, v in values.items() if v})