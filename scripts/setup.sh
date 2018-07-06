# set up the google drive
pip install --upgrade google-api-python-client
curl -s https://raw.githubusercontent.com/gsuitedevs/python-samples/master/drive/quickstart/quickstart.py > google-drive-auth.py
python3 google-drive-auth.py --noauth_local_webserver

# handle the video file and use montage to combine multiple frame image into a big one
pip install youtube-dl # download video from youtube
sudo apt install ffmpeg graphicsmagick-imagemagick-compat
pip install ffmpeg-python # a good tool to handle ffmpeg with python
