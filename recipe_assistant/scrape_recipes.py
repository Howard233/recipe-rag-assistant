import requests
import pandas as pd
from bs4 import BeautifulSoup


# parse recipe
def get_recipe_description(soup):
    description = soup.find("div", class_="recipe-description paragraph").get_text()
    return description


def get_ratings(soup):
    rating_div = soup.find("div", class_="rating")
    review_tag = rating_div.find_next()
    aria_label = review_tag["aria-label"].strip()
    return aria_label


def get_ready_in(soup):
    ready_in_miniutes = soup.find("dt", string="Ready In:").find_next_sibling("dd")
    ready_in_miniutes = ready_in_miniutes.get_text(strip=True)
    return ready_in_miniutes


def get_directions(soup):
    ul = soup.find("ul", class_="direction-list svelte-ar8gac")
    directions = [li.get_text(strip=True) for li in ul.find_all("li")]
    return directions


def get_ingredients(soup):
    ul = soup.find("ul", class_="ingredient-list svelte-ar8gac")

    ingredients = []
    for li in ul.find_all("li"):
        # If it's a section heading
        heading_tag = li.find("h4", class_="ingredient-heading")
        if heading_tag:
            # Section heading
            heading_text = heading_tag.get_text(strip=True)
            ingredients.append(f"=== {heading_text} ===")

        qty_tag = li.find("span", class_="ingredient-quantity svelte-ar8gac")
        text_tag = li.find("span", class_="ingredient-text svelte-ar8gac")

        if qty_tag and text_tag:
            quantity = qty_tag.get_text(strip=True)
            text = text_tag.get_text(" ", strip=True)
            ingredients.append(f"{quantity} {text}")
    return ingredients


if __name__ == "__main__":
    # get recipes urls
    url = r"https://www.food.com/ideas/all-time-best-dinner-recipes-6009?ref=nav"

    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    recipes = [
        {"recipe_name": r.getText(), "recipe_link": r.a["href"]}
        for r in soup.find_all("h2", class_="title")
    ]

    # get recipe data
    for i, recipe in enumerate(recipes):
        recipe_name = recipe["recipe_name"]
        recipe_link = recipe["recipe_link"]

        # set id
        recipe["recipe_id"] = i

        print(f"Parsing {recipe_name}")
        response = requests.get(recipe_link)
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # description
        print("Getting description")
        recipe["recipe_description"] = get_recipe_description(soup)
        recipe["recipe_description"] = recipe["recipe_description"].strip()

        # rating
        print("Getting ratings")
        recipe["ratings"] = get_ratings(soup)
        recipe["ratings"] = recipe["ratings"].strip()

        # ready in
        print("Getting ready-in")
        recipe["ready-in"] = get_ready_in(soup)
        recipe["ready-in"] = recipe["ready-in"].strip()

        # directions
        recipe["directions"] = get_directions(soup)

        # ingredients
        recipe["ingredients"] = get_ingredients(soup)
        print()

    df_recipes = pd.DataFrame(recipes)
    df_recipes.to_csv("../data/recipes.csv", index=False)
