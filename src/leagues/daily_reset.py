import os, psycopg2
from datetime import datetime
from dotenv import load_dotenv
from leagues.league import init_league

load_dotenv()
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

async def daily_reset():
	try:
		conn = psycopg2.connect(
			database=db_name,
			user=db_user,
			password=db_pass,
			host=db_host,
			port=db_port
		)
		cursor = conn.cursor()
		cursor.execute("SELECT user_id, last_league FROM pusers")
		today = datetime.now().date()
		users = cursor.fetchall()
		for u in users:
			id, last_league = u
			league = init_league(id)
			if last_league is None:
				last_league = today
			if last_league < today:
				cursor.execute("UPDATE pusers SET league = %s, last_league = %s WHERE user_id = %s", (league, today, id))
				conn.commit()
	except (Exception, psycopg2.Error) as error:
		print("Error while connecting to PostgreSQL", error)
	finally:
		if conn:
			cursor.close()
			conn.close()