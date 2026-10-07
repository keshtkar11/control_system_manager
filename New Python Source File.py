# check_hmi_label.py
import sqlite3
from utils.paths import get_database_path

db_path = get_database_path()
con = sqlite3.connect(db_path)

cursor = con.execute('''
    SELECT project_name, persian_label, english_label
    FROM component_labels
    WHERE component_key = 'HMI'
    ORDER BY project_name
''')

print("📊 HMI Labels in DB:")
print("-" * 60)
for row in cursor.fetchall():
    print(f"  📁 {row[0]}")
    print(f"     fa={row[1]!r}")
    print(f"     en={row[2]!r}")
    print()

con.close()