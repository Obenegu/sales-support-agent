from typing import Optional


# -------------------------------------------
# 1. CALCULATE PRICING
# -------------------------------------------



class Sales_Tools():
    def __init__(self, products, upsells):
        self.products = products
        self.upsells = upsells


    def calculate_price(self, product_name: str, quantity: int = 1) -> Optional[float]:
        product_name = product_name.lower()

        if product_name not in self.products:
            return f"Sorry We do not have '{product_name}' at the moment"

        return self.products[product_name] * quantity


    # -------------------------------------------
    # 2. GENERATE QUOTATION
    # -------------------------------------------

    def generate_quote(self, customer_name: str, product: str, quantity: int = 1) -> str:
        price = self.calculate_price(product, quantity)

        if price is None:
            return f"Sorry, I couldn’t find pricing for '{product}'."

        return (
            f"Quotation for {customer_name}\n"
            f"Product: {product}\n"
            f"Quantity: {quantity}\n"
            f"Total Price: ${price}\n"
            f"Thank you for choosing us!"
        )


    # -------------------------------------------
    # 3. SUGGEST UPSELLS
    # -------------------------------------------

   


    def suggest_upsells(self, product: str) -> str:
        product = product.lower()

        if product in self.upsells:
            items = ", ".join(self.upsells[product])
            return f"Customers who buy a {product} also consider: {items}."

        return "No upsells available."
    

    # -------------------------------------------
    #  SALES QUERY
    # -------------------------------------------



    def handle_sales_query(query: str):
        # Example: pretend we pull product info from a DB
        product_catalog = {
            "iphone 15": {"price": 999, "stock": 12},
            "samsung s24": {"price": 899, "stock": 8},
            "macbook air": {"price": 1299, "stock": 5},
        }

        query_lower = query.lower()
        for product, data in product_catalog.items():
            if product in query_lower:
                return {
                    "product": product,
                    "price": data["price"],
                    "stock": data["stock"],
                    "message": f"{product} is available for ${data['price']} and we have {data['stock']} in stock."
                }

        return {"message": "Sorry, I couldn’t find that product."}
    

    # -------------------------------------------
    #  SALES PERSONA
    # -------------------------------------------

    SALES_PERSONA = """

    You are a Calm Trust-Builder Sales Assistant.

Your personality and communication style:
- Speak in a warm, reassuring, professional tone.
- Never pressure the user. Instead, guide them confidently.
- Provide clarity, confidence, and stability.
- Focus on trust, expertise, and making the user feel understood.
- Use simple, smooth, non-aggressive language.
- Never sound desperate or salesy.

Your persuasion style:
- Lead with value, not hype.
- Show how the solution reduces stress, risk, or uncertainty for the user.
- Use micro-commitments (small confirmations that build momentum).
- Reinforce that the user is making a smart, safe choice.
- Always end responses with a gentle question to move the conversation forward.
- Offer help, not pressure.

Your emotional tone:
- Calm confidence.
- Quiet authority.
- Zero-stress communication.
- Empathy > urgency.
- “You’re in good hands” energy.

Examples of your tone:
- “Here’s what I recommend based on what you’ve shared…”
- “If you’d like, I can take care of that for you.”
- “No rush — whenever you’re ready, I can prepare everything.”
- “Most clients choose this option because it gives the best long-term results.”

Forbidden behaviors:
- No aggressive closing.
- No overwhelming enthusiasm.
- No “sales hype”.
- No guilt-tripping or pressure.
- No emojis unless the user uses them.

Your mission:
Make the user feel safe, understood, and confident — so buying becomes the natural next step.


"""
