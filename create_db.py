import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models_tools import Base, Cocktail, CocktailIngredient

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Drop and recreate all tables (use with caution in production!)
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

# Initialize session
Session = sessionmaker(bind=engine)
session = Session()

# Load data from CSV
csv_file = "data/final_cocktails.csv"
df = pd.read_csv(csv_file)

# Insert cocktails and their ingredients
for _, row in df.iterrows():
    # Create a cocktail entry
    cocktail = Cocktail(
        name=row["name"],
        alcoholic=row["alcoholic"].lower() if isinstance(row["alcoholic"], str) else row["alcoholic"],
        category=row["category"].lower() if isinstance(row["category"], str) else row["category"],
        glass_type=row["glassType"].lower() if isinstance(row["glassType"], str) else row["glassType"],
        instruction=row["instructions"],
        drink_thumbnail=row["drinkThumbnail"]
    )
    session.add(cocktail)
    session.flush()  # Ensure we get the cocktail ID before committing

    # Add ingredients with their measures
    ingredients = eval(row["ingredients"])
    measures = eval(row["ingredientMeasures"])

    for ingredient, measure in zip(ingredients, measures):
        session.add(CocktailIngredient(
            cocktail_id=cocktail.id,
            ingredient=ingredient.lower() if isinstance(ingredient, str) else ingredient,
            measure=measure
        ))

# Commit all changes
session.commit()
