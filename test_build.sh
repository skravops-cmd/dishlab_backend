#!/usr/bin/env bash
set -euo pipefail

BASE_URL="http://localhost:8000"
EMAIL="testuser$(date +%s)@dishlab.dev"
PASSWORD="StrongPassword123!"

echo "=============================="
echo "🧪 DISHLAB API SMOKE TESTS"
echo "=============================="

expect_one_of() {
  local status="$1"
  shift
  for code in "$@"; do
    [[ "$status" == "$code" ]] && return 0
  done
  echo "❌ Unexpected status code: $status (expected: $*)"
  exit 1
}

echo ""
echo "1️⃣ Checking API availability..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{}')

expect_one_of "$STATUS" 400 401 422
echo "✅ API reachable"

echo ""
echo "2️⃣ Registering new user..."
REGISTER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

expect_one_of "$REGISTER_STATUS" 200 201
echo "✅ User registered"

echo ""
echo "3️⃣ Logging in..."
LOGIN_RESPONSE=$(curl -s \
  -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')

if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "❌ JWT token missing"
  exit 1
fi

AUTH_HEADER="Authorization: Bearer $TOKEN"
echo "✅ JWT token acquired"

echo ""
echo "4️⃣ Creating receipt..."
CREATE_RESPONSE=$(curl -s \
  -X POST "$BASE_URL/api/receipts/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "Margherita Pizza",
    "cuisine": "Italian",
    "ingredients": "cheese, tomato, basil",
    "youtube_link": "https://youtube.com/watch?v=pizza"
  }')

RECEIPT_ID=$(echo "$CREATE_RESPONSE" | jq -r '.id')

if [[ -z "$RECEIPT_ID" || "$RECEIPT_ID" == "null" ]]; then
  echo "❌ Failed to create receipt"
  exit 1
fi

echo "✅ Receipt created: $RECEIPT_ID"

echo ""
echo "5️⃣ Updating receipt (valid update)..."
UPDATE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X PUT "$BASE_URL/api/receipts/$RECEIPT_ID" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "Updated Pizza",
    "cuisine": "French"
  }')

expect_one_of "$UPDATE_STATUS" 200
echo "✅ Receipt updated successfully"

echo ""
echo "6️⃣ Verifying update reflected in dashboard..."
UPDATED_DASHBOARD=$(curl -s \
  -X GET "$BASE_URL/api/receipts/dashboard" \
  -H "$AUTH_HEADER")

UPDATED_NAME=$(echo "$UPDATED_DASHBOARD" | jq -r '.[0].name')

if [[ "$UPDATED_NAME" != "Updated Pizza" ]]; then
  echo "❌ Update not reflected in dashboard"
  exit 1
fi

echo "✅ Update confirmed"

echo ""
echo "7️⃣ Updating with invalid cuisine (should fail)..."
INVALID_UPDATE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X PUT "$BASE_URL/api/receipts/$RECEIPT_ID" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "cuisine": "Martian"
  }')

expect_one_of "$INVALID_UPDATE_STATUS" 400 422
echo "✅ Invalid cuisine rejected"

echo ""
echo "8️⃣ Updating with empty payload (should fail)..."
EMPTY_UPDATE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X PUT "$BASE_URL/api/receipts/$RECEIPT_ID" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{}')

expect_one_of "$EMPTY_UPDATE_STATUS" 400 422
echo "✅ Empty update rejected"

echo ""
echo "9️⃣ Updating with invalid ObjectId (should 400)..."
BAD_ID_UPDATE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X PUT "$BASE_URL/api/receipts/invalid-id" \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test"}')

expect_one_of "$BAD_ID_UPDATE_STATUS" 400
echo "✅ Invalid ObjectId rejected"

echo ""
echo "🔟 Unauthorized update (should 401)..."
UNAUTH_UPDATE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X PUT "$BASE_URL/api/receipts/$RECEIPT_ID" \
  -H "Content-Type: application/json" \
  -d '{"name":"Hacker"}')

expect_one_of "$UNAUTH_UPDATE_STATUS" 401
echo "✅ Unauthorized update blocked"

echo ""
echo "1️⃣1️⃣ Deleting receipt..."
DELETE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X DELETE "$BASE_URL/api/receipts/$RECEIPT_ID" \
  -H "$AUTH_HEADER")

expect_one_of "$DELETE_STATUS" 200 204
echo "✅ Receipt deleted"

echo ""
echo "1️⃣2️⃣ Dashboard should now be empty..."
FINAL_DASHBOARD=$(curl -s \
  -X GET "$BASE_URL/api/receipts/dashboard" \
  -H "$AUTH_HEADER")

FINAL_COUNT=$(echo "$FINAL_DASHBOARD" | jq length)

if [[ "$FINAL_COUNT" -ne 0 ]]; then
  echo "❌ Receipt not removed"
  exit 1
fi

echo "✅ Dashboard clean"

echo ""
echo "=============================="
echo "🎉 ALL TESTS PASSED SUCCESSFULLY"
echo "==============================":w
