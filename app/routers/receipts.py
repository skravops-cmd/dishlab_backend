from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_jwt_auth import AuthJWT
from bson import ObjectId
from datetime import datetime
from pymongo import ReturnDocument

from app.db import get_db, ensure_writable
from app.models import ReceiptCreate, ReceiptUpdate

router = APIRouter(prefix="/api/receipts", tags=["Receipts"])

# Canonical lowercase cuisines
CUISINES = [
    "italian",
    "asian",
    "mexican",
    "indian",
    "american",
    "french",
    "mediterranean",
]


# -------------------------
# Helpers
# -------------------------

def normalize(value: str) -> str:
    return value.strip().lower()


def normalize_ingredients(raw: str) -> List[str]:
    ingredients = [normalize(i) for i in raw.split(",") if i.strip()]
    if not ingredients:
        raise HTTPException(status_code=400, detail="Invalid ingredients provided")
    return ingredients


def get_current_user_object_id(Authorize: AuthJWT) -> ObjectId:
    user_id = Authorize.get_jwt_subject()

    if not isinstance(user_id, str):
        raise HTTPException(status_code=401, detail="Invalid token subject")

    try:
        return ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid user id")


# -------------------------
# Create
# -------------------------

@router.post("/", status_code=201)
def create_receipt(
    data: ReceiptCreate,
    Authorize: AuthJWT = Depends(),
    db=Depends(get_db),
):
    Authorize.jwt_required()
    ensure_writable()

    normalized_cuisine = normalize(data.cuisine)

    if normalized_cuisine not in CUISINES:
        raise HTTPException(status_code=400, detail="Invalid cuisine")

    ingredients = normalize_ingredients(data.ingredients)
    user_obj_id = get_current_user_object_id(Authorize)

    result = db.receipts.insert_one(
        {
            "user_id": user_obj_id,
            "name": data.name.strip(),
            "cuisine": normalized_cuisine,
            "ingredients": ingredients,
            "youtube_link": str(data.youtube_link),
            "created_at": datetime.utcnow(),
        }
    )

    return {"id": str(result.inserted_id)}


# -------------------------
# Dashboard
# -------------------------

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

    return [
        {
            "id": str(r["_id"]),
            "name": r["name"],
            "cuisine": r["cuisine"],
            "ingredients": r["ingredients"],
            "youtube_link": r["youtube_link"],
        }
        for r in receipts
    ]


# -------------------------
# Delete
# -------------------------

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

    deleted = db.receipts.delete_one(
        {"_id": receipt_obj_id, "user_id": user_obj_id}
    )

    if deleted.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Receipt not found")

    return {"msg": "Receipt deleted successfully"}


# -------------------------
# Update
# -------------------------

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
        update_data["name"] = data.name.strip()

    if data.cuisine is not None:
        normalized_cuisine = normalize(data.cuisine)

        if normalized_cuisine not in CUISINES:
            raise HTTPException(status_code=400, detail="Invalid cuisine")

        update_data["cuisine"] = normalized_cuisine

    if data.ingredients is not None:
        update_data["ingredients"] = normalize_ingredients(data.ingredients)

    if data.youtube_link is not None:
        update_data["youtube_link"] = str(data.youtube_link)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided")

    updated = db.receipts.find_one_and_update(
        {"_id": receipt_obj_id, "user_id": user_obj_id},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER,
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


# -------------------------
# Search
# -------------------------

@router.get("/search")
def search_receipts(
    ingredients: Optional[str] = Query(
        None, description="Comma separated ingredients"
    ),
    cuisine: Optional[str] = Query(
        None, description="Cuisine name"
    ),
    match_all: bool = False,
    Authorize: AuthJWT = Depends(),
    db=Depends(get_db),
):
    Authorize.jwt_required()
    user_obj_id = get_current_user_object_id(Authorize)

    query = {"user_id": user_obj_id}

    # Ingredient filter
    if ingredients:
        ingredient_list = normalize_ingredients(ingredients)

        if match_all:
            query["ingredients"] = {"$all": ingredient_list}
        else:
            query["ingredients"] = {"$in": ingredient_list}

    # Cuisine filter
    if cuisine:
        normalized_cuisine = normalize(cuisine)

        if normalized_cuisine not in CUISINES:
            raise HTTPException(status_code=400, detail="Invalid cuisine")

        query["cuisine"] = normalized_cuisine

    receipts = list(
        db.receipts.find(query)
        .sort("created_at", -1)
    )

    return [
        {
            "id": str(r["_id"]),
            "name": r["name"],
            "cuisine": r["cuisine"],
            "ingredients": r["ingredients"],
            "youtube_link": r["youtube_link"],
        }
        for r in receipts
    ]