sudo apt install python3 python3-pip wget unzip

pip3 install -r requirements.txt

mkdir stockfish-10-linux
python3 setup.py

wget https://stockfishchess.org/files/stockfish-10-linux.zip
mkdir stockfish-10-linux
unzip -p stockfish-10-linux.zip stockfish-10-linux/Linux/stockfish_10_x64 > stockfish-10-linux/stockfish_10_x64
unzip -p stockfish-10-linux.zip stockfish-10-linux/Linux/stockfish_10_x64_modern > stockfish-10-linux/stockfish_10_x64_modern
unzip -p stockfish-10-linux.zip stockfish-10-linux/Linux/stockfish_10_x64_bmi2 > stockfish-10-linux/stockfish_10_x64_bmi2

chmod +x stockfish-10-linux/stockfish_10_x64 
chmod +x stockfish-10-linux/stockfish_10_x64_modern 
chmod +x stockfish-10-linux/stockfish_10_x64_bmi2

# rm stockfish-10-linux.zip