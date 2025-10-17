from app.api import crud
from passlib.context import CryptContext


def test_password_hash_and_verify():
    pwd = "secret123"
    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = ctx.hash(pwd)
    assert ctx.verify(pwd, hashed)
