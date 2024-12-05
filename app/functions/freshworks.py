create_contact = {
    "name": "freshwork_create_contact",
    "description": "A function to create a contact in the Freshworks CRM using user details such as name and mobile number.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The name of the user to be added as a contact in Freshworks CRM.",
            },
            "mobile_number": {
                "type": "string",
                "description": "The mobile number of the user to be added as a contact in Freshworks CRM.",
            },
        },
        "required": ["name", "mobile_number"],
    },
}
