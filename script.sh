sudo docker stop $(sudo docker ps -q -f ancestor=auto-keka)
sudo docker build -t auto-keka . --no-cache
sudo docker run -dp 5000:5000 auto-keka