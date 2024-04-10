import database as db
import binascii
import psycopg2
import bcrypt
from PIL import Image

def create_superUser():
    conn = None
    cur = None
    try:
        conn = db.connect_db()  # Ensure this function exists in your database module
        cur = conn.cursor()

        # Assuming hash_generator() exists in your db module and returns a bytes object
        password = db.hash_generator('Criminova@py2080')
        # Convert the hashed password to a hexadecimal string
        password_hash = binascii.hexlify(password).decode('utf-8')

        # Load the image from file
        image_path = 'icons/jd.jpg'
        with open(image_path, 'rb') as img_file:
            image_data = img_file.read()

        # Insert the new superuser into the database
        cur.execute('INSERT INTO authorized_users (username, name, role, password, image) VALUES (%s, %s, %s, %s, %s)',
                    ('31jay', 'Jayadev Tripathi', 'Administrator', password_hash, image_data))
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        print("Error:", error)
    finally:
        # Properly close cursor and connection in finally block
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    create_superUser()



'''# Convert the hexadecimal string back to bytes
stored_hash_bytes = binascii.unhexlify(stored_hash)

# Verify the entered password against the stored hash
if bcrypt.checkpw(entered_password.encode(), stored_hash_bytes):
    print("Password is correct.")
else:
    print("Password is incorrect.")'''