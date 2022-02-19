rm -rf downloaded
rm -rf rate_sampled
rm -rf processed
mkdir processed
mkdir rate_sampled
mkdir downloaded
cd downloaded
youtube-dl --rm-cache-dir --extract-audio --audio-format mp3 -o "%(title)s.%(ext)s" https://www.youtube.com/playlist?list=PLAZ2X-buqv3EcYNIVPTEZj2ins9TldeAK
for FILE in *; do ffmpeg -i "$FILE" -ar 48000 "../rate_sampled/$FILE"; done
cd ../rate_sampled
for FILE in *; do sox -v 0.06 - "$FILE" "../processed/$FILE"; done
cd ..
