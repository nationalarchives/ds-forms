from app.forms.models import FormFlow
from app.forms.parts import (
    AddressForm,
    PizzaBrand,
    PizzaOrChocolate,
    PizzaToppings,
    TypeOfChocolate,
)

# Put everything together in a FormPages instance so we can handle all the logic
example_form_flow = FormFlow(slug="example")

# Set up all the required pages
pizza_or_chocolate = example_form_flow.create_starting_page(
    name="Pizza or Chocolate", slug="pizza-or-chocolate", form=PizzaOrChocolate
)
neither_page = example_form_flow.create_page(
    name="Neither",
    slug="neither",
    description="You selected neither pizza nor chocolate.",
    template="forms/example/neither.html",
)
pizza_topping = example_form_flow.create_page(
    name="Pizza toppings", slug="pizza-topping", form=PizzaToppings
)
pizza_brand = example_form_flow.create_page(
    name="Pizza brand", slug="pizza-brand", form=PizzaBrand
)
type_of_chocolate = example_form_flow.create_page(
    name="Type of Chocolate", slug="type-of-chocolate", form=TypeOfChocolate
)
address = example_form_flow.create_page(
    name="Enter your address",
    slug="address",
    description="We need this to deliver your pizza or chocolate.",
    form=AddressForm,
)
final_page = example_form_flow.create_page(
    name="Final Page",
    slug="final-page",
    description="This is the final page of the flow.",
    template="forms/final.html",
)

# Handle the flow logic for different options
pizza_or_chocolate.redirect_when_complete(
    page=pizza_topping,
    when=("food", "pizza"),
).redirect_when_complete(
    page=type_of_chocolate,
    when=("food", "chocolate"),
).redirect_when_complete(
    page=neither_page,
    when=("food", "neither"),
).redirect_when_complete(
    url="https://www.reddit.com/r/catpictures/",
    when=("food", "cats"),
)

# Require certain responses before proceeding else redirect to that page
pizza_topping.require_response(
    pizza_or_chocolate, "food", "pizza"
).redirect_when_complete(page=pizza_brand)
type_of_chocolate.require_response(
    pizza_or_chocolate, "food", "chocolate"
).redirect_when_complete(page=address)

# Require the completion of previous pages
pizza_brand.require_completion_of(pizza_topping).redirect_when_complete(
    url="https://www.dominos.co.uk/",
    condition=lambda form_data: form_data.get("brand") != "dominos",
).redirect_when_complete(page=address)

address.require_completion_of_any(
    [pizza_brand, type_of_chocolate], pizza_or_chocolate
).redirect_when_complete(page=final_page)

# Require completion of any of the previous pages
final_page.require_completion_of_any(
    [pizza_brand, type_of_chocolate], pizza_or_chocolate
)

forms = {
    "example": example_form_flow,
}
