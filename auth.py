from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from models.schemas import UserCredential, Database, UserPreference
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint("auth", __name__)
SECRET_KEY = "aameen@2710"

db = Database()

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data["username"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(current_user, *args, **kwargs)
    return wrapper

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    session = db.get_session()
    try:
        hashed_pw = generate_password_hash(password)
        user = UserCredential(username=username, password_hash=hashed_pw)
        session.add(user)
        session.commit()
        return jsonify({"message": "Registered successfully"}), 201
    except IntegrityError:
        session.rollback()
        return jsonify({"error": "Username already exists"}), 400
    finally:
        session.close()

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    session = db.get_session()
    user = session.query(UserCredential).filter_by(username=username).first()
    session.close()

    if user and check_password_hash(user.password_hash, password):
        token = jwt.encode({
            "username": username,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, SECRET_KEY, algorithm="HS256")
        return jsonify({"token": token}), 200

    return jsonify({"error": "Invalid credentials"}), 401


@auth_bp.route("/update-preferences", methods=["POST"])
@token_required
def update_preferences(current_user):
    data = request.get_json()
    keywords = data.get("keywords", [])

    if not isinstance(keywords, list):
        return jsonify({"error": "Keywords must be a list"}), 400

    session = db.get_session()
    try:
        user = session.query(UserCredential).filter_by(username=current_user).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        session.query(UserPreference).filter_by(user_id=user.id).delete()

        for keyword in set(keywords):  
            pref = UserPreference(user_id=user.id, keyword=keyword)
            session.add(pref)

        session.commit()
        return jsonify({"message": "Preferences updated successfully"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        session.close()
