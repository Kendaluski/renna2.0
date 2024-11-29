import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

try:
	conn = psycopg2.connect(
		database=db_name,
		user=db_user,
		password=db_pass,
		host=db_host,
		port=db_port
	)
	cursor = conn.cursor()
	cursor.execute("SELECT version();")
	record = cursor.fetchone()
	print("You are connected to - ", record, "\n")

except (Exception, psycopg2.Error) as error:
	print("Error while connecting to PostgreSQL", error)
finally:
	if conn:
		cursor.close()
		conn.close()
		print("PostgreSQL connection is closed")