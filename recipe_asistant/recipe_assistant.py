# -*- coding: utf-8 -*-
"""Recipe Assistant - An AI-powered agent for personalized recipe recommendations.

This module implements a LangGraph-based conversational agent that helps users find
recipes based on their preferences through iterative refinement with human-in-the-loop feedback.
"""

import logging
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from IPython.display import Image, display
from langchain.schema import SystemMessage
from langchain.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel, Field, field_validator

# Configuration constants
MAX_USER_INPUT_LENGTH = 1000
MAX_SEARCH_RESULTS = 3
DEFAULT_MODEL = "gpt-4o-mini-2024-07-18"
DEFAULT_TEMPERATURE = 0

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_api_keys() -> None:
    """Load and validate required API keys from environment.

    Raises:
        EnvironmentError: If required API keys are missing.
    """
    load_dotenv()
    required_keys = ["OPENAI_API_KEY", "TAVILY_API_KEY"]
    missing = [key for key in required_keys if not os.environ.get(key)]
    if missing:
        raise EnvironmentError(
            f"Missing required API keys: {', '.join(missing)}. "
            f"Please ensure these are set in your .env file."
        )
    logger.info("API keys loaded successfully")


def sanitize_user_input(text: str, max_length: int = MAX_USER_INPUT_LENGTH) -> str:
    """Sanitize user input to prevent prompt injection and ensure validity.

    Args:
        text: The user input text to sanitize.
        max_length: Maximum allowed length for the input.

    Returns:
        Sanitized text string.

    Raises:
        ValueError: If input is empty or exceeds maximum length.
    """
    if not text or not text.strip():
        raise ValueError("Input cannot be empty")
    if len(text) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length} characters")
    return text.strip()


def sanitize_web_content(content: str, max_length: int = 2000) -> str:
    """Sanitize web search content before using in prompts.

    Args:
        content: Web content to sanitize.
        max_length: Maximum allowed length for content.

    Returns:
        Sanitized content string.
    """
    if not content:
        return ""
    sanitized = content.strip()[:max_length]
    return sanitized


# Load API keys at module initialization
load_api_keys()

# Initialize AI model and search tool
try:
    llm = ChatOpenAI(model=DEFAULT_MODEL, temperature=DEFAULT_TEMPERATURE)
    tavily_search = TavilySearchResults(max_results=MAX_SEARCH_RESULTS)
    logger.info(f"Initialized LLM with model: {DEFAULT_MODEL}")
except Exception as e:
    logger.error(f"Failed to initialize AI services: {e}")
    raise


class SearchQuery(BaseModel):
    """Search query model for retrieval."""

    search_query: str = Field(None, description="Search query for retrieval.")


class RecipeState(MessagesState):
    """State model for the recipe assistant workflow."""

    query: str  # The search query
    recipes: List[Dict]  # List of found recipes
    key_features: List[str]  # Extracted key features from recipes
    recipes_index: int  # Index of selected recipe


class QueryTranslator:
    """Transforms human messages into structured web queries using LLM."""

    @staticmethod
    def translate(state: RecipeState) -> RecipeState:
        """Translate conversation into optimized search query.

        Args:
            state: Current recipe state.

        Returns:
            Updated state with search query.
        """
        logger.info("Starting query translation")
        logger.debug(f"Current state: {state}")

        search_instructions = SystemMessage(
            content="""You will be given a conversation between a user and assistant about recipe preferences.

Your task is to generate a concise and well-structured query for web search retrieval.

Instructions:
1. Analyze the conversation carefully.
2. Identify key elements such as:
   - Main ingredients (e.g., tofu, noodles)
   - Cooking styles (e.g., Asian, grilled)
   - Dietary restrictions (e.g., allergies, missing ingredients)
   - Dish preferences (e.g., avoid soups, prefer stir-fry)
3. Identify unwanted ingredients/elements or cooking styles
4. Construct a precise search query that includes only the essential elements for finding the best recipe.

Example:
Input: "Bring me an Asian-style recipe for noodles with tofu. I don't like onion."
Output: "Asian-style tofu noodle recipe without onions"

The query should be:
- Concise and free of unnecessary words
- Optimized for retrieving relevant web results
- Structured naturally for a search engine

Generate only the search query, nothing else."""
        )

        logger.debug(f"Search instructions: {search_instructions}")
        conversation_parts = [f"User:{m.content}" for m in state["messages"]]
        conversation_text = "\n".join(conversation_parts)
        conversation_text = (
            "**Input Conversation:**\n" + conversation_text + "\n\nSearch query:"
        )
        conversation_input = HumanMessage(content=conversation_text)

        logger.debug(f"Prompt: {conversation_parts}")

        try:
            search_query = llm.invoke([search_instructions, conversation_input])
            state["query"] = search_query.content
            logger.info(f"Generated search query: {search_query.content}")
        except Exception as e:
            logger.error(f"Failed to translate query: {e}")
            raise RuntimeError(f"Query translation failed: {str(e)}") from e

        logger.debug(f"Updated state: {state}")
        logger.info("Query translation completed")
        return state


class RecipeRetriever:
    """Retrieves recipes using Tavily search."""

    @staticmethod
    def retrieve(state: RecipeState) -> RecipeState:
        """Retrieve recipes from web search.

        Args:
            state: Current recipe state with search query.

        Returns:
            Updated state with retrieved recipes.
        """
        logger.info("Starting recipe retrieval")
        logger.debug(f"Current state: {state}")

        query = state.get("query")
        if not query:
            raise ValueError("No search query provided in state")

        logger.info(f"Searching for: {query}")

        try:
            search_docs = tavily_search.run(query)
            logger.debug(f"Search results: {search_docs}")
        except Exception as e:
            logger.error(f"Tavily search failed for query '{query}': {e}")
            raise RuntimeError(f"Recipe search failed: {str(e)}") from e

        formatted_search_recipes = [
            {
                "name": doc.get("title", "Unknown Dish"),
                "url": doc["url"],
                "content": sanitize_web_content(doc.get("content", "")),
            }
            for doc in search_docs
        ]

        logger.info(f"Retrieved {len(formatted_search_recipes)} recipes")
        logger.debug(f"Formatted recipes: {formatted_search_recipes}")

        state["recipes"] = formatted_search_recipes
        logger.debug(f"Updated state: {state}")
        logger.info("Recipe retrieval completed")

        return state


class ResponseRecipeKeyFeatures(BaseModel):
    """Response model for recipe key features."""

    results: List[str]


class RecipeKeyFeatures:
    """Extracts key features from the retrieved recipes."""

    @staticmethod
    def extract(state: RecipeState) -> RecipeState:
        """Extract key features from recipes.

        Args:
            state: Current recipe state with retrieved recipes.

        Returns:
            Updated state with extracted key features.
        """
        logger.info("Starting key feature extraction")

        if not state.get("recipes"):
            raise ValueError("No recipes found in state for feature extraction")

        system_message = SystemMessage(
            content="""You will receive the top 3 recipes from a web search. 

Extract key information for each recipe and format it as a concise summary string.

For each recipe, include:
- Dish name
- Key ingredients (3-4 most important ones)
- Cooking style/cuisine type

Format each recipe as a single descriptive string that captures the essence of the dish.

Example output format:
["Spicy Thai Tofu Pad Thai - Key ingredients: rice noodles, firm tofu, tamarind, fish sauce - Thai stir-fry",
 "Asian Sesame Tofu Noodle Bowl - Key ingredients: udon noodles, silken tofu, sesame oil, soy sauce - Japanese-style bowl",
 "Vietnamese Pho with Tofu - Key ingredients: rice noodles, vegetable broth, tofu, herbs - Vietnamese soup"]

Focus on the most distinctive features that would help a user choose between recipes."""
        )

        formatted_docs = "\n\n".join(
            [
                f"Recipe: {doc['name']}\nContent: {doc['content']}"
                for doc in state["recipes"]
            ]
        )

        try:
            structured_llm = llm.with_structured_output(ResponseRecipeKeyFeatures)
            key_features = structured_llm.invoke(
                [system_message, HumanMessage(content=formatted_docs)]
            )
            state["key_features"] = key_features.results
            logger.info(f"Extracted {len(key_features.results)} key features")
            logger.debug(f"Key features: {key_features.results}")
        except Exception as e:
            logger.error(f"Failed to extract key features: {e}")
            raise RuntimeError(f"Feature extraction failed: {str(e)}") from e

        logger.debug(f"Updated state: {state}")
        logger.info("Key feature extraction completed")
        return state


class Satisfaction:
    """Determines if user is satisfied with recipe selection."""

    @staticmethod
    def recipe_satisfaction(state: RecipeState) -> str:
        """Check if user selected a recipe or needs new search.

        Args:
            state: Current recipe state.

        Returns:
            Next node to transition to ('translate_query' or END).
        """
        logger.info("Checking recipe satisfaction")

        if state["recipes_index"] == -1:
            logger.info("User not satisfied, retrying search")
            return "translate_query"
        else:
            selected_recipe = state["recipes"][state["recipes_index"]]
            logger.info(f"User selected recipe: {selected_recipe['name']}")
            logger.info("Here is your desired recipe - Bon Appétit!")
            logger.info(f"Recipe details: {selected_recipe}")
            return END


class HumanSelection(BaseModel):
    """Model for human feedback on recipe selection."""

    like: Optional[int] = Field(
        None, description="Index of the liked recipe (0, 1, or 2). Null if none liked."
    )
    dislike: Optional[str] = Field(
        None,
        description="Explanation of why all recipes were disliked. Null if a recipe was liked.",
    )

    @field_validator("like", mode="before")
    @classmethod
    def validate_and_convert_like(cls, value: Optional[str | int]) -> Optional[int]:
        """Validate and convert like field to integer.

        Args:
            value: The value to validate.

        Returns:
            Validated integer or None.

        Raises:
            ValueError: If value is not 0, 1, 2, or None.
        """
        if value is None:
            return None
        if isinstance(value, str) and value.isdigit():
            value = int(value)
        if value not in {0, 1, 2}:
            raise ValueError("like must be either 0, 1, 2, or None")
        return value

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": [
                {"like": 1, "dislike": None},
                {"like": None, "dislike": "I prefer vegan options."},
                {"like": "2", "dislike": None},
            ]
        }


class HumanFeedback:
    """Allows the user to refine results by providing feedback using LLM interpretation."""

    @staticmethod
    def refine(state: RecipeState) -> RecipeState:
        """Collect and process human feedback on recipe options.

        Args:
            state: Current recipe state with key features.

        Returns:
            Updated state based on user feedback.
        """
        logger.info("Starting human feedback collection")

        user_feedback = interrupt(
            "Did you like any of the options? If so, which dish did you prefer? "
            "If not, please let us know why and what changes you would suggest"
        )
        logger.info(f"Received user feedback: {user_feedback}")

        try:
            # Sanitize user feedback
            sanitized_feedback = sanitize_user_input(str(user_feedback))
        except ValueError as e:
            logger.error(f"Invalid user input: {e}")
            raise

        # Validate we have key features
        if not state.get("key_features") or len(state["key_features"]) < 3:
            raise ValueError(
                "Insufficient key features in state for feedback processing"
            )

        # LLM interprets the feedback
        system_message = SystemMessage(
            content=f"""Analyze the user's feedback on these recipe options:

Recipe 0: {state["key_features"][0]}
Recipe 1: {state["key_features"][1]} 
Recipe 2: {state["key_features"][2]}

User feedback: {sanitized_feedback}

Task: Determine if the user likes a specific recipe or dislikes all options.

If the user likes a specific recipe:
- Identify which recipe they're referring to (0, 1, or 2)
- Return the index number in the "like" field
- Set "dislike" to null

If the user dislikes all recipes:
- Analyze their reasoning to understand what they want instead
- Summarize their preferences, restrictions, or requirements for a new search
- Set "like" to null
- Put the summary in the "dislike" field

Return format:
- For liked recipe: {{"like": index_number, "dislike": null}}
- For disliked all: {{"like": null, "dislike": "summary of what they want instead"}}

Only one field (like or dislike) can be non-null."""
        )

        logger.debug("Processing feedback with LLM")

        try:
            structured_llm = llm.with_structured_output(HumanSelection)
            logger.debug(f"Prompt: {system_message}")

            classification = structured_llm.invoke([system_message])
            logger.debug(f"LLM classification: {classification}")
        except Exception as e:
            logger.error(f"Failed to process user feedback: {e}")
            raise RuntimeError(f"Feedback processing failed: {str(e)}") from e

        logger.info("Feedback processed successfully")

        if classification.like is not None:
            # Validate recipe index
            if classification.like not in {0, 1, 2}:
                raise ValueError(f"Invalid recipe index: {classification.like}")
            if classification.like >= len(state["recipes"]):
                raise ValueError(f"Recipe index {classification.like} out of bounds")

            logger.info(f"User liked recipe at index {classification.like}")
            state["recipes_index"] = classification.like
            return state
        else:
            logger.info("User disliked all recipes, refining search")
            state["messages"] = [HumanMessage(content=classification.dislike)]
            return state


# Build the state graph
builder = StateGraph(RecipeState)

builder.add_node("translate_query", QueryTranslator.translate)
builder.add_node("retrieve_recipes", RecipeRetriever.retrieve)
builder.add_node("extract_key_features", RecipeKeyFeatures.extract)
builder.add_node("human_feedback", HumanFeedback.refine)

builder.add_edge(START, "translate_query")
builder.add_edge("translate_query", "retrieve_recipes")
builder.add_edge("retrieve_recipes", "extract_key_features")
builder.add_edge("extract_key_features", "human_feedback")

builder.add_conditional_edges(
    "human_feedback", Satisfaction.recipe_satisfaction, ["translate_query", END]
)

builder.executor = builder.compile()

# Compile graph with memory
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)

# Display graph visualization
try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception as e:
    logger.warning(f"Could not display graph visualization: {e}")
