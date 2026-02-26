from fastapi import APIRouter, Depends, HTTPException
from fastapi_jwt_auth import AuthJWT
from bson import ObjectId
from datetime import datetime
from pymongo import ReturnDocument

from app.db import get_db, ensure_writable
from app.models import ReceiptCreate, ReceiptUpdate

router = APIRouter(prefix="/api/receipts", tags=["Receipts"])

CUISINES = [
    "Italian", "Asian", "Mexican", "Indian",
    "American", "French", "Mediterranean"
]


def get_current_user_object_id(Authorize: AuthJWT) -> ObjectId:
    user_id = Authorize.get_jwt_subject()

    if not isinstance(user_id, str):
        raise HTTPException(status_code=401, detail="Invalid token subject")

    try:
        return ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid user id")


@router.post("/", status_code=201)
def create_receipt(
    data: ReceiptCreate,
    Authorize: AuthJWT = Depends(),
    db=Depends(get_db),
):
    Authorize.jwt_required()
    ensure_writable()

    if data.cuisine not in CUISINES:
        raise HTTPException(status_code=400, detail="Invalid cuisine")

    user_obj_id = get_current_user_object_id(Authorize)

    result = db.receipts.insert_one({
        "user_id": user_obj_id,
        "name": data.name,
        "cuisine": data.cuisine,
        "ingredients": [i.strip() for i in data.ingredients.split(",")],
        "youtube_link": data.youtube_link,
        "created_at": datetime.utcnow(),
    })

    return {"id": str(result.inserted_id)}


@router.get("/dashboard")
def dashboard(
    Authorize: AuthJWT = Depends(),
    db=Depends(get_db),
):
    Authorize.jwt_required()

    user_obj_id = get_current_user_object_id(Authorize)

    receipts = list(
        db.receipts.find({"user_id": user_obj_id})
        .sort("created_at", -1)
        .limit(10)
    )

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
    Authorize: AuthJWT = Depends(),
    db=Depends(get_db),
):
    Authorize.jwt_required()
    ensure_writable()

    user_obj_id = get_current_user_object_id(Authorize)

    try:
        receipt_obj_id = ObjectId(receipt_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid receipt id")

    deleted = db.receipts.delete_one({
        "_id": receipt_obj_id,
        "user_id": user_obj_id
    })

    if deleted.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return {"msg": "Receipt deleted successfully"}


@router.put("/{receipt_id}", status_code=200)
def update_receipt(
    receipt_id: str,
    data: ReceiptUpdate,
    Authorize: AuthJWT = Depends(),
    db=Depends(get_db),
):
    Authorize.jwt_required()
    ensure_writable()

    user_obj_id = get_current_user_object_id(Authorize)

    try:
        receipt_obj_id = ObjectId(receipt_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid receipt id")

    update_data = {}

    if data.name is not None:
        update_data["name"] = data.name

    if data.cuisine is not None:
        if data.cuisine not in CUISINES:
            raise HTTPException(status_code=400, detail="Invalid cuisine")
        update_data["cuisine"] = data.cuisine

    if data.ingredients is not None:
        update_data["ingredients"] = [
            i.strip() for i in data.ingredients.split(",")
        ]

    if data.youtube_link is not None:
        update_data["youtube_link"] = data.youtube_link

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    updated = db.receipts.find_one_and_update(
        {"_id": receipt_obj_id, "user_id": user_obj_id},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return {
        "id": str(updated["_id"]),
        "name": updated["name"],
        "cuisine": updated["cuisine"],
        "ingredients": updated["ingredients"],
        "youtube_link": updated["youtube_link"],
    }