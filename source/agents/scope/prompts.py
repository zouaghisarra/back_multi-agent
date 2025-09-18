clarify_with_user_prompt = """You are a legal research assistant.
Your task is to determine if the user's request is clear enough to proceed.

If not, ask a short, precise question to clarify.
If yes, confirm and verify.

Today's date is {date}.

<Conversation>
{messages}
</Conversation>

Respond using the provided JSON schema.
"""

transform_messages_prompt = """Based on the conversation, generate a precise research brief.

Include:
- The legal topic
- The country
- The type of sources needed (e.g., official codes, court rulings)

Today's date is {date}.

<Conversation>
{messages}
</Conversation>

Respond using the provided JSON schema.
"""