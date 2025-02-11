import argparse
import asyncio
import os
from typing import Optional, List
from dataclasses import asdict

from dotenv import load_dotenv

from graph import graph
from state import MealPlanStateInput

async def run_meal_planner(
    location: str,
    cuisine: Optional[str] = None,
    restrictions: Optional[List[str]] = None,
    flavor: Optional[str] = None,
    model: Optional[str] = "gpt-4-0125-preview"
) -> str:
    """Run the meal planning agent.
    
    Args:
        location: User's location for store recommendations
        cuisine: Preferred cuisine type (optional)
        restrictions: List of dietary restrictions (optional)
        flavor: Preferred flavor profile (optional)
        model: The OpenAI model to use
    
    Returns:
        str: The final meal planning report
    """
    # Create the initial state
    config = {
        "configurable": {
            "model_name": model,
            "max_store_recommendations": 3,
            "include_price_estimates": True
        }
    }
    
    # Create input state
    input_state = MealPlanStateInput(
        location=location,
        cuisine_preference=cuisine,
        dietary_restrictions=restrictions or [],
        flavor_preference=flavor
    )
    
    # Run the graph
    result = await graph.ainvoke(
        asdict(input_state),
        config=config
    )
    
    return result["final_report"]

def save_to_markdown(report: str, location: str):
    """Save the meal planning report to a markdown file."""
    # Add timestamp
    from datetime import datetime
    timestamp = f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    
    # Combine content
    content = timestamp + report
    
    # Create filename from location
    filename = f"meal_plan_{location.lower().replace(' ', '_')}.md"
    
    # Save to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\nMeal plan saved to {filename}")

def main():
    # Load environment variables
    load_dotenv()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Get meal planning and grocery recommendations')
    parser.add_argument('location', type=str, help='Your location (city or zip code)')
    parser.add_argument('--cuisine', type=str, help='Preferred cuisine type')
    parser.add_argument('--restrictions', type=str, nargs='+', help='Dietary restrictions')
    parser.add_argument('--flavor', type=str, help='Preferred flavor profile')
    parser.add_argument('--model', type=str, default="gpt-4-0125-preview",
                      help='OpenAI model to use (default: gpt-4-0125-preview)')
    
    args = parser.parse_args()
    
    # Run the meal planner
    report = asyncio.run(run_meal_planner(
        location=args.location,
        cuisine=args.cuisine,
        restrictions=args.restrictions,
        flavor=args.flavor,
        model=args.model
    ))
    
    # Print the results to console
    print("\n" + "="*80)
    print("Meal Planning Report")
    print("="*80 + "\n")
    print(report)
    
    # Save to markdown file
    save_to_markdown(report, args.location)

if __name__ == "__main__":
    main() 