#!/bin/bash

API="http://127.0.0.1:8000/api"
echo "=== 1. Login Conducteur ==="
DRIVER=$(curl -s -X POST $API/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"jean","password":"testpass123"}')
DRIVER_TOKEN=$(echo $DRIVER | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")
echo "Token conducteur OK"

echo "=== 2. Login Passager ==="
PASS=$(curl -s -X POST $API/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"passager1","password":"testpass123"}')
PASS_TOKEN=$(echo $PASS | python3 -c "import sys,json; print(json.load(sys.stdin)['access'])")
echo "Token passager OK"

echo "=== 3. Créer véhicule ==="
VEH=$(curl -s -X POST $API/vehicles/ \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"brand":"Toyota","model":"Corolla","color":"Gris","plate_number":"CM-TEST-01","seats":4,"year":2020}')
VEH_ID=$(echo $VEH | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
echo "Véhicule ID: $VEH_ID"

echo "=== 4. Créer trajet ==="
TRIP=$(curl -s -X POST $API/trips/ \
  -H "Authorization: Bearer $DRIVER_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"vehicle\":$VEH_ID,\"origin_city\":\"Yaoundé\",\"destination_city\":\"Douala\",\"departure_datetime\":\"2026-10-15T07:30:00+01:00\",\"seats_total\":3,\"price_per_seat\":\"4500.00\"}")
TRIP_ID=$(echo $TRIP | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
echo "Trajet ID: $TRIP_ID"

echo "=== 5. Réserver ==="
BOOK=$(curl -s -X POST $API/bookings/ \
  -H "Authorization: Bearer $PASS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"trip\":$TRIP_ID,\"seats\":1}")
BOOK_ID=$(echo $BOOK | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
echo "Réservation ID: $BOOK_ID — Status: $(echo $BOOK | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))")"

echo "=== 6. Paiement ==="
PAY=$(curl -s -X POST $API/payments/ \
  -H "Authorization: Bearer $PASS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"booking\":$BOOK_ID,\"provider\":\"ORANGE_MONEY\"}")
PAY_ID=$(echo $PAY | python3 -c "import sys,json; print(json.load(sys.stdin).get('id',''))")
echo "Paiement ID: $PAY_ID"

echo "=== 7. Simuler succès paiement ==="
curl -s -X POST $API/payments/$PAY_ID/simulate_success/ \
  -H "Authorization: Bearer $PASS_TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); print('Status:', d.get('status'), '| TX:', d.get('transaction_id'))"

echo "=== 8. Terminer le trajet ==="
curl -s -X POST $API/trips/$TRIP_ID/complete/ \
  -H "Authorization: Bearer $DRIVER_TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin))"

echo "=== 9. Noter le conducteur ==="
curl -s -X POST $API/reviews/ \
  -H "Authorization: Bearer $PASS_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"trip\":$TRIP_ID,\"reviewed_user\":2,\"rating\":5,\"comment\":\"Super trajet !\"}" | python3 -c "import sys,json; d=json.load(sys.stdin); print('Avis:', d.get('rating'), '★')"

echo "=== 10. Notifications passager ==="
curl -s $API/notifications/ \
  -H "Authorization: Bearer $PASS_TOKEN" | python3 -c "import sys,json; data=json.load(sys.stdin); print('Notifications:', data.get('count', len(data.get('results',[]))))"

echo ""
echo "=== FLUX COMPLET TERMINÉ ==="