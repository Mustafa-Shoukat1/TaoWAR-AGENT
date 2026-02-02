from database.schema import create_tables
from database.users import add_default_users


create_tables()
add_default_users()
print("✅ Database initialized and default users added.")
