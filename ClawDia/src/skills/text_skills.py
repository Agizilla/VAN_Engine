import json
import math
import random
import re
import unicodedata
from datetime import datetime
from collections import Counter

from .base import BaseSkill, register_skill, SkillContext


# ── shared helpers ──────────────────────────────────────────────────

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD_SPLIT = re.compile(r"\b\w+\b")
_NON_ALPHA = re.compile(r"[^a-zA-Z0-9\s]")
_ENTITIES_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "url": re.compile(r"https?://[^\s]+"),
    "phone": re.compile(r"\+?\d[\d\s\-().]{7,}\d"),
    "date": re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b"),
    "number": re.compile(r"\b\d+(?:\.\d+)?\b"),
    "hashtag": re.compile(r"#\w+"),
    "mention": re.compile(r"@\w+"),
}

_TRANSLATION_DB = {
    "en": {"hello": "hello", "world": "world", "thank you": "thank you", "goodbye": "goodbye", "yes": "yes", "no": "no", "please": "please", "sorry": "sorry", "help": "help", "food": "food", "water": "water", "friend": "friend", "love": "love", "time": "time", "day": "day", "night": "night", "good": "good", "bad": "bad", "big": "big", "small": "small"},
    "es": {"hello": "hola", "world": "mundo", "thank you": "gracias", "goodbye": "adiós", "yes": "sí", "no": "no", "please": "por favor", "sorry": "lo siento", "help": "ayuda", "food": "comida", "water": "agua", "friend": "amigo", "love": "amor", "time": "tiempo", "day": "día", "night": "noche", "good": "bueno", "bad": "malo", "big": "grande", "small": "pequeño"},
    "fr": {"hello": "bonjour", "world": "monde", "thank you": "merci", "goodbye": "au revoir", "yes": "oui", "no": "non", "please": "s'il vous plaît", "sorry": "désolé", "help": "aide", "food": "nourriture", "water": "eau", "friend": "ami", "love": "amour", "time": "temps", "day": "jour", "night": "nuit", "good": "bon", "bad": "mauvais", "big": "grand", "small": "petit"},
    "de": {"hello": "hallo", "world": "welt", "thank you": "danke", "goodbye": "auf wiedersehen", "yes": "ja", "no": "nein", "please": "bitte", "sorry": "entschuldigung", "help": "hilfe", "food": "essen", "water": "wasser", "friend": "freund", "love": "liebe", "time": "zeit", "day": "tag", "night": "nacht", "good": "gut", "bad": "schlecht", "big": "groß", "small": "klein"},
    "it": {"hello": "ciao", "world": "mondo", "thank you": "grazie", "goodbye": "arrivederci", "yes": "sì", "no": "no", "please": "per favore", "sorry": "mi dispiace", "help": "aiuto", "food": "cibo", "water": "acqua", "friend": "amico", "love": "amore", "time": "tempo", "day": "giorno", "night": "notte", "good": "buono", "bad": "cattivo", "big": "grande", "small": "piccolo"},
    "pt": {"hello": "olá", "world": "mundo", "thank you": "obrigado", "goodbye": "tchau", "yes": "sim", "no": "não", "please": "por favor", "sorry": "desculpe", "help": "ajuda", "food": "comida", "water": "água", "friend": "amigo", "love": "amor", "time": "tempo", "day": "dia", "night": "noite", "good": "bom", "bad": "ruim", "big": "grande", "small": "pequeno"},
}
_LANGS = list(_TRANSLATION_DB.keys())

_CATEGORIES = [
    "technology", "science", "business", "health", "education", "entertainment",
    "sports", "politics", "environment", "food", "travel", "arts", "finance",
    "social", "other",
]

