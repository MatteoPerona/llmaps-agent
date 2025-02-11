import operator
from dataclasses import dataclass, field
from typing_extensions import TypedDict, Annotated
from typing import Optional, List, Dict

@dataclass(kw_only=True)
class MealPlanState:
    # User inputs
    location: str = field(default=None)  # User's location
    cuisine_preference: str = field(default=None)  # Preferred cuisine type
    dietary_restrictions: List[str] = field(default_factory=list)  # Any dietary restrictions
    flavor_preference: str = field(default=None)  # Preferred flavors
    
    # Recipe information
    recipe_name: str = field(default=None)  # Selected recipe name
    ingredients: List[Dict] = field(default_factory=list)  # List of ingredients with quantities
    instructions: List[str] = field(default_factory=list)  # Cooking instructions
    
    # Store recommendations
    store_recommendations: List[Dict] = field(default_factory=list)  # List of recommended stores
    
    # Search and research tracking
    web_research_results: Annotated[list, operator.add] = field(default_factory=list)
    sources_gathered: Annotated[list, operator.add] = field(default_factory=list)
    
    # Final output
    final_report: str = field(default=None)  # Formatted final report

@dataclass(kw_only=True)
class MealPlanStateInput:
    location: str = field(default=None)
    cuisine_preference: Optional[str] = field(default=None)
    dietary_restrictions: Optional[List[str]] = field(default_factory=list)
    flavor_preference: Optional[str] = field(default=None)

@dataclass(kw_only=True)
class MealPlanStateOutput:
    final_report: str = field(default=None)