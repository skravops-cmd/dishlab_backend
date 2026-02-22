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
echo "1️⃣ Checking API availability (auth endpoint)..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{}')

expect_one_of "$STATUS" 400 401 422
echo "✅ API reachable"

echo ""
echo "2️⃣ Registering new user..."
REGISTER_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

REGISTER_BODY=$(echo "$REGISTER_RESPONSE" | head -n1)
REGISTER_STATUS=$(echo "$REGISTER_RESPONSE" | tail -n1)

expect_one_of "$REGISTER_STATUS" 200 201
echo "✅ User registered"

echo ""
echo "3️⃣ Duplicate registration should fail..."
DUPLICATE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

expect_one_of "$DUPLICATE_STATUS" 400 409
echo "✅ Duplicate registration blocked"

echo ""
echo "4️⃣ Logging in..."
LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | head -n1)
LOGIN_STATUS=$(echo "$LOGIN_RESPONSE" | tail -n1)

expect_one_of "$LOGIN_STATUS" 200

TOKEN=$(echo "$LOGIN_BODY" | jq -r '.access_token')

if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "❌ JWT token missing"
  exit 1
fi

AUTH_HEADER="Authorization: Bearer $TOKEN"
echo "✅ JWT token acquired"

echo ""
echo "5️⃣ Creating receipt (valid cuisine)..."
CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "$BASE_URL/api/receipts/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "Margherita Pizza",
    "cuisine": "Italian",
    "ingredients": "cheese, tomato, basil",
    "youtube_link": "https://youtube.com/watch?v=pizza"
  }')

CREATE_STATUS=$(echo "$CREATE_RESPONSE" | tail -n1)
expect_one_of "$CREATE_STATUS" 200 201
echo "✅ Receipt created"

echo ""
echo "6️⃣ Creating receipt with invalid cuisine (should fail)..."
INVALID_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$BASE_URL/api/receipts/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "Alien Dish",
    "cuisine": "Martian",
    "ingredients": "dust",
    "youtube_link": "https://youtube.com/watch?v=alien"
  }')

expect_one_of "$INVALID_STATUS" 400 422
echo "✅ Invalid cuisine rejected"

echo ""
echo "7️⃣ Fetching dashboard..."
DASHBOARD=$(curl -s -X GET "$BASE_URL/api/receipts/dashboard" \
  -H "$AUTH_HEADER")

COUNT=$(echo "$DASHBOARD" | jq length)

if [[ "$COUNT" -lt 1 || "$COUNT" -gt 10 ]]; then
  echo "❌ Dashboard count invalid: $COUNT"
  exit 1
fi

echo "✅ Dashboard returned $COUNT receipts"

echo ""
echo "8️⃣ Unauthorized dashboard access should fail..."
UNAUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X GET "$BASE_URL/api/receipts/dashboard")

expect_one_of "$UNAUTH_STATUS" 401
echo "✅ Unauthorized access blocked"

echo ""
echo "9️⃣ Extracting receipt ID..."
RECEIPT_ID=$(echo "$DASHBOARD" | jq -r '.[0].id')

if [[ -z "$RECEIPT_ID" || "$RECEIPT_ID" == "null" ]]; then
  echo "❌ Failed to extract receipt ID"
  exit 1
fi

echo "✅ Using receipt ID: $RECEIPT_ID"

echo ""
echo "🔟 Deleting receipt (should succeed)..."
DELETE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X DELETE "$BASE_URL/api/receipts/$RECEIPT_ID" \
  -H "$AUTH_HEADER")

expect_one_of "$DELETE_STATUS" 200 204
echo "✅ Receipt deleted"

echo ""
echo "1️⃣1️⃣ Deleting same receipt again (should 404)..."
DELETE_AGAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X DELETE "$BASE_URL/api/receipts/$RECEIPT_ID" \
  -H "$AUTH_HEADER")

expect_one_of "$DELETE_AGAIN_STATUS" 404
echo "✅ Second delete returned 404"

echo ""
echo "1️⃣2️⃣ Deleting with invalid ObjectId (should 400)..."
INVALID_DELETE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X DELETE "$BASE_URL/api/receipts/invalid-id" \
  -H "$AUTH_HEADER")

expect_one_of "$INVALID_DELETE_STATUS" 400
echo "✅ Invalid ID rejected"

echo ""
echo "1️⃣3️⃣ Unauthorized delete attempt (should 401)..."
UNAUTH_DELETE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X DELETE "$BASE_URL/api/receipts/$RECEIPT_ID")

expect_one_of "$UNAUTH_DELETE_STATUS" 401
echo "✅ Unauthorized delete blocked"

echo ""
echo "1️⃣4️⃣ Verifying dashboard is empty..."
NEW_DASHBOARD=$(curl -s -X GET "$BASE_URL/api/receipts/dashboard" \
  -H "$AUTH_HEADER")

NEW_COUNT=$(echo "$NEW_DASHBOARD" | jq length)

if [[ "$NEW_COUNT" -ne 0 ]]; then
  echo "❌ Receipt was not removed from dashboard"
  exit 1
fi

echo "✅ Dashboard reflects deletion"

echo ""
echo "=============================="
echo "🎉 ALL TESTS PASSED SUCCESSFULLY"
echo "=============================="
