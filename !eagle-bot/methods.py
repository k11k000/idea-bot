import disnake
import datetime
import sqlite3
import json

def startprint(name):
	now = datetime.datetime.now().strftime("%H:%M:%S")
	print (f"[{now}] {name} started.")

def embed(title: str, description: str, color = disnake.Colour.from_rgb(252, 250, 220), timestamp: bool = True):
	embed = disnake.Embed(
		title=title,
		description=description,
		color=color,
	)

	if timestamp:
		embed.timestamp = datetime.datetime.now()
	return embed

def error(text: str):
	embed1 = embed("Произошла ошибка", text, disnake.Colour.red())
	return embed1

def set_rating(user_id: int, idea_id: int, rating: int):
	with sqlite3.connect("ideas.db") as db:
		cursor = db.cursor()
		row = cursor.execute("SELECT likes, dislikes, voted FROM ideas WHERE id = ?", (idea_id,)).fetchone()
		if not row:
			return

		likes, dislikes, voted_json = row
		voted = json.loads(voted_json)

		prev_rating = voted.get(str(user_id), 0)

		if prev_rating == rating:
			return
		
		if prev_rating == 1: 
			likes -= 1
		elif prev_rating == -1:
			dislikes -= 1

		if rating == 1:
			likes += 1
		elif rating == -1:
			dislikes += 1

		voted[str(user_id)] = rating

		cursor.execute("UPDATE ideas SET likes = ?, dislikes = ?, voted = ? WHERE id = ?",
					(likes, dislikes, json.dumps(voted), idea_id))
		db.commit()

def get_rating(idea_id: int):
	with sqlite3.connect("ideas.db") as db:
		cursor = db.cursor()
		row = cursor.execute("SELECT likes, dislikes FROM ideas WHERE id = ?", (idea_id,)).fetchone()
		return row if row else (0, 0)

def bar_generator(likes, dislikes):
    total = likes + dislikes

    rate_likes = likes / total
    bar_length = 25
    fill_length = int(bar_length * rate_likes)
    
    bar = '█' * fill_length + '░' * (bar_length - fill_length)
    return bar

