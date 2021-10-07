#/bin/bash
docker build -t mtg-bot .
docker stop MTG-Bot
docker rm MTG-Bot
docker run -d --name MTG-Bot mtg-bot
