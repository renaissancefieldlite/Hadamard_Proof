#!/bin/bash
cd "$(dirname "$0")"

mkdir -p runs

nohup python3 -u williamson_search.py --order 428 --steps 50000 --batch 32 --seed 428 > runs/order_428.log 2>&1 </dev/null &
echo $! > runs/order_428.pid

nohup python3 -u williamson_search.py --order 668 --steps 50000 --batch 32 --seed 668 > runs/order_668.log 2>&1 </dev/null &
echo $! > runs/order_668.pid

echo "Started Hadamard searches:"
echo "  428 PID: $(cat runs/order_428.pid)"
echo "  668 PID: $(cat runs/order_668.pid)"
