from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token
from datetime import datetime
from ..extensions import bcrypt

auth_bp = Blueprint("auth", __name__)


def get_db():
    return current_app.extensions["mongo"].db


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user
    ---
    tags:
      - Auth
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - email
              - password
            properties:
              email:
                type: string
                example: user@dishlab.dev
              password:
                type: string
                example: StrongPassword123!
    responses:
      201:
        description: User created
      400:
        description: User already exists
    """

    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"msg": "Email and password required"}), 400

    db = get_db()

    if db.users.find_one({"email": email}):
        return jsonify({"msg": "User already exists"}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

    db.users.insert_one({
        "email": email,
        "password": hashed_pw,
        "created_at": datetime.utcnow()
    })

    return jsonify({"msg": "User created"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Login and receive JWT token
    ---
    tags:
      - Auth
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - email
              - password
            properties:
              email:
                type: string
              password:
                type: string
    responses:
      200:
        description: JWT token returned
      401:
        description: Bad credentials
    """

    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"msg": "Email and password required"}), 400

    db = get_db()
    user = db.users.find_one({"email": email})

    if not user or not bcrypt.check_password_hash(user["password"], password):
        return jsonify({"msg": "Bad credentials"}), 401

    access_token = create_access_token(identity=str(user["_id"]))
    return jsonify(access_token=access_token), 200
