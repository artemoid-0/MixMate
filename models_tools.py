from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Cocktail(Base):
    """
    Represents a cocktail with its main attributes.
    """
    __tablename__ = 'cocktails'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    alcoholic = Column(String, nullable=False)  # 'Alcoholic', 'Non alcoholic' or 'Optional
    category = Column(String, nullable=False)
    glass_type = Column(String)
    instruction = Column(Text)
    drink_thumbnail = Column(String)

    ingredients = relationship("CocktailIngredient", back_populates="cocktail", cascade="all, delete-orphan")

class CocktailIngredient(Base):
    """
    Represents an ingredient in a cocktail, linked via cocktail_id.
    """
    __tablename__ = 'cocktail_ingredients'

    id = Column(Integer, primary_key=True)
    cocktail_id = Column(Integer, ForeignKey('cocktails.id', ondelete="CASCADE"))
    ingredient = Column(String, nullable=False)
    measure = Column(String)

    cocktail = relationship("Cocktail", back_populates="ingredients")

class UserData(Base):
    """
    Stores user preferences and recent message history.
    """
    __tablename__ = 'user_data'

    user_id = Column(Integer, primary_key=True)  # User ID
    preferences = Column(JSONB, nullable=False, default={})  # JSONB field for storing preferences
    message_history = Column(JSONB, nullable=False, default=[])  # Stores the last N messages


tools = [
    {
        "type": "function",
        "function": {
            "name": "parse_cocktail_info_request",
            "description": "Fetch all names of the cocktails the user is interested in",
            "parameters": {
                "type": "object",
                "properties": {
                    "cocktail_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "description": "python list of all cocktails, mentioned by the user in the query."
                    }
                },
                "required": ["cocktail_names"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "parse_cocktail_recommendation_request",
            "description": "Recommend cocktails based on user preferences and provided criteria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "excluded_cocktail_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of cocktails the user wants to exclude from the results."
                    },
                    "ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of ingredients that the user wants to see in the cocktail."
                    },
                    "excluded_ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of ingredients the user wishes to exclude."
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Cocktail categories that the user is interested in, if explicitly mentioned (e.g., 'cocktail', 'shot')."
                    },
                    "excluded_categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Cocktail categories the user wants to exclude."
                    },
                    "alcohol_content": {
                        "type": "string",
                        "enum": ["alcoholic", "non alcoholic", "any"],
                        "description": "The alcohol content preference: 'alcoholic' for alcoholic drinks, 'non alcoholic' for non-alcoholic drinks, 'any' for no specific preference."
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "The maximum number of cocktails to return. If not specified, a default value is used."
                    }
                },
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "parse_cocktail_similar_request",
            "description": "Find cocktail similar to those mentioned by the user in the query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cocktails_like": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of cocktails the user wants to find similar to."
                    },
                    "excluded_cocktail_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of cocktails the user wants to exclude from the results."
                    },
                    "ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of ingredients, that the user wants to see in the cocktail."
                    },
                    "excluded_ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of ingredients the user wishes to exclude."
                    },
                    "categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Cocktail categories that the user is interested in, if explicitly mentioned (e.g. 'Cocktail', 'Shot')."
                    },
                    "excluded_categories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Cocktail categories the user wants to exclude."
                    },
                    "alcohol_content": {
                        "type": "string",
                        "enum": ["Alcoholic", "Non alcoholic", "Any"],
                        "description": "The alcohol content preference of the cocktail: 'Alcoholic' for alcoholic drinks, 'Non alcoholic' for non-alcoholic drinks, 'Any' for no specific preference."
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "The maximum number of cocktails to return. If not specified, a default value is used."
                    }
                }
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "update_user_preferences",
            "description": "Update user preferences based on their input. Adds new likes/dislikes and removes items that the user is no longer interested in.",
            "parameters": {
                "type": "object",
                "properties": {
                    "liked_cocktails": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of cocktail names that the user likes.",
                        "default": []
                    },
                    "disliked_cocktails": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of cocktail names that the user dislikes.",
                        "default": []
                    },
                    "liked_ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of ingredients that the user likes.",
                        "default": []
                    },
                    "disliked_ingredients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of ingredients that the user dislikes.",
                        "default": []
                    }
                }
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_user_preferences",
            "description": "Retrieve the user's current cocktail and ingredient preferences.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "clear_user_preferences",
            "description": "Clear all user preferences, removing all liked and disliked cocktails and ingredients.",
            "parameters": {
                "type": "object",
                "properties": {},
                "description": "This function does not require any parameters."
            }
        }
    }

]
