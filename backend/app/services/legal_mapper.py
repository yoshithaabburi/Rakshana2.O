# ============================================
# RAKSHANA 24/7 — Legal Mapper Service
# ============================================
# Maps incident types to applicable Indian cyber laws

def map_incident_to_laws(incident_type: str) -> list[dict]:
    """
    Map an incident type to applicable Indian cyber law sections.

    Returns a list of law references with section, act, and description.
    """

    LAW_MAP = {
        "stalking": [
            {
                "section": "354D",
                "act": "Indian Penal Code (IPC)",
                "title": "Stalking",
                "description": "Following or monitoring someone using electronic means",
                "punishment": "Up to 3 years (first offence), 5 years (repeat)",
            },
            {
                "section": "78",
                "act": "Bharatiya Nyaya Sanhita (BNS)",
                "title": "Stalking (New Law)",
                "description": "Updated anti-stalking provision under new criminal code",
                "punishment": "Up to 3 years + fine",
            },
        ],
        "morphed_image": [
            {
                "section": "66E",
                "act": "IT Act 2000",
                "title": "Privacy Violation",
                "description": "Capturing/publishing private images without consent",
                "punishment": "Up to 3 years + ₹2 lakh fine",
            },
            {
                "section": "67",
                "act": "IT Act 2000",
                "title": "Publishing Obscene Material",
                "description": "Transmitting obscene material in electronic form",
                "punishment": "Up to 5 years + ₹10 lakh fine (first offence)",
            },
            {
                "section": "67A",
                "act": "IT Act 2000",
                "title": "Sexually Explicit Content",
                "description": "Publishing sexually explicit material electronically",
                "punishment": "Up to 7 years + ₹10 lakh fine",
            },
        ],
        "harassment": [
            {
                "section": "354A",
                "act": "Indian Penal Code (IPC)",
                "title": "Sexual Harassment",
                "description": "Making sexually coloured remarks or sending unwanted sexual messages",
                "punishment": "Up to 3 years + fine",
            },
            {
                "section": "509",
                "act": "Indian Penal Code (IPC)",
                "title": "Insult to Modesty",
                "description": "Word, gesture or act intended to insult the modesty of a woman",
                "punishment": "Up to 3 years + fine",
            },
            {
                "section": "67",
                "act": "IT Act 2000",
                "title": "Obscene Electronic Content",
                "description": "Publishing obscene material online",
                "punishment": "Up to 5 years + ₹10 lakh fine",
            },
        ],
        "blackmail": [
            {
                "section": "384",
                "act": "Indian Penal Code (IPC)",
                "title": "Extortion",
                "description": "Putting any person in fear to dishonestly induce delivery of property",
                "punishment": "Up to 3 years + fine",
            },
            {
                "section": "385",
                "act": "Indian Penal Code (IPC)",
                "title": "Attempt to Extort",
                "description": "Putting a person in fear of injury for extortion",
                "punishment": "Up to 2 years + fine",
            },
            {
                "section": "506",
                "act": "Indian Penal Code (IPC)",
                "title": "Criminal Intimidation",
                "description": "Threatening a person with injury to person, reputation, or property",
                "punishment": "Up to 2 years + fine (up to 7 years for death/serious threats)",
            },
        ],
        "doxxing": [
            {
                "section": "66C",
                "act": "IT Act 2000",
                "title": "Identity Theft",
                "description": "Fraudulent use of electronic signature, password or unique ID",
                "punishment": "Up to 3 years + ₹1 lakh fine",
            },
            {
                "section": "72",
                "act": "IT Act 2000",
                "title": "Breach of Confidentiality and Privacy",
                "description": "Disclosing personal information obtained during lawful access",
                "punishment": "Up to 2 years + ₹1 lakh fine",
            },
            {
                "section": "43A",
                "act": "IT Act 2000",
                "title": "Compensation for Failure to Protect Data",
                "description": "Body corporate failing to protect sensitive personal data",
                "punishment": "Compensation to affected person",
            },
        ],
        "other": [
            {
                "section": "66",
                "act": "IT Act 2000",
                "title": "Computer Related Offences",
                "description": "Any dishonest or fraudulent act done with a computer",
                "punishment": "Up to 3 years + ₹5 lakh fine",
            },
        ],
    }

    return LAW_MAP.get(incident_type, LAW_MAP["other"])
