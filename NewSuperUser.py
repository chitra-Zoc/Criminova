import database as db
import binascii
import psycopg2
from datetime import datetime

NAME = 'test'
CONTACT = 'test'
JOINED_DATE = datetime.now().date()
EMAIL = 'abcd@gmail.com'
USERNAME = 'test'
IMAGE_PATH = 'icons/victim.jpg'
PASSWORD = '1234'
ROLE = 'Administrator'
IMAGE_DATA = None

# Read image data from file
with open(IMAGE_PATH, 'rb') as img_file:
    IMAGE_DATA = img_file.read()

conn = db.connect_db()
cur=conn.cursor()
cur.execute("SELECT username from authorized where role='Administrator'")
exist=cur.fetchone()[0]


def create_superUser():
    if ROLE=='Administrator' and exist is None:
        conn = None
        try:
            # Connect to the database
            conn = db.connect_db()
            cur=conn.cursor()
            # Hash the password
            password_hash = db.hash_generator(PASSWORD)

            # Convert the hashed password to hexadecimal string
            password_hex = binascii.hexlify(password_hash).decode('utf-8')

            # Insert data into officer_record table
            cur.execute(f"""
                INSERT INTO officer_record (name, contact, email, joined_date, image) 
                VALUES ('{NAME}', '{CONTACT}', '{EMAIL}', '{JOINED_DATE}', %s)
                RETURNING id;
            """, (psycopg2.Binary(IMAGE_DATA),))
            officer_id = cur.fetchone()[0]

            # Insert data into authorized table
            cur.execute(f"""
                INSERT INTO authorized (id, username, password, role) 
                VALUES ({officer_id}, '{USERNAME}', '{password_hex}', '{ROLE}');
            """)

            # Commit the transaction
            conn.commit()
            print("Superuser created successfully.")

        except (Exception, psycopg2.DatabaseError) as error:
            print("Error:", error)
            if conn:
                conn.rollback()

        finally:
            # Properly close connection in finally block
            if conn:
                conn.close()
    else:
        print('Error: Administrator Already present')

if __name__ == '__main__':
    create_superUser()
