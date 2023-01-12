sudo docker build -t auto-keka . --no-cache
sudo docker run -dp 8000:8000 auto-keka