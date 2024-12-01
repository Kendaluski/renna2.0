
import requests, discord, os, random, shared, asyncio, psycopg2
from dotenv import load_dotenv

load_dotenv()
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')

def get_league(id):
	try:
		conn = psycopg2.connect(
			database=db_name,
			user=db_user,
			password=db_pass,
			host=db_host,
			port=db_port
		)
		cursor = conn.cursor()
		cursor.execute("SELECT league FROM pusers WHERE user_id = %s", (id,))
		l = cursor.fetchone()[0]
		if l == None:
			return 0
		else:
			return l
	except (Exception, psycopg2.Error) as error:
		print("Error while connecting to PostgreSQL", error)
	finally:
		if conn:
			cursor.close()
			conn.close()

def init_league(id):
	if id == 0:
		return 0
	try:
		conn = psycopg2.connect(
			database=db_name,
			user=db_user,
			password=db_pass,
			host=db_host,
			port=db_port
		)
		cursor = conn.cursor()
		cursor.execute("SELECT MAX(stats) FROM pcatches WHERE user_id = %s", (id,))
		stats = cursor.fetchone()[0]
		if stats == None:
			return 0
		if stats <= 100:
			l = 100
		if stats > 100 and stats <= 300:
			l = 300
		if stats > 300 and stats <= 500:
			l = 500
		if stats > 500 and stats <= 600:
			l = 600
		if stats > 600 and stats <= 800:
			l = 800
		return l
	except (Exception, psycopg2.Error) as error:
		print("Error while connecting to PostgreSQL", error)
	finally:
		if conn:
			cursor.close()
			conn.close()


def same_league(cid, did):
	try:
		conn = psycopg2.connect(
			database=db_name,
			user=db_user,
			password=db_pass,
			host=db_host,
			port=db_port
		)
		cursor = conn.cursor()
		cursor.execute("SELECT league FROM pusers WHERE user_id = %s", (cid,))
		league1 = cursor.fetchone()[0]
		if league1 == 0 or league1 == None:
			league1 = init_league(cid)
		cursor.execute("SELECT league FROM pusers WHERE user_id = %s", (did,))
		league2 = cursor.fetchone()[0]
		if league2 == 0 or league2 == None:
			league2 = init_league(did)
		if league1 == league2:
			return False
		else:
			return True
	except (Exception, psycopg2.Error) as error:
		print("Error while connecting to PostgreSQL", error)

	finally:
		if conn:
			cursor.close()
			conn.close()

def check_stats(stats1, stats2, l):
	c1 = False
	c2 = False
	for s in stats1:
		if l == 100 and s[0] <= 100:
			c1 = True
		elif l == 300 and s[0] > 100 and s[0] <= 300:
			c1 = True
		elif l == 500 and s[0] > 300 and s[0] <= 500:
			c1 = True
		elif l == 600 and s[0] > 500 and s[0] <= 600:
			c1 = True
		elif l == 800 and s[0] > 600 and s[0] <= 800:
			c1 = True
	for s in stats2:
		if l == 100 and s[0] <= 100:
			c2 = True
		elif l == 300 and s[0] > 100 and s[0] <= 300:
			c2 = True
		elif l == 500 and s[0] > 300 and s[0] <= 500:
			c2 = True
		elif l == 600 and s[0] > 500 and s[0] <= 600:
			c2 = True
		elif l == 800 and s[0] > 600 and s[0] <= 800:
			c2 = True
	if c1 and c2:
		return True
	else:
		return False

def both_have_pk(cid, did):
	try:
		conn = psycopg2.connect(
			database=db_name,
			user=db_user,
			password=db_pass,
			host=db_host,
			port=db_port
		)
		cursor = conn.cursor()
		cursor.execute("SELECT stats FROM pcatches WHERE user_id = %s", (cid,))
		stats1 = cursor.fetchall()
		cursor.execute("SELECT stats FROM pcatches WHERE user_id = %s", (did,))
		stats2 = cursor.fetchall()
		if len(stats1) == 0 or len(stats2) == 0:
			return False
		else:
			l = get_league(cid)
			if check_stats(stats1, stats2, l):
				return True
			else:
				return False
	except (Exception, psycopg2.Error) as error:
		print("Error while connecting to PostgreSQL", error)
	finally:
		if conn:
			cursor.close()
			conn.close()

def pk_in_league(pid, id):
	try:
		conn = psycopg2.connect(
			database=db_name,
			user=db_user,
			password=db_pass,
			host=db_host,
			port=db_port
		)
		cursor = conn.cursor()
		cursor.execute("SELECT stats FROM pcatches WHERE user_id = %s AND pk_id = %s", (id, pid))
		stats = cursor.fetchone()
		if stats == None:
			return False
		else:
			cursor.execute("SELECT league FROM pusers WHERE user_id = %s", (id,))
			l = cursor.fetchone()[0]
			if l == 100 and stats[0] <= 100:
				return True
			elif l == 300 and stats[0] > 100 and stats[0] <= 300:
				return True
			elif l == 500 and stats[0] > 300 and stats[0] <= 500:
				return True
			elif l == 600 and stats[0] > 500 and stats[0] <= 600:
				return True
			elif l == 800 and stats[0] > 600 and stats[0] <= 800:
				return True
			else:
				return False
	except (Exception, psycopg2.Error) as error:
		print("Error while connecting to PostgreSQL", error)
	finally:
		if conn:
			cursor.close()
			conn.close()

def n_l(id):
	try:
		conn = psycopg2.connect(
			database=db_name,
			user=db_user,
			password=db_pass,
			host=db_host,
			port=db_port
		)
		cursor = conn.cursor()
		cursor.execute("SELECT league FROM pusers WHERE user_id = %s", (id,))
		l = cursor.fetchone()[0]
		if l == None:
			return 0
		else:
			if l == 100:
				return 100
			elif l == 300:
				return 100
			elif l == 500:
				return 300
			elif l == 600:
				return 500
			elif l == 800:
				return 600
	except (Exception, psycopg2.Error) as error:
		print("Error while connecting to PostgreSQL", error)
	finally:
		if conn:
			cursor.close()
			conn.close()