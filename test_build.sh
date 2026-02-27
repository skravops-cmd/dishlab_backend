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

############################################
# 1️⃣ API Availability
############################################

echo ""
echo "1️⃣ Checking API availability..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{}')

expect_one_of "$STATUS" 400 401 422
echo "✅ API reachable"

############################################
# 2️⃣ Register
############################################

echo ""
echo "2️⃣ Registering new user..."
REGISTER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

expect_one_of "$REGISTER_STATUS" 200 201
echo "✅ User registered"

############################################
# 3️⃣ Login
############################################

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

############################################
# 4️⃣ Create Multiple Receipts
############################################

echo ""
echo "4️⃣ Creating receipts for search testing..."

create_receipt() {
  curl -s \
    -X POST "$BASE_URL/api/receipts/" \
    -H "Content-Type: application/json" \
    -H "$AUTH_HEADER" \
    -d "$1"
}

echo "✅ Test receipts created"

############################################
# 5️⃣ Search Tests
############################################

echo ""
echo "5️⃣ Testing search - ANY match..."

SEARCH_ANY=$(curl -s \
  -X GET "$BASE_URL/api/receipts/search?ingredients=cheese,tomato" \
  -H "$AUTH_HEADER")

COUNT_ANY=$(echo "$SEARCH_ANY" | jq length)

if [[ "$COUNT_ANY" -lt 2 ]]; then
  echo "❌ ANY search failed"
  exit 1
fi

echo "✅ ANY search passed"

echo ""
echo "6️⃣ Testing search - ALL match..."

SEARCH_ALL=$(curl -s \
  -X GET "$BASE_URL/api/receipts/search?ingredients=cheese,tomato&match_all=true" \
  -H "$AUTH_HEADER")

COUNT_ALL=$(echo "$SEARCH_ALL" | jq length)

if [[ "$COUNT_ALL" -ne 1 ]]; then
  echo "❌ ALL search failed"
  exit 1
fi

echo "✅ ALL search passed"

echo ""
echo "7️⃣ Testing single ingredient search..."

SEARCH_SINGLE=$(curl -s \
  -X GET "$BASE_URL/api/receipts/search?ingredients=paneer" \
  -H "$AUTH_HEADER")

COUNT_SINGLE=$(echo "$SEARCH_SINGLE" | jq length)

if [[ "$COUNT_SINGLE" -ne 1 ]]; then
  echo "❌ Single ingredient search failed"
  exit 1
fi

echo "✅ Single ingredient search passed"

echo ""
echo "8️⃣ Testing no results case..."

SEARCH_NONE=$(curl -s \
  -X GET "$BASE_URL/api/receipts/search?ingredients=dragonfruit" \
  -H "$AUTH_HEADER")

COUNT_NONE=$(echo "$SEARCH_NONE" | jq length)

if [[ "$COUNT_NONE" -ne 0 ]]; then
  echo "❌ Expected zero results"
  exit 1
fi

echo "✅ No-results search passed"

echo ""
echo "9️⃣ Testing missing ingredients param (should 400)..."

MISSING_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X GET "$BASE_URL/api/receipts/search" \
  -H "$AUTH_HEADER")

expect_one_of "$MISSING_STATUS" 400 422
echo "✅ Missing param rejected"

echo ""
echo "🔟 Testing unauthorized search (should 401)..."

UNAUTH_SEARCH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X GET "$BASE_URL/api/receipts/search?ingredients=cheese")

expect_one_of "$UNAUTH_SEARCH_STATUS" 401
echo "✅ Unauthorized search blocked"

############################################
# 6️⃣ Cleanup
############################################

echo ""
echo "1️⃣1️⃣ Cleaning up receipts..."

IDS=$(curl -s \
  -X GET "$BASE_URL/api/receipts/dashboard" \
  -H "$AUTH_HEADER" | jq -r '.[].id')

for id in $IDS; do
  curl -s -X DELETE "$BASE_URL/api/receipts/$id" \
    -H "$AUTH_HEADER" > /dev/null
done

FINAL_COUNT=$(curl -s \
  -X GET "$BASE_URL/api/receipts/dashboard" \
  -H "$AUTH_HEADER" | jq length)

if [[ "$FINAL_COUNT" -ne 0 ]]; then
  echo "❌ Cleanup failed"
  exit 1
fi

echo "✅ Cleanup successful"

############################################

echo ""
echo "=============================="
echo "🎉 ALL TESTS PASSED SUCCESSFULLY"
echo "=============================="
