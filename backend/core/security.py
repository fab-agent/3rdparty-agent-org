from cryptography.fernet import Fernet
import pathlib

SECRET_FILE = pathlib.Path("data/.secret")


def get_fernet() -> Fernet:
    if not SECRET_FILE.exists():
        SECRET_FILE.parent.mkdir(exist_ok=True)
        key = Fernet.generate_key()
        SECRET_FILE.write_bytes(key)
        SECRET_FILE.chmod(0o600)
    return Fernet(SECRET_FILE.read_bytes())


def encrypt(plain: str) -> str:
    return get_fernet().encrypt(plain.encode()).decode()


def decrypt(cipher: str) -> str:
    return get_fernet().decrypt(cipher.encode()).decode()
