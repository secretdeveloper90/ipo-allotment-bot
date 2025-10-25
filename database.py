import sqlite3

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Create new table for multiple PANs with unique constraint
    c.execute("""
        CREATE TABLE IF NOT EXISTS pan_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            pan TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, pan)
        )
    """)
    conn.commit()
    conn.close()

def add_pan(user_id, name, pan):
    """Add a new PAN number for a user (max 20 PANs per user)"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Check if user already has 20 PANs
    c.execute("SELECT COUNT(*) FROM pan_numbers WHERE user_id = ?", (user_id,))
    count = c.fetchone()[0]

    if count >= 20:
        conn.close()
        raise Exception("Maximum 20 PAN numbers allowed per user")

    # Check if this PAN already exists for this user
    c.execute("SELECT COUNT(*) FROM pan_numbers WHERE user_id = ? AND pan = ?", (user_id, pan))
    exists = c.fetchone()[0]

    if exists > 0:
        conn.close()
        raise Exception("This PAN number is already added")

    # Insert the new PAN
    try:
        c.execute("INSERT INTO pan_numbers (user_id, name, pan) VALUES (?, ?, ?)", (user_id, name, pan))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise Exception("This PAN number is already added")
    finally:
        conn.close()

def get_all_pans(user_id):
    """Get all PAN numbers for a user"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, name, pan FROM pan_numbers WHERE user_id = ? ORDER BY created_at", (user_id,))
    results = c.fetchall()
    conn.close()
    return [{"id": r[0], "name": r[1], "pan": r[2]} for r in results]

def delete_pan_by_id(pan_id):
    """Delete a specific PAN by ID"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM pan_numbers WHERE id = ?", (pan_id,))
    conn.commit()
    conn.close()

def get_pan_count(user_id):
    """Get count of PANs for a user"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM pan_numbers WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

# Legacy functions for backward compatibility (deprecated)
def set_pan(user_id, pan):
    """Legacy function - adds PAN with default name"""
    add_pan(user_id, "No Name", pan)

def get_pan(user_id):
    """Legacy function - gets first PAN"""
    pans = get_all_pans(user_id)
    return pans[0]["pan"] if pans else None

def delete_pan(user_id):
    """Legacy function - deletes all PANs for user"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM pan_numbers WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
