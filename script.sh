alias d='sudo docker'
alias dstop='sudo docker stop $(sudo docker ps -q -f ancestor=auto-keka)'
alias dbuild='sudo docker build -t auto-keka . --no-cache'
alias drun='sudo docker run -dp 5000:5000 auto-keka'
alias dexec='sudo docker exec -it $(sudo docker ps -q -f ancestor=auto-keka) /bin/bash'
alias dlogs='sudo docker logs $(sudo docker ps -q -f ancestor=auto-keka)'

dstop
dbuild
drun