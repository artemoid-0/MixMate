import os
import random
import string

from dotenv import load_dotenv
from fastapi import Header, HTTPException
from sqlalchemy import create_engine, not_, func, or_
from sqlalchemy.orm import Session

from models_tools import *

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
MESSAGE_HISTORY_LIMIT = 5  # Number of user-bot message pairs to store

def parse_cocktail_info_request(user_id, cocktail_names: list):
    """
    Fetches cocktail details based on provided names.
    """
    cocktail_names = [string.capwords(name.strip()) for name in cocktail_names]
    with Session(engine) as session:
        query = session.query(Cocktail)
        query = query.filter(Cocktail.name.in_(cocktail_names))
        return query.all()

def parse_cocktail_recommendation_request(user_id,
                                          excluded_cocktail_names=None,
                                          ingredients=None,
                                          excluded_ingredients=None,
                                          categories=None,
                                          excluded_categories=None,
                                          alcohol_content=None,
                                          limit: int = 3):
    """
    Generates cocktail recommendations based on user preferences and filters.
    """
    with Session(engine) as session:
        query = session.query(Cocktail)

        # Retrieve user preferences
        user_preferences = session.query(UserData).filter_by(user_id=user_id).first()
        preferences = user_preferences.preferences if user_preferences else {}

        liked_cocktails = set(preferences.get("liked_cocktails", []))
        disliked_cocktails = set(preferences.get("disliked_cocktails", []))
        liked_ingredients = set(preferences.get("liked_ingredients", []))
        disliked_ingredients = set(preferences.get("disliked_ingredients", []))

        # Exclude disliked cocktails
        if disliked_cocktails:
            query = query.filter(not_(Cocktail.name.in_(disliked_cocktails)))

        # Exclude disliked ingredients unless they are explicitly required
        if excluded_ingredients:
            disliked_ingredients -= set(ingredients or [])
        if disliked_ingredients:
            query = query.filter(
                not_(
                    session.query(CocktailIngredient)
                    .filter(CocktailIngredient.cocktail_id == Cocktail.id)
                    .filter(CocktailIngredient.ingredient.in_(disliked_ingredients))
                    .exists()
                )
            )

        # Apply standard filters
        if excluded_cocktail_names:
            excluded_cocktail_names = [string.capwords(name.strip()) for name in excluded_cocktail_names]
            query = query.filter(not_(Cocktail.name.in_(excluded_cocktail_names)))

        if ingredients:
            ingredients = [ing.strip().lower() for ing in ingredients]
            query = query.filter(
                session.query(CocktailIngredient.cocktail_id)
                .filter(CocktailIngredient.cocktail_id == Cocktail.id)
                .filter(CocktailIngredient.ingredient.in_(ingredients))
                .group_by(CocktailIngredient.cocktail_id)
                .having(func.count(CocktailIngredient.ingredient) == len(ingredients))
                .exists()
            )

        if categories:
            categories = [cat.strip().lower() for cat in categories]
            query = query.filter(Cocktail.category.in_(categories))

        if excluded_categories:
            excluded_categories = [cat.strip().lower() for cat in excluded_categories]
            query = query.filter(not_(Cocktail.category.in_(excluded_categories)))

        if alcohol_content:
            alcohol_content = alcohol_content.strip().lower()
            if alcohol_content == "alcoholic":
                query = query.filter(
                    or_(Cocktail.alcoholic == "alcoholic", Cocktail.alcoholic == "optional alcohol")
                )
            elif alcohol_content == "non alcoholic":
                query = query.filter(
                    or_(Cocktail.alcoholic == "non alcoholic", Cocktail.alcoholic == "optional alcohol")
                )

        cocktails = query.all()

        # Categorize based on user preferences
        favorite_cocktails = [c for c in cocktails if c.name in liked_cocktails]
        cocktails_with_liked_ingredients = sorted(
            [c for c in cocktails if c.name not in liked_cocktails],
            key=lambda c: (
                sum(1 for ing in c.ingredients if ing.ingredient in liked_ingredients),
                random.random()
            ),
            reverse=True
        )

        other_cocktails = [c for c in cocktails if c.name not in liked_cocktails and c not in cocktails_with_liked_ingredients]
        random.shuffle(other_cocktails)

        # Combine groups and return the top results
        sorted_cocktails = favorite_cocktails + cocktails_with_liked_ingredients + other_cocktails
        return sorted_cocktails[:limit]


