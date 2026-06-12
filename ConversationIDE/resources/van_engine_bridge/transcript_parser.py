#!/usr/bin/env python3
import sys, io, json, re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

@dataclass
class TranscriptMessage:
    role: str
    content: str
    timestamp: Optional[str] = None

@dataclass
class StructuredResponse:
    date: str = ""
    summary: str = ""
    analysis: str = ""
    actions: str = ""
    results: str = ""
    status: str = ""
    next_action: str = ""

@dataclass
class ParsedTranscript:
    raw: str
    last_message: str
    current_response_text: str
    voice_completion: str
    plain_completion: str
    structured: StructuredResponse
    response_state: str
    messages: List[TranscriptMessage] = field(default_factory=list)
    message_count: int = 0
    error: Optional[str] = None

class TranscriptParser:
    def __init__(self, da_name: str = "Assistant", principal_name: str = "User"):
        self.da_name = da_name
        self.principal_name = principal_name

    def parse_file(self, transcript_path: Path) -> ParsedTranscript:
        if not transcript_path.exists():
            return ParsedTranscript(raw="", last_message="", current_response_text="",
                voice_completion="", plain_completion="",
                structured=StructuredResponse(), response_state="error",
                error=f"File not found: {transcript_path}")
        content = transcript_path.read_text(encoding='utf-8')
        return self.parse_content(content)

    def parse_content(self, content: str) -> ParsedTranscript:
        lines = content.strip().split('\n')
        messages = []
        last_assistant_message = ""
        current_response_parts = []
        last_human_index = -1

        for i, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                msg_type = entry.get('type')
                if msg_type == 'user' and self._is_real_user_message(entry.get('message', {})):
                    last_human_index = i
                    messages.append(TranscriptMessage(role='user',
                        content=self._extract_text(entry.get('message', {}).get('content')),
                        timestamp=entry.get('timestamp')))
                elif msg_type == 'assistant':
                    text = self._extract_text(entry.get('message', {}).get('content'))
                    if text:
                        last_assistant_message = text
                        messages.append(TranscriptMessage(role='assistant',
                            content=text, timestamp=entry.get('timestamp')))
            except json.JSONDecodeError:
                continue

        for i in range(last_human_index + 1, len(lines)):
            try:
                entry = json.loads(lines[i])
                if entry.get('type') == 'assistant':
                    text = self._extract_text(entry.get('message', {}).get('content'))
                    if text:
                        current_response_parts.append(text)
            except:
                continue

        current_response_text = '\n'.join(current_response_parts)

        return ParsedTranscript(raw=content, last_message=last_assistant_message,
            current_response_text=current_response_text,
            voice_completion=self._extract_voice_completion(current_response_text),
            plain_completion=self._extract_plain_completion(current_response_text),
            structured=self._extract_structured_sections(current_response_text),
            response_state=self._detect_response_state(last_assistant_message),
            messages=messages, message_count=len(messages))

    def _is_real_user_message(self, message: dict) -> bool:
        content = message.get('content')
        if isinstance(content, str):
            return bool(content.strip())
        if isinstance(content, list):
            for block in content:
                if block.get('type') == 'text' and block.get('text'):
                    return True
        return False

    def _extract_text(self, content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = []
            for block in content:
                if block.get('type') == 'text':
                    texts.append(block.get('text', ''))
                elif 'text' in block:
                    texts.append(str(block['text']))
            return ' '.join(texts)
        return ''

    def _remove_system_reminders(self, text: str) -> str:
        return re.sub(r'<system-reminder>[\s\S]*?</system-reminder>', '', text)

    def _extract_voice_completion(self, text: str) -> str:
        text = self._remove_system_reminders(text)
        patterns = [
            rf'\U0001F5E3\s*\*?{re.escape(self.da_name)}:?\*?\s*(.+?)(?:\n|$)',
            r'\U0001F3AF\s*\*?COMPLETED:?\*?\s*(.+?)(?:\n|$)'
        ]
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                last_match = matches[-1]
                result = last_match.group(1).strip()
                result = re.sub(r'^\[AGENT:\w+\]\s*', '', result)
                return result
        return ""

    def _extract_plain_completion(self, text: str) -> str:
        voice = self._extract_voice_completion(text)
        if voice:
            voice = re.sub(r'\[.*?\]', '', voice)
            voice = re.sub(r'\*\*', '', voice)
            voice = re.sub(r'\*', '', voice)
            voice = re.sub(r'[\U00010000-\U0010ffff]', '', voice)
            voice = re.sub(r'\s+', ' ', voice).strip()
            return voice
        summary_match = re.search(r'\U0001F4CB\s*\*?SUMMARY:?\*?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if summary_match:
            summary = summary_match.group(1).strip()
            return summary[:30] + "..." if len(summary) > 30 else summary
        return ""

    def _extract_structured_sections(self, text: str) -> StructuredResponse:
        text = self._remove_system_reminders(text)
        def extract(pattern: str) -> str:
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else ""
        return StructuredResponse(
            date=extract(r'\U0001F4C5\s*(.+?)(?:\n|$)'),
            summary=extract(r'\U0001F4CB\s*SUMMARY:\s*(.+?)(?:\n|$)'),
            analysis=extract(r'\U0001F50D\s*ANALYSIS:\s*(.+?)(?:\n|$)'),
            actions=extract(r'\u26A1\s*ACTIONS:\s*(.+?)(?:\n|$)'),
            results=extract(r'\u2705\s*RESULTS:\s*(.+?)(?:\n|$)'),
            status=extract(r'\U0001F4CA\s*STATUS:\s*(.+?)(?:\n|$)'),
            next_action=extract(r'\u27A1\uFE0F\s*NEXT:\s*(.+?)(?:\n|$)')
        )

    def _detect_response_state(self, last_message: str) -> str:
        if not last_message:
            return "completed"
        if "AskUserQuestion" in last_message or ("?" in last_message and "COMPLETED" not in last_message):
            return "awaiting_input"
        if re.search(r'error|failed|exception|\u274C|\U0001F6A8', last_message, re.IGNORECASE):
            return "error"
        return "completed"

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("transcript_path", help="Path to transcript JSONL file")
    parser.add_argument("--voice", action="store_true", help="Output voice completion")
    parser.add_argument("--plain", action="store_true", help="Output plain completion")
    parser.add_argument("--structured", action="store_true", help="Output structured sections")
    parser.add_argument("--state", action="store_true", help="Output response state")
    args = parser.parse_args()
    parser_obj = TranscriptParser()
    result = parser_obj.parse_file(Path(args.transcript_path))
    if args.voice:
        print(result.voice_completion)
    elif args.plain:
        print(result.plain_completion)
    elif args.structured:
        print(json.dumps(result.structured.__dict__, indent=2))
    elif args.state:
        print(result.response_state)
    else:
        print(json.dumps({
            "last_message": result.last_message[:200],
            "voice_completion": result.voice_completion,
            "response_state": result.response_state,
            "message_count": result.message_count
        }, indent=2))

if __name__ == "__main__":
    main()
