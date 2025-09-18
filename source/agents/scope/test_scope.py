# test_scope_agent.py
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import json


console = Console()

def show_prompt(prompt_text: str, title: str = "Prompt", border_style: str = "blue"):
    formatted_text = Text(prompt_text)
    formatted_text.highlight_regex(r'<[^>]+>', style="bold blue")
    formatted_text.highlight_regex(r'##[^#\n]+', style="bold magenta")
    formatted_text.highlight_regex(r'###[^#\n]+', style="bold cyan")
    console.print(Panel(formatted_text, title=f"[bold green]{title}[/bold green]", border_style=border_style, padding=(1, 2)))

def format_messages(messages):
    for m in messages:
        msg_type = m.__class__.__name__.replace('Message', '')
        content = format_message_content(m)
        style = "blue" if msg_type == "Human" else "green" if msg_type == "AI" else "yellow"
        title_icon = "🧑" if msg_type == "Human" else "🤖" if msg_type == "AI" else "🔧"
        console.print(Panel(content, title=f"{title_icon} {msg_type}", border_style=style))

def format_message_content(message):
    parts = []
    tool_calls_processed = False

    if isinstance(message.content, str):
        parts.append(message.content)
    elif isinstance(message.content, list):
        for item in message.content:
            if item.get('type') == 'text':
                parts.append(item['text'])
            elif item.get('type') == 'tool_use':
                parts.append(f"\n🔧 Tool Call: {item['name']}")
                parts.append(f"   Args: {json.dumps(item['input'], indent=2)}")
                parts.append(f"   ID: {item.get('id', 'N/A')}")
                tool_calls_processed = True
    else:
        parts.append(str(message.content))

    if not tool_calls_processed and hasattr(message, 'tool_calls') and message.tool_calls:
        for tool_call in message.tool_calls:
            parts.append(f"\n🔧 Tool Call: {tool_call['name']}")
            parts.append(f"   Args: {json.dumps(tool_call['args'], indent=2)}")
            parts.append(f"   ID: {tool_call['id']}")

    return "\n".join(parts)