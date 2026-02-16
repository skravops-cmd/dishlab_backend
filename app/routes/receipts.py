from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from datetime import datetime
from flask import abort

receipts_bp = Blueprint("receipts", __name__)

CUISINES = [
    "Italian",
    "Asian",
    "Mexican",
    "Indian",
    "American",
    "French",
    "Mediterranean",
]


def get_db():
    return current_app.extensions["mongo"].db


def ensure_writable():
    if current_app.config.get("MONGO_READ_ONLY"):
        abort(403, description="Read-only environment")


@receipts_bp.route("/", methods=["POST"])
@jwt_required()
def create_receipt():
    """
    Create a new receipt
    ---
    tags:
      - Receipts
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - name
              - cuisine
              - ingredients
              - youtube_link
            properties:
              name:
                type: string
                example: Margherita Pizza
              cuisine:
                type: string
                example: Italian
              ingredients:
                type: string
                example: cheese, tomato, basil
              youtube_link:
                type: string
                example: https://youtube.com/watch?v=pizza
    responses:
      201:
        description: Receipt created
      400:
        description: Invalid input
      401:
        description: Unauthorized
    """

    ensure_writable()
    data = request.get_json() or {}

    required = ["name", "cuisine", "ingredients", "youtube_link"]
    if not all(k in data for k in required):
        return jsonify({"msg": "Missing fields"}), 400

    if data["cuisine"] not in CUISINES:
        return jsonify({"msg": "Invalid cuisine"}), 400

    db = get_db()
    user_id = get_jwt_identity()

    receipt = {
        "user_id": ObjectId(user_id),
        "name": data["name"],
        "cuisine": data["cuisine"],
        "ingredients": [i.strip() for i in data["ingredients"].split(",")],
        "youtube_link": data["youtube_link"],
        "created_at": datetime.utcnow(),
    }

    db.receipts.insert_one(receipt)
    return jsonify({"msg": "Receipt created"}), 201


@receipts_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    """
    Get last 10 receipts for current user
    ---
    tags:
      - Receipts
    security:
      - bearerAuth: []
    responses:
      200:
        description: List of receipts
      401:
        description: Unauthorized
    """

    db = get_db()
    user_id = get_jwt_identity()

    receipts = list(
        db.receipts.find({"user_id": ObjectId(user_id)})
        .sort("created_at", -1)
        .limit(10)
    )

    for r in receipts:
        r["_id"] = str(r["_id"])
        r["user_id"] = str(r["user_id"])

    return jsonify(receipts), 200


@receipts_bp.route("/<receipt_id>", methods=["PUT"])
@jwt_required()
def update_receipt(receipt_id):
    """
    Update an existing receipt
    ---
    tags:
      - Receipts
    security:
      - bearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              name:
                type: string
              cuisine:
                type: string
              ingredients:
                type: string
              youtube_link:
                type: string
    responses:
      200:
        description: Receipt updated
      400:
        description: Invalid input
      401:
        description: Unauthorized
      404:
        description: Receipt not found
    """
    ensure_writable()
    data = request.get_json() or {}
    db = get_db()
    user_id = get_jwt_identity()

    receipt = db.receipts.find_one(
        {"_id": ObjectId(receipt_id), "user_id": ObjectId(user_id)}
    )
    if not receipt:
        return jsonify({"msg": "Receipt not found"}), 404

    updates = {}
    if "name" in data:
        updates["name"] = data["name"]
    if "cuisine" in data:
        if data["cuisine"] not in CUISINES:
            return jsonify({"msg": "Invalid cuisine"}), 400
        updates["cuisine"] = data["cuisine"]
    if "ingredients" in data:
        updates["ingredients"] = [i.strip() for i in data["ingredients"].split(",")]
    if "youtube_link" in data:
        updates["youtube_link"] = data["youtube_link"]

    if updates:
        db.receipts.update_one({"_id": ObjectId(receipt_id)}, {"$set": updates})

    return jsonify({"msg": "Receipt updated"}), 200


@receipts_bp.route("/<receipt_id>", methods=["DELETE"])
@jwt_required()
def delete_receipt(receipt_id):
    """
    Delete a receipt
    ---
    tags:
      - Receipts
    security:
      - bearerAuth: []
    responses:
      200:
        description: Receipt deleted
      401:
        description: Unauthorized
      404:
        description: Receipt not found
    """
    ensure_writable()
    db = get_db()
    user_id = get_jwt_identity()

    result = db.receipts.delete_one(
        {"_id": ObjectId(receipt_id), "user_id": ObjectId(user_id)}
    )
    if result.deleted_count == 0:
        return jsonify({"msg": "Receipt not found"}), 404

    return jsonify({"msg": "Receipt deleted"}), 200
