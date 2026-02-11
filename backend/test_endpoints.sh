#!/bin/bash

echo "================================"
echo "API ENDPOINT TESTS"
echo "================================"

# Test 1: Root
echo -e "\n1. Testing Root Endpoint..."
curl -s http://localhost:8000/ | jq .

# Test 2: Health
echo -e "\n2. Testing Health Check..."
curl -s http://localhost:8000/health | jq .

# Test 3: Chat
echo -e "\n3. Testing Chat Endpoint..."
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I am a farmer in Bihar", "conversation_history": []}' | jq .

# Test 4: List Schemes
echo -e "\n4. Testing List Schemes..."
curl -s "http://localhost:8000/schemes?limit=5" | jq '.total'

echo -e "\n================================"
echo "Tests complete!"
echo "================================"
