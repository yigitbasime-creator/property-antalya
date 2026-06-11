import re
import uuid


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[àáâãäå]", "a", text)
    text = re.sub(r"[èéêë]", "e", text)
    text = re.sub(r"[ìíîï]", "i", text)
    text = re.sub(r"[òóôõö]", "o", text)
    text = re.sub(r"[ùúûü]", "u", text)
    text = re.sub(r"[ç]", "c", text)
    text = re.sub(r"[ğ]", "g", text)
    text = re.sub(r"[ş]", "s", text)
    text = re.sub(r"[ı]", "i", text)
    text = re.sub(r"[ö]", "o", text)
    text = re.sub(r"[ü]", "u", text)
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def unique_slug(text: str) -> str:
    base = slugify(text)
    return f"{base}-{uuid.uuid4().hex[:6]}"


def new_id() -> str:
    return uuid.uuid4().hex
