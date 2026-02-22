from fastapi import APIRouter, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from bson import ObjectId
from datetime import datetime
from app.db import get_db, ensure_writable
from app.models import ReceiptCreate, ReceiptUpdate

router = APIRouter(prefix="/api/receipts", tags=["Receipts"])

CUISINES = [
    "Italian", "Asian", "Mexican", "Indian",
    "American", "French", "Mediterranean"
]


@router.post("/", status_code=201)
def create_receipt(
    data: ReceiptCreate,
    Authorize: AuthJWT = Depends()
):
    Authorize.jwt_required()
    ensure_writable()

    if data.cuisine not in CUISINES:
        raise HTTPException(400, "Invalid cuisine")

    user_id = Authorize.get_jwt_subject()
    db = get_db()

    db.receipts.insert_one({
        "user_id": ObjectId(user_id),
        "name": data.name,
        "cuisine": data.cuisine,
        "ingredients": [i.strip() for i in data.ingredients.split(",")],
        "youtube_link": data.youtube_link,
        "created_at": datetime.utcnow(),
    })

    return {"msg": "Receipt created"}


@router.get("/dashboard")
def dashboard(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    db = get_db()

    try:
        receipts = list(
            db.receipts.find({"user_id": ObjectId(user_id)})
            .sort("created_at", -1)
            .limit(10)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    return [{
        "id": str(r["_id"]),
        "name": r["name"],
        "cuisine": r["cuisine"],
        "ingredients": r["ingredients"],
        "youtube_link": r["youtube_link"],
    } for r in receipts]

@router.delete("/{receipt_id}", status_code=200)
def delete_receipt(
    receipt_id: str,
    Authorize: AuthJWT = Depends()
):
    Authorize.jwt_required()
    ensure_writable()

    user_id = Authorize.get_jwt_subject()
    db = get_db()

    # Validate ObjectId format
    try:
        receipt_obj_id = ObjectId(receipt_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid receipt id")

    # Ensure receipt belongs to authenticated user
    receipt = db.receipts.find_one({
        "_id": receipt_obj_id,
        "user_id": ObjectId(user_id)
    })

    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    db.receipts.delete_one({"_id": receipt_obj_id})

    return {"msg": "Receipt deleted successfully"}