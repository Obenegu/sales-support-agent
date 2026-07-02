sales_schema = [
    {
        "name": "calculate_total_product_cost",
        "description": "Calculate the total cost for a product.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "quantity": {"type": "number"},
            },
            "required": ["product_id", "quantity"],
        },
    }, 
    {
        "name": "process_payment",
        "description": "Process a customer payment by sending the cart to the payment service. Returns a checkout link.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Current session ID (used to load the real cart)"
                },
                "user_id": {
                    "type": "string",
                    "description": "ID of the user placing the order"
                },
                "order_id": {
                    "type": "string",
                    "description": "Unique order reference"
                },
                "amount": {
                    "type": "number",
                    "description": "Total amount to charge"
                }
            },
            "required": ["session_id", "user_id", "order_id", "amount"]
        }
    },
    {
        "name": "search_product",
        "description": "Used to Search products by name and also to get relevant details about the product like price description and availability.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The product name to search for. Pass the best keyword (e.g. 'pen', 'samsung'). The search handles plurals and partial matches automatically.",
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "add_item_to_order",
        "description": "Add an item to the user's cart in working memory. Cart is like a basket where the user adds items before checkout.",
        "parameters": {
            "type": "object",
            "properties": {
            "session_id": {
                "type": "string",
                "description": "Current session ID"
            },
            "user_id": {
                "type": "string",
                "description": "User ID"
            },
            "item": {
                "type": "object",
                "properties": {
                "name": { "type": "string" },
                "quantity": { "type": "string" },
                "price": { "type": "number" },
                "color": { "type": "string" }
                },
                "required": ["name", "quantity", "price", "color"]
            }
            },
            "required": ["session_id", "user_id", "item"]
        }
    },
    {
        "name": "remove_item_from_order",
        "description": "Remove an item from the user's cart",
        "parameters": {
            "type": "object",
            "properties": {
            "session_id": {
                "type": "string",
                "description": "Current session ID"
            },
            "user_id": {
                "type": "string",
                "description": "User ID"
            },
            "item_name": {
                "type": "string",
                "description": "Name of the item to remove"
            }
            },
            "required": ["session_id", "user_id", "item_name"]
        }
    },
    {
        "name": "generate_quote",
        "description": "Generate a customer quotation.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {"type": "string"},
                "product": {"type": "string"},
                "quantity": {"type": "number"},
            },
            "required": ["customer_name", "product"],
        },
    },
    {
        "name": "suggest_upsells",
        "description": "Suggest upsells based on the selected product.",
        "parameters": {
            "type": "object",
            "properties": {
                "product": {"type": "string"},
            },
            "required": ["product"],
        },
    },
]