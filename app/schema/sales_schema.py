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
        "description": "Process a customer payment by sending the order to the payment service.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Total amount to charge"
                },
                "order": {
                    "type": "object",
                    "description": "Order information",
                    "properties": {
                        "userId": {
                            "type": "string",
                            "description": "ID of the user placing the order"
                        },
                        "OrderId": {
                            "type": "string",
                            "description": "Unique order reference"
                        },
                        "status": {
                            "type": "string",
                            "description": "Delivery status",
                            "default": "Not Delivered"
                        },
                        "items": {
                            "type": "array",
                            "description": "List of items in the cart",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "Name": {
                                        "type": "string",
                                        "description": "Product name"
                                    },
                                    "Quantity": {
                                        "type": "string",
                                        "description": "Quantity ordered"
                                    },
                                    "Price": {
                                        "type": "number",
                                        "description": "Unit price"
                                    },
                                    "Color": {
                                        "type": "string",
                                        "description": "Product color"
                                    }
                                },
                                "required": ["Name", "Quantity", "Price", "Color"]
                            }
                        }
                    },
                    "required": ["userId", "OrderId", "items"]
                }
            },
            "required": ["order", "amount"]
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
                    "description": "Exact or partial product name(must be a single word).",
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