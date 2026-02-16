#!/usr/bin/env bash
set -euo pipefail

BASE_URL="http://localhost:5000"
EMAIL="testuser$(date +%s)@dishlab.dev"
PASSWORD="StrongPassword123!"

echo "=============================="
echo "🧪 DISHLAB API SMOKE TESTS"
echo "=============================="

echo ""
echo "1️⃣ Checking API availability (auth endpoint)..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{}')

if [[ "$STATUS" != "400" && "$STATUS" != "401" ]]; then
  echo "❌ API not reachable or unexpected status: $STATUS"
  exit 1
fi
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

echo "HTTP $REGISTER_STATUS"
echo "$REGISTER_BODY"

if [[ "$REGISTER_STATUS" != "201" ]]; then
  echo "❌ Registration failed"
  exit 1
fi

echo "$REGISTER_BODY" | jq .
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

if [[ "$DUPLICATE_STATUS" != "400" ]]; then
  echo "❌ Duplicate registration not blocked"
  exit 1
fi
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

echo "HTTP $LOGIN_STATUS"
echo "$LOGIN_BODY"

if [[ "$LOGIN_STATUS" != "200" ]]; then
  echo "❌ Login failed"
  exit 1
fi

TOKEN=$(echo "$LOGIN_BODY" | jq -r '.access_token')

if [[ -z "$TOKEN" || "$TOKEN" == "null" ]]; then
  echo "❌ JWT token missing"
  exit 1
fi

echo "✅ JWT token acquired"
AUTH_HEADER="Authorization: Bearer $TOKEN"

echo ""
echo "5️⃣ Creating receipt (valid cuisine)..."
curl -s -X POST "$BASE_URL/api/receipts/" \
  -H "Content-Type: application/json" \
  -H "$AUTH_HEADER" \
  -d '{
    "name": "Margherita Pizza",
    "cuisine": "Italian",
    "ingredients": "cheese, tomato, basil",
    "youtube_link": "https://youtube.com/watch?v=pizza"
  }' | jq .

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

if [[ "$INVALID_STATUS" != "400" ]]; then
  echo "❌ Invalid cuisine accepted"
  exit 1
fi
echo "✅ Invalid cuisine rejected"

echo ""
echo "7️⃣ Fetching dashboard..."
DASHBOARD=$(curl -s -X GET "$BASE_URL/api/receipts/dashboard" \
  -H "$AUTH_HEADER")

echo "$DASHBOARD" | jq .

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

if [[ "$UNAUTH_STATUS" != "401" ]]; then
  echo "❌ Unauthorized access allowed"
  exit 1
fi

echo "✅ Unauthorized access blocked"

echo ""
echo "=============================="
echo "🎉 ALL TESTS PASSED SUCCESSFULLY"
echo "=============================="