def parse_cocktail_similar_request(user_id,
                                   cocktails_like,
                                   excluded_cocktail_names=None,
                                   ingredients=None,
                                   excluded_ingredients=None,
                                   categories=None,
                                   excluded_categories=None,
                                   alcohol_content=None,
                                   limit: int = 3):
    # Function to get all ingredients of a cocktail
    def get_ingredients_for_cocktail(cocktail_id):
        with Session(engine) as session:
            return set(
                ingredient.ingredient for ingredient in session.query(CocktailIngredient)
                .filter(CocktailIngredient.cocktail_id == cocktail_id).all()
            )

    # Function to get the categories of a cocktail
    def get_categories_for_cocktail(cocktail_id):
        with Session(engine) as session:
            return set(
                category.category for category in session.query(Cocktail)
                .filter(Cocktail.id == cocktail_id).all()
            )

    # Function to compute Jaccard Similarity for two sets
    def jaccard_similarity(set1, set2):
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union != 0 else 0

    cocktails_like = [string.capwords(name) for name in cocktails_like]
    with Session(engine) as session:
        # Convert cocktail names to Cocktail objects
        cocktails_like_objs = session.query(Cocktail).filter(Cocktail.name.in_(cocktails_like)).all()

        if not cocktails_like_objs:
            return []  # If no initial cocktails are found, return an empty list

        # Add cocktails_like to the list of excluded cocktails
        if excluded_cocktail_names:
            excluded_cocktail_names.extend([c.name for c in cocktails_like_objs])
        else:
            excluded_cocktail_names = [c.name for c in cocktails_like_objs]

        # Filter the cocktail database based on strict criteria
        filtered_cocktails = parse_cocktail_recommendation_request(
            user_id,
            excluded_cocktail_names,
            ingredients,
            excluded_ingredients,
            categories,
            excluded_categories,
            alcohol_content,
            limit=None  # Get all, not just 3 random ones
        )

        if not filtered_cocktails:
            return []

        # Get ingredients and categories for each initial cocktail
        cocktails_like_data = []
        for cocktail in cocktails_like_objs:
            cocktails_like_data.append({
                "id": cocktail.id,
                "ingredients": get_ingredients_for_cocktail(cocktail.id),
                "categories": get_categories_for_cocktail(cocktail.id)
            })

        # Compute similarity between remaining cocktails and cocktails_like
        similarity_scores = []
        for candidate in filtered_cocktails:
            candidate_ingredients = get_ingredients_for_cocktail(candidate.id)
            candidate_categories = get_categories_for_cocktail(candidate.id)

            # Average Jaccard Similarity based on ingredients and categories
            similarities = [
                (jaccard_similarity(candidate_ingredients, ref["ingredients"]) +
                 jaccard_similarity(candidate_categories, ref["categories"])) / 2
                for ref in cocktails_like_data
            ]

            max_similarity = max(similarities) if similarities else 0
            similarity_scores.append((candidate, max_similarity))

        # Sort by descending similarity and take the top 3
        similarity_scores.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in similarity_scores[:3]]


def update_user_preferences(user_id, liked_cocktails=None, disliked_cocktails=None, liked_ingredients=None, disliked_ingredients=None):
    # Ensure parameters are not None
    liked_cocktails = set(string.capwords(name.strip()) for name in (liked_cocktails or []))
    disliked_cocktails = set(string.capwords(name.strip()) for name in (disliked_cocktails or []))
    liked_ingredients = set(ing.strip().lower() for ing in (liked_ingredients or []))
    disliked_ingredients = set(ing.strip().lower() for ing in (disliked_ingredients or []))

    with Session(autoflush=False, bind=engine) as session:
        # Retrieve current user preferences
        user_preferences = session.query(UserData).filter_by(user_id=user_id).first()

        if not user_preferences:
            user_preferences = UserData(user_id=user_id, preferences={})
            session.add(user_preferences)

        # Load or initialize preferences
        preferences = user_preferences.preferences or {}

        # Remove conflicts
        liked_cocktails -= disliked_cocktails
        disliked_cocktails -= liked_cocktails
        liked_ingredients -= disliked_ingredients
        disliked_ingredients -= liked_ingredients

        # Update preference lists
        preferences.setdefault("liked_cocktails", [])
        preferences.setdefault("disliked_cocktails", [])
        preferences.setdefault("liked_ingredients", [])
        preferences.setdefault("disliked_ingredients", [])

        # Update preferences
        new_preferences = {
            "liked_cocktails": list(set(preferences["liked_cocktails"]).union(liked_cocktails) - disliked_cocktails),
            "disliked_cocktails": list(set(preferences["disliked_cocktails"]).union(disliked_cocktails) - liked_cocktails),
            "liked_ingredients": list(set(preferences["liked_ingredients"]).union(liked_ingredients) - disliked_ingredients),
            "disliked_ingredients": list(set(preferences["disliked_ingredients"]).union(disliked_ingredients) - liked_ingredients)
        }

        # Explicitly update the JSONB field
        user_preferences.preferences = new_preferences
        session.commit()


def get_user_id(x_user_id: str = Header(...)) -> int:
    if not x_user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    return int(x_user_id)


def get_user_preferences(user_id):
    with Session(engine) as session:
        user_preferences = session.query(UserData).filter_by(user_id=user_id).first()

        if not user_preferences:
            return {
                "liked_cocktails": [],
                "disliked_cocktails": [],
                "liked_ingredients": [],
                "disliked_ingredients": []
            }

        preferences = user_preferences.preferences

        return {
            "liked_cocktails": [string.capwords(name.strip()) for name in preferences.get("liked_cocktails", [])],
            "disliked_cocktails": [string.capwords(name.strip()) for name in preferences.get("disliked_cocktails", [])],
            "liked_ingredients": [ing.strip().lower() for ing in preferences.get("liked_ingredients", [])],
            "disliked_ingredients": [ing.strip().lower() for ing in preferences.get("disliked_ingredients", [])]
        }


def clear_user_preferences(user_id):
    with Session(engine) as session:
        user_preferences = session.query(UserData).filter_by(user_id=user_id).first()

        if user_preferences:
            user_preferences.preferences = {
                "liked_cocktails": [],
                "disliked_cocktails": [],
                "liked_ingredients": [],
                "disliked_ingredients": []
            }
            session.commit()


def update_message_history(session: Session, user_id: int, user_message: str, bot_response: str):
    user_data = session.query(UserData).filter_by(user_id=user_id).first()
    if not user_data:
        user_data = UserData(user_id=user_id, message_history=[])
        session.add(user_data)

    # Add new user message and bot response
    user_data.message_history.append({"user": user_message, "bot": bot_response})

    # Limit message history size
    if len(user_data.message_history) > MESSAGE_HISTORY_LIMIT:
        user_data.message_history = user_data.message_history[-MESSAGE_HISTORY_LIMIT:]

    session.commit()
