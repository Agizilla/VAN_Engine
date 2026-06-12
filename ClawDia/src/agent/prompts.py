SYSTEM_PROMPT = """You are ClawDia, an intelligent AI assistant running entirely offline. You help users with music production, audio analysis, coding, and general tasks.

You have access to tools you can call to interact with the system. When you need information or want to perform an action, use the appropriate tool.

Guidelines:
- Be concise and direct
- When asked about your capabilities, list your available tools
- If a tool returns an error, tell the user and suggest alternatives
- Use memory to remember user preferences and past conversations
- Use RAG when you need to look up documents or knowledge
- Keep responses under 3 paragraphs unless the user asks for detail

Your available tools are listed below. Call them when needed."""


TOOL_SCHEMAS = {
    "search_memory": {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Search past conversations and stored knowledge",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    "store_memory": {
        "type": "function",
        "function": {
            "name": "store_memory",
            "description": "Store a fact or piece of information in long-term memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The information to remember"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category (user_preference, fact, note, project)",
                        "enum": ["user_preference", "fact", "note", "project"]
                    }
                },
                "required": ["text", "category"]
            }
        }
    },
    "search_documents": {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Search ingested documents for relevant information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    },
    "list_skills": {
        "type": "function",
        "function": {
            "name": "list_skills",
            "description": "List all available skills and their capabilities",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by category (audio, vision, video, general)",
                        "default": ""
                    }
                }
            }
        }
    },
    "execute_skill": {
        "type": "function",
        "function": {
            "name": "execute_skill",
            "description": "Execute a specific skill by name with parameters",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_name": {
                        "type": "string",
                        "description": "Name of the skill to execute"
                    },
                    "params": {
                        "type": "object",
                        "description": "Parameters to pass to the skill",
                        "default": {}
                    }
                },
                "required": ["skill_name"]
            }
        }
    },
}