_CLASSIFY_KEYWORDS = {
    "technology": ["computer", "software", "code", "app", "digital", "data", "algorithm", "ai", "robot", "internet", "cyber", "programming", "server", "cloud", "api"],
    "science": ["research", "study", "experiment", "theory", "lab", "biology", "chemistry", "physics", "dna", "genome", "particle", "quantum", "equation"],
    "business": ["company", "startup", "market", "revenue", "profit", "investment", "funding", "ceo", "ipo", "merger", "acquisition", "stakeholder", "enterprise"],
    "health": ["health", "medical", "disease", "patient", "doctor", "hospital", "symptom", "treatment", "vaccine", "therapy", "mental", "wellness", "exercise", "diet"],
    "education": ["school", "university", "student", "teacher", "course", "learning", "study", "classroom", "curriculum", "degree", "exam", "lesson", "tutorial"],
    "entertainment": ["movie", "music", "game", "film", "actor", "artist", "concert", "album", "show", "series", "streaming", "performance", "stage", "audience"],
    "sports": ["sport", "game", "team", "player", "champion", "tournament", "match", "score", "olympic", "coach", "athlete", "stadium", "league"],
    "politics": ["government", "president", "election", "policy", "law", "senate", "congress", "vote", "democracy", "party", "minister", "politician", "campaign"],
    "environment": ["climate", "environment", "sustainable", "renewable", "carbon", "emission", "pollution", "energy", "solar", "wind", "conservation", "recycling", "green"],
    "food": ["food", "recipe", "cooking", "restaurant", "chef", "meal", "cuisine", "ingredient", "bake", "grill", "taste", "flavor", "kitchen", "dinner"],
    "travel": ["travel", "trip", "destination", "hotel", "flight", "tour", "vacation", "journey", "tourist", "country", "city", "adventure", "backpack", "road"],
    "arts": ["art", "painting", "sculpture", "museum", "gallery", "design", "creative", "piece", "exhibition", "artist", "canvas", "drawing", "culture"],
    "finance": ["finance", "bank", "stock", "bond", "trading", "crypto", "currency", "interest", "loan", "mortgage", "dividend", "portfolio", "asset", "debt"],
}

_REWRITE_TEMPLATES = {
    "formal": [
        "It is observed that {text}",
        "One may note that {text}",
        "The following has been established: {text}",
        "It can be stated that {text}",
        "According to reliable sources, {text}",
    ],
    "casual": [
        "So like, {text}",
        "Basically, {text}",
        "You know what, {text}",
        "Just saying, {text}",
        "Here's the thing: {text}",
    ],
    "professional": [
        "Analysis indicates that {text}",
        "Our findings show that {text}",
        "Based on our assessment, {text}",
        "The data suggests that {text}",
        "In conclusion, {text}",
    ],
    "creative": [
        "Imagine a world where {text}",
        "Picture this: {text}",
        "What if I told you that {text}",
        "Like a phoenix rising, {text}",
        "In the grand tapestry of things, {text}",
    ],
    "simple": [
        "Simply put, {text}",
        "In short, {text}",
        "The gist is: {text}",
        "Long story short, {text}",
        "To put it simply, {text}",
    ],
}


# ── 1. Text Summarize ───────────────────────────────────────────────

@register_skill("text_summarize", "utility")
class TextSummarizeSkill(BaseSkill):
    name = "text_summarize"
    description = "Extractive text summarization — top sentences by keyword density"
    author = "ClawDia"
    version = "1.0.0"
    category = "utility"
    tags = ["text", "summarize", "nlp", "extractive"]
    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to summarize"},
            "max_sentences": {"type": "integer", "default": 3},
            "style": {"type": "string", "enum": ["concise", "detailed", "bullet"], "default": "concise"},
        },
    }

    def execute(self, **kwargs) -> dict:
        text = kwargs.get("text", "")
        max_sentences = max(1, min(kwargs.get("max_sentences", 3), 20))
        style = kwargs.get("style", "concise")

        if not text.strip():
            return {"error": None, "result": {"summary": "", "original_length": 0, "summary_length": 0, "compression_ratio": 0}}

        raw_sentences = _SENTENCE_SPLIT.split(text.strip())
        sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 10]
        if not sentences:
            sentences = [text.strip()]

        words = _WORD_SPLIT.findall(text.lower())
        word_freq = Counter(words)
        max_freq = max(word_freq.values()) if word_freq else 1

        scored = []
        for i, sent in enumerate(sentences):
            sent_words = _WORD_SPLIT.findall(sent.lower())
            if not sent_words:
                continue
            score = sum(word_freq.get(w, 0) / max_freq for w in sent_words) / len(sent_words)
            scored.append((score, i, sent))

        scored.sort(key=lambda x: (-x[0], x[1]))
        top = scored[:max_sentences]
        top.sort(key=lambda x: x[1])

        selected = [s for _, _, s in top]

        if style == "bullet":
            summary = "\n".join(f"- {s}" for s in selected)
        elif style == "detailed":
            summary = " ".join(selected)
        else:
            if len(selected) == 1:
                summary = selected[0]
            else:
                summary = " ".join(selected)

        orig_len = len(text.split())
        summ_len = len(summary.split())
        ratio = round((1 - summ_len / orig_len) * 100, 1) if orig_len else 0

        return {
            "error": None,
            "result": {
                "summary": summary,
                "original_length": orig_len,
                "summary_length": summ_len,
                "compression_ratio": ratio,
                "sentence_count": len(selected),
            },
        }


# ── 2. Text Rewrite ─────────────────────────────────────────────────

@register_skill("text_rewrite", "utility")
class TextRewriteSkill(BaseSkill):
    name = "text_rewrite"
    description = "Paraphrase text in different tones — formal, casual, professional, creative, simple"
    author = "ClawDia"
    version = "1.0.0"
    category = "utility"
    tags = ["text", "rewrite", "paraphrase", "tone"]
    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to rewrite"},
            "tone": {"type": "string", "enum": ["formal", "casual", "professional", "creative", "simple"], "default": "professional"},
            "max_variations": {"type": "integer", "default": 1},
        },
    }

    def execute(self, **kwargs) -> dict:
        text = kwargs.get("text", "").strip()
        tone = kwargs.get("tone", "professional")
        max_variations = max(1, min(kwargs.get("max_variations", 1), 5))

        if not text:
            return {"error": None, "result": {"variations": [], "tone": tone}}

        templates = _REWRITE_TEMPLATES.get(tone, _REWRITE_TEMPLATES["professional"])

        words = _WORD_SPLIT.findall(text)
        word_count = len(words)

        if word_count <= 3:
            base = text
            rewrite_fns = {
                "formal": lambda t: t.capitalize() + ".",
                "casual": lambda t: t.lower(),
                "professional": lambda t: t,
                "creative": lambda t: t[::-1] if len(t) > 5 else t,
                "simple": lambda t: t,
            }
            variations = []
            seen = set()
            for _ in range(max_variations * 3):
                fn = rewrite_fns.get(tone, lambda t: t)
                v = fn(text)
                if v and v not in seen:
                    seen.add(v)
                    variations.append(v)
                if len(variations) >= max_variations:
                    break
            if not variations:
                variations = [text]
        else:
            text_lower = text.lower()
            variations = []
            seen = set()
            for t in templates:
                v = t.format(text=text_lower)
                if v not in seen:
                    seen.add(v)
                    variations.append(v)
                if len(variations) >= max_variations:
                    break

            if text.endswith("."):
                alt = text[:-1]
            else:
                alt = text + "."

            if len(variations) < max_variations and alt not in seen:
                variations.append(alt)

        return {
            "error": None,
            "result": {
                "variations": variations[:max_variations],
                "tone": tone,
                "original_word_count": word_count,
            },
        }


# ── 3. Text Generate ────────────────────────────────────────────────

_TEMPLATES = {
    "story": [
        "Once upon a time, in a land not too far away, there was a {subject} who {action}. Every day, they would {habit}. But one morning, everything changed when {conflict}. {resolution} And so, {moral}.",
        "The {subject} had always known that {fact}. What they didn't expect was {twist}. With {resource} in hand, they set out to {goal}. The journey taught them that {lesson}.",
    ],
    "poem": [
        "The {subject} whispers through the {place},\nA {adjective} {noun} in time and space.\n{verb} the {noun2} of yesterday,\nWhile {concept} lights the way.",
        "In {place} where {subject} {verb}s the {noun},\nA {adjective} {noun2} comes undone.\n{concept} and {concept2} embrace,\nLeaving {emotion} upon this place.",
    ],
    "email": [
        "Subject: {subject}\n\nDear {recipient},\n\nI hope this message finds you well. I'm writing to {purpose}. {detail}.\n\nCould you please {action_item}? I'd appreciate your response by {deadline}.\n\nBest regards,\n{author}",
        "Hi {recipient},\n\nQuick note about {subject}: {purpose}. {detail}.\n\nCan you {action_item}? Thanks!\n\n- {author}",
    ],
    "tweet": [
        "{hook} {detail}. {call_to_action} #ClawDia",
        "Just realized: {insight}. Mind = blown. 🤯 {call_to_action}",
        "PSA: {message} {call_to_action}",
    ],
    "description": [
        "The {subject} is a {adjective1}, {adjective2} {noun} designed for {purpose}. Featuring {feature1} and {feature2}, it {benefit}. Perfect for {audience}.",
        "Introducing {subject}: {hook}. With {feature1} at its core, {benefit}. Built for {audience} who demand {quality}.",
    ],
}

_TEMPLATE_WORDS = {
    "subject": ["developer", "designer", "writer", "explorer", "thinker", "maker", "artist", "dreamer", "coder", "builder"],
    "action": ["sought the truth", "chased the horizon", "built something new", "fixed what was broken", "connected the dots", "broke the rules", "started a revolution"],
    "habit": ["write code at dawn", "sketch ideas on napkins", "question everything", "help others grow", "push the boundaries", "find beauty in simplicity"],
    "conflict": ["a shadow appeared", "the rules changed", "nothing worked as expected", "a rival emerged", "the deadline moved up"],
    "resolution": ["With courage and wit, they prevailed.", "They learned that asking for help was strength.", "In the end, the answer was simpler than expected.", "They pivoted, adapted, and grew stronger."],
    "moral": ["the real treasure was the journey itself.", "perfection is the enemy of done.", "done is better than perfect.", "the best code is the code you ship."],
    "fact": ["change was inevitable", "great things take time", "the best ideas come at 2 AM", "collaboration beats competition"],
    "twist": ["an unexpected ally", "a hidden truth", "the opposite of what they believed", "a gift in disguise"],
    "resource": ["a cup of coffee", "a rubber duck", "their wit", "a second chance", "an old notebook"],
    "goal": ["change the world", "ship the product", "learn something new", "make a difference", "fix the bug"],
    "lesson": ["done is better than perfect", "collaboration compounds", "rest is productive", "curiosity pays"],
    "place": ["silicon valley", "the workshop", "the terminal", "the cloud", "the open source community", "the city"],
    "adjective": ["gentle", "restless", "quiet", "bright", "ancient", "digital", "timeless", "curious"],
    "noun": ["spirit", "craft", "art", "system", "pattern", "rhythm", "dream", "path", "code"],
    "verb": ["shape", "define", "guide", "inspire", "build", "create", "weave", "ignite"],
    "noun2": ["regret", "wonder", "silence", "noise", "order", "chaos", "meaning"],
    "concept": ["hope", "time", "grace", "truth", "art", "logic", "passion"],
    "concept2": ["reason", "intuition", "memory", "desire", "purpose"],
    "emotion": ["peace", "awe", "contentment", "wonder", "serenity", "joy"],
    "recipient": ["Team", "Friend", "Colleague", "Mentor", "Stakeholder"],
    "purpose": ["discuss the upcoming project", "share an update", "propose a new idea", "ask for your input", "follow up on our conversation"],
    "detail": ["I've attached the relevant documents", "Here are the key points to consider", "I've outlined the main findings below", "Let me know your thoughts"],
    "action_item": ["review the proposal by Friday", "share your feedback at your earliest convenience", "let me know if you have questions", "confirm your availability for next week"],
    "deadline": ["end of week", "tomorrow", "Monday", "next Friday", "COB today"],
    "author": ["Your Colleague", "The Team", "Your Friendly AI", "The Builder"],
    "hook": ["Hot take:", "Unpopular opinion:", "Real talk:", "Thread:", "Breaking:", "PSA:"],
    "call_to_action": ["What do you think?", "Retweet if you agree.", "Share your thoughts below.", "DM for details."],
    "insight": ["the best tool is the one you already have", "you don't need permission to start", "constraints breed creativity", "consistency beats intensity"],
    "message": ["your mental health matters more than productivity", "open source is how we win", "documentation is a love letter to your future self"],
    "adjective1": ["powerful", "elegant", "robust", "lightweight", "versatile", "intuitive"],
    "adjective2": ["scalable", "beautiful", "efficient", "modular", "reliable", "secure"],
    "feature1": ["real-time sync", "offline-first architecture", "zero-config setup", "API-first design"],
    "feature2": ["automatic backups", "collaborative editing", "cross-platform support", "plugin system"],
    "benefit": ["saves you hours every week", "just works, everywhere", "lets you focus on what matters", "scales with your needs"],
    "audience": ["teams of all sizes", "solo developers", "enterprise organizations", "creative professionals"],
    "quality": ["reliability", "simplicity", "performance", "flexibility", "security"],
}


@register_skill("text_generate", "utility")
class TextGenerateSkill(BaseSkill):
    name = "text_generate"
    description = "Template-based text generation — stories, poems, emails, tweets, descriptions"
    author = "ClawDia"
    version = "1.0.0"
    category = "utility"
    tags = ["text", "generate", "templates", "creative"]
    input_schema = {
        "type": "object",
        "properties": {
            "template_type": {"type": "string", "enum": ["story", "poem", "email", "tweet", "description"], "default": "story"},
            "seed": {"type": "string", "default": "", "description": "Optional theme or subject hint"},
            "count": {"type": "integer", "default": 1},
        },
    }

    def execute(self, **kwargs) -> dict:
        template_type = kwargs.get("template_type", "story")
        seed = kwargs.get("seed", "").strip()
        count = max(1, min(kwargs.get("count", 1), 10))

        templates = _TEMPLATES.get(template_type, _TEMPLATES["story"])

        results = []
        for _ in range(count):
            t = random.choice(templates)
            filled = t
            for key, vals in _TEMPLATE_WORDS.items():
                placeholder = "{" + key + "}"
                if placeholder in filled:
                    if seed and key == "subject":
                        filled = filled.replace(placeholder, seed, 1)
                        seed_used = True
                    else:
                        filled = filled.replace(placeholder, random.choice(vals), 1)
            if seed and "{subject}" in filled:
                filled = filled.replace("{subject}", seed, 1)
            results.append(filled.strip())

        return {
            "error": None,
            "result": {
                "generated": results,
                "template_type": template_type,
                "count": len(results),
            },
        }


# ── 4. Text Classify ────────────────────────────────────────────────

@register_skill("text_classify", "utility")
class TextClassifySkill(BaseSkill):
    name = "text_classify"
    description = "Keyword-based text classification into 14 categories with confidence scores"
    author = "ClawDia"
    version = "1.0.0"
    category = "utility"
    tags = ["text", "classify", "nlp", "categorization"]
    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to classify"},
            "top_n": {"type": "integer", "default": 3},
        },
    }

    def execute(self, **kwargs) -> dict:
        text = kwargs.get("text", "").strip()
        top_n = max(1, min(kwargs.get("top_n", 3), len(_CATEGORIES)))

        if not text:
            return {"error": None, "result": {"categories": [], "primary": "other", "confidence": 0}}

        words_lower = set(_WORD_SPLIT.findall(text.lower()))
        total_words = len(words_lower)

        scores = {}
        for cat, keywords in _CLASSIFY_KEYWORDS.items():
            matched = sum(1 for kw in keywords if kw in words_lower)
            if matched > 0:
                scores[cat] = matched / max(len(keywords) * 0.3, 1)

        if not scores:
            scores["other"] = 0.1

        ranked = sorted(scores.items(), key=lambda x: -x[1])
        top = ranked[:top_n]
        total_score = sum(s for _, s in top) or 1

        categories = [
            {"category": cat, "confidence": round(score / total_score, 4)}
            for cat, score in top
        ]

        return {
            "error": None,
            "result": {
                "categories": categories,
                "primary": top[0][0] if top else "other",
                "confidence": round(top[0][1] / total_score, 4) if top else 0,
                "total_keyword_matches": sum(scores.values()),
            },
        }


# ── 5. Text Extract Entities ────────────────────────────────────────

@register_skill("text_extract_entities", "utility")
class TextExtractEntitiesSkill(BaseSkill):
    name = "text_extract_entities"
    description = "Extract structured entities from text — emails, URLs, phones, dates, numbers, hashtags, mentions"
    author = "ClawDia"
    version = "1.0.0"
    category = "utility"
    tags = ["text", "entities", "extraction", "nlp"]
    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to extract entities from"},
            "types": {
                "type": "array",
                "items": {"type": "string", "enum": list(_ENTITIES_PATTERNS.keys())},
                "description": "Entity types to extract (default: all)",
            },
            "deduplicate": {"type": "boolean", "default": True},
        },
    }

    def execute(self, **kwargs) -> dict:
        text = kwargs.get("text", "")
        requested_types = kwargs.get("types", list(_ENTITIES_PATTERNS.keys()))
        deduplicate = kwargs.get("deduplicate", True)

        if not text.strip():
            return {"error": None, "result": {"entities": {}, "total_count": 0}}

        patterns = {k: v for k, v in _ENTITIES_PATTERNS.items() if k in requested_types}

        entities = {}
        for etype, pattern in patterns.items():
            matches = pattern.findall(text)
            if deduplicate:
                matches = list(dict.fromkeys(matches))
            if matches:
                entities[etype] = matches

        total = sum(len(v) for v in entities.values())

        stats = {}
        if "number" in entities:
            nums = []
            for n in entities["number"]:
                try:
                    nums.append(float(n))
                except ValueError:
                    continue
            if nums:
                stats["number"] = {
                    "count": len(nums),
                    "min": min(nums),
                    "max": max(nums),
                    "sum": round(sum(nums), 2),
                    "mean": round(sum(nums) / len(nums), 2),
                }

        return {
            "error": None,
            "result": {
                "entities": entities,
                "total_count": total,
                "types_found": list(entities.keys()),
                "stats": stats,
            },
        }


# ── 6. Text Translate ───────────────────────────────────────────────

@register_skill("text_translate", "utility")
class TextTranslateSkill(BaseSkill):
    name = "text_translate"
    description = "Translate text between languages using a built-in phrase database (en, es, fr, de, it, pt)"
    author = "ClawDia"
    version = "1.0.0"
    category = "utility"
    tags = ["text", "translate", "language", "i18n"]
    input_schema = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to translate"},
            "source_lang": {"type": "string", "enum": _LANGS, "default": "en", "description": "Source language code"},
            "target_lang": {"type": "string", "enum": _LANGS, "default": "es", "description": "Target language code"},
            "mode": {"type": "string", "enum": ["phrase", "word"], "default": "phrase", "description": "Translation mode"},
        },
    }

    def execute(self, **kwargs) -> dict:
        text = kwargs.get("text", "").strip().lower()
        source = kwargs.get("source_lang", "en")
        target = kwargs.get("target_lang", "es")
        mode = kwargs.get("mode", "phrase")

        if not text:
            return {"error": None, "result": {"translated": "", "source": source, "target": target, "match_count": 0}}

        source_dict = _TRANSLATION_DB.get(source, _TRANSLATION_DB["en"])
        target_dict = _TRANSLATION_DB.get(target, _TRANSLATION_DB["es"])

        if mode == "word":
            words = text.split()
            translated_words = []
            match_count = 0
            for w in words:
                w_clean = w.strip(".,!?;:")
                if w_clean in source_dict:
                    tw = target_dict.get(source_dict.get(w_clean, w_clean), w_clean)
                    translated_words.append(tw)
                    match_count += 1
                else:
                    if target == "en" and w_clean not in target_dict:
                        for src_lang, src_words in _TRANSLATION_DB.items():
                            if src_lang != target:
                                for phrase, translation in src_words.items():
                                    if translation == w_clean:
                                        translated_words.append(phrase)
                                        match_count += 1
                                        break
                                else:
                                    continue
                                break
                        else:
                            translated_words.append(w)
                    else:
                        translated_words.append(w)
            translated = " ".join(translated_words)
        else:
            if text in source_dict:
                phrase = source_dict[text]
                translated = target_dict.get(phrase, phrase)
                match_count = 1
            else:
                words = text.split()
                translated_words = []
                match_count = 0
                for w in words:
                    w_clean = w.strip(".,!?;:")
                    if w_clean in source_dict:
                        tw = target_dict.get(source_dict[w_clean], w_clean)
                        translated_words.append(tw)
                        match_count += 1
                    else:
                        translated_words.append(w)
                translated = " ".join(translated_words)

        return {
            "error": None,
            "result": {
                "translated": translated,
                "source": source,
                "target": target,
                "match_count": match_count,
                "total_words": len(text.split()),
            },
        }
