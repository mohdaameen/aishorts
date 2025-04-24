from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_apscheduler import APScheduler
from auth import auth_bp, token_required
import os
import json
from utils.youtube import process_all_users
from sqlalchemy.orm import joinedload
from utils.rss import process_blog_feed_for_all_users
from models.schemas import Database, Tag, UserTagMap, UserCredential, Summary
from datetime import datetime, timedelta


db = Database()


app = Flask(__name__)
CORS(app)
app.register_blueprint(auth_bp)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

scheduler.add_job(id='youtube_summary_job', func=process_all_users, trigger='interval', seconds=300)
scheduler.add_job(id='blog_summary_job', func=process_blog_feed_for_all_users, trigger='interval', seconds=300)

@app.route("/", methods=["GET"])
def index():
    return {"message": "YouTube Summary Backend is Running 🎬"}

@app.route("/summaries", methods=["GET"])
@token_required
def get_user_summaries(user):
    print(user)
    session = db.get_session()
    try:
        tag_names = [name for (name,) in session.query(Tag.name)
                     .join(UserTagMap)
                     .filter(UserTagMap.user_id == user.id)
                     .all()]
        print(tag_names)

        if not tag_names:
            return jsonify([])

        cutoff_date = datetime.utcnow() - timedelta(days=7)

        summaries = (
            session.query(Summary)
            .join(Summary.tags)
            .filter(
                Tag.name.in_(tag_names),
                Summary.created_at >= cutoff_date 
            )
            .options(joinedload(Summary.tags))
            .distinct()
            .all()
        )
        
        if not summaries:
            return jsonify([])

        summary_list = []
        for summary in summaries:
            summary_list.append({
                "title": summary.title,
                "summary": summary.summary,
                "category": summary.category,
                "tags": [tag.name for tag in summary.tags],
                "source": summary.source
            })

        return jsonify(summary_list)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()




@app.route("/tags", methods=["GET"])
@token_required
def get_all_tags(current_user):
    print(current_user)
    session = db.get_session()
    try:
        user = session.query(UserCredential).filter_by(id=current_user.id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        selected_tag_ids = [tag.id for tag in user.tags]

        unselected_tags = session.query(Tag).filter(~Tag.id.in_(selected_tag_ids)).all()
        tag_names = [tag.name for tag in unselected_tags]

        return jsonify(tag_names)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()




@app.route("/set-user-tags", methods=["POST"])
@token_required
def set_user_tags(current_user):
    session = db.get_session()
    try:
        tag_list = request.json.get("tags", [])
        if not tag_list:
            return jsonify({"error": "No tags provided"}), 400

        session.query(UserTagMap).filter_by(user_id=current_user.id).delete()

        for tag_name in tag_list:
            tag = session.query(Tag).filter_by(name=tag_name.lower()).first()
            if tag:
                user_tag_map = UserTagMap(user_id=current_user.id, tag_id=tag.id)
                session.add(user_tag_map)

        session.commit()
        return jsonify({"message": "Tags updated successfully"})
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()



if __name__ == "__main__":

    app.run(debug=True,use_reloader=False, host="0.0.0.0", port=5050)

