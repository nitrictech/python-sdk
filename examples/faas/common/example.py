from uuid import uuid4


def generate_id() -> str:
    return str(uuid4())