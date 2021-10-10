#/bin/bash
#docker build -t mtg-bot .
docker stop MTG-Bot
docker rm MTG-Bot
docker pull pyaniz/mtg-tbot
docker run -d --name MTG-Bot pyaniz/mtg-tbot
