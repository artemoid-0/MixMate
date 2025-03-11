from main import update_user_preferences, clear_user_preferences, parse_cocktail_recommendation_request, parse_cocktail_similar_request

# update_user_preferences(user_id=1, liked_ingredients=["lime juice"])
# result = parse_cocktail_recommendation_request(user_id=1, ingredients=["sugar"], limit=5)
#
# for c in result:
#     print(c.id, c.name, [ing.ingredient for ing in c.ingredients])


result = parse_cocktail_similar_request(user_id=1, cocktails_like=["Margarita"])
print(result)
