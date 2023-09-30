#!/usr/bin/env python3

WRITEUP_TEMPLATE = [
    {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": "📚 Table of Contents"},
                }
            ],
        },
    },
    {
        "object": "block",
        "type": "table_of_contents",
        "table_of_contents": {},
    },
    {"object": "block", "type": "divider", "divider": {}},
    {
        "object": "block",
        "type": "heading_1",
        "heading_1": {
            "rich_text": [{"type": "text", "text": {"content": "🔎 Enumeration"}}]
        },
    },
    {
        "object": "block",
        "type": "code",
        "code": {
            "language": "php",
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": "$ nmap -sC -sV -oA nmap/initial $IP"},
                }
            ],
        },
    },
    {"object": "block", "type": "divider", "divider": {}},
    {
        "object": "block",
        "type": "heading_1",
        "heading_1": {
            "rich_text": [{"type": "text", "text": {"content": "💥 Exploitation"}}],
        },
    },
    {
        "object": "block",
        "type": "code",
        "code": {
            "language": "php",
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": "[...] gained foothold on the machine via command injection in the web application [...]"
                    },
                }
            ],
        },
    },
    {"object": "block", "type": "divider", "divider": {}},
    {
        "object": "block",
        "type": "heading_1",
        "heading_1": {
            "rich_text": [
                {"type": "text", "text": {"content": "#️⃣ Privilege Escalation"}}
            ]
        },
    },
    {
        "object": "block",
        "type": "code",
        "code": {
            "language": "php",
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": "[...] became root user by exploiting a vulnerable SUID binary [...]"
                    },
                }
            ],
        },
    },
    {"object": "block", "type": "divider", "divider": {}},
]
