sudo docker build -t auto-keka . --no-cache
sudo docker run -dp 5000:5000 auto-keka