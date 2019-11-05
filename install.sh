sudo apt install python3 python3-pip wget unzip

pip3 install -r requirements.txt

python3 setup.py

wget https://stockfishchess.org/files/stockfish-10-linux.zip
unzip -p stockfish-10-linux.zip stockfish-10-linux/Linux/stockfish_10_x64 > stockfish.bin

rm stockfish-10-linux.zip
chmod +x stockfish.bin