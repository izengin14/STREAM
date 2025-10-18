

(
    cd /home/izengin/Desktop/STREAM || exit
    python3 streamtime.py
)& 
sleep 1
(
    cd /home/izengin/Desktop/STREAM || exit
    ./streammod1
)&

wait