import secrets


def generate_token(length=32):
    """Generate a secure random token"""
    return secrets.token_hex(length // 2)
