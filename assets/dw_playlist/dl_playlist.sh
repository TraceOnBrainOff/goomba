rm -rf downloaded
rm -rf processed
mkdir processed
mkdir downloaded
cd downloaded
youtube-dl --rm-cache-dir --extract-audio --audio-format mp3 -o "%(title)s.%(ext)s" https://www.youtube.com/playlist?list=PLAZ2X-buqv3EcYNIVPTEZj2ins9TldeAK
for FILE in *; do sox -v 0.06 "$FILE" "../processed/$FILE"; done
cd ..
