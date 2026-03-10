import random
import string


def generate_tracking_code(prefix: str = "TRK", length: int = 10) -> str:
    # Напр.: TRK-AB12CD34EF
    alphabet = string.ascii_uppercase + string.digits
    body = "".join(random.choices(alphabet, k=length))
    return f"{prefix}-{body}"
