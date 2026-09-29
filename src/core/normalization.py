import unicodedata


def normalize_username(username: str) -> str:
    return unicodedata.normalize("NFKC", username)


def make_username_key(username: str) -> str:
    return normalize_username(username).casefold()


def normalize_email(email: str) -> str:
    return email.strip().lower()
