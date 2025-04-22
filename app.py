from flask import Flask, jsonify
from flask_cors import CORS
from flask_apscheduler import APScheduler
from auth import auth_bp, token_required
import os
import json
from utils.youtube import process_all_users
from utils.rss import process_blog_feed_for_all_users
# from models.schemas import Database

# db = Database()


app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_bp)
# db.create_tables()  



scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

scheduler.add_job(id='youtube_summary_job', func=process_all_users, trigger='interval', seconds=12000)
scheduler.add_job(id='blog_summary_job', func=process_blog_feed_for_all_users, trigger='interval', seconds=12000)

@app.route("/", methods=["GET"])
def index():
    return {"message": "YouTube Summary Backend is Running 🎬"}

@app.route("/summaries", methods=["GET"])
@token_required
def get_user_summaries(current_user):
    json_file = f"summaries/{current_user}.json"
    
    if os.path.exists(json_file):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        data = []

    summaries = [entry.get("summary", "") for entry in data]
    return jsonify(summaries)


if __name__ == "__main__":

    app.run(debug=True,use_reloader=False, host="0.0.0.0", port=5050)

