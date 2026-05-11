from sqlalchemy import select

from app.core.database import SessionLocal, get_engine
from app.core.security import hash_password
from app.models.user import User

TARGET_EMAILS = (
    "admin.dev@meerkat.local",
    "worker1.dev@meerkat.local",
    "worker2.dev@meerkat.local",
)
DEFAULT_PASSWORD = "devpass1234"


def main() -> None:
    get_engine()
    with SessionLocal() as db:
        users = db.scalars(select(User).where(User.email.in_(TARGET_EMAILS))).all()
        if not users:
            print("No target dev users found.")
            return

        for user in users:
            user.hashed_password = hash_password(DEFAULT_PASSWORD)
        db.commit()
        print(f"Updated {len(users)} dev users. Password set to: {DEFAULT_PASSWORD}")


if __name__ == "__main__":
    main()
