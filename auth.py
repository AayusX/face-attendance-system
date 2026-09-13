import binascii
import hashlib
import hmac
import os

from database import get_setting, init_db, set_setting

DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"
ITERATIONS = 200_000


def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return (
        f"pbkdf2${ITERATIONS}${binascii.hexlify(salt).decode()}"
        f"${binascii.hexlify(digest).decode()}"
    )


def verify_password(password, stored):
    try:
        _, iterations, salt_hex, hash_hex = stored.split("$")
        salt = binascii.unhexlify(salt_hex)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, int(iterations)
        )
        return hmac.compare_digest(digest, binascii.unhexlify(hash_hex))
    except (ValueError, TypeError):
        return False


def seed_defaults():
    init_db()
    if get_setting("auth_username") is None:
        set_setting("auth_username", DEFAULT_USERNAME)
        set_setting("auth_password", hash_password(DEFAULT_PASSWORD))
        return True
    return False


def check_login(username, password):
    seed_defaults()
    stored_user = get_setting("auth_username")
    stored_pass = get_setting("auth_password")
    if username != stored_user:
        return False, "Unknown username."
    if not stored_pass or not verify_password(password, stored_pass):
        return False, "Incorrect password."
    return True, None


def change_password(username, current, new_username, new_password):
    ok, error = check_login(username, current)
    if not ok:
        return False, error
    set_setting("auth_username", new_username.strip() or username)
    set_setting("auth_password", hash_password(new_password))
    return True, None