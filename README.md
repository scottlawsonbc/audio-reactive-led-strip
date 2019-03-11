On Linux, install PyAudio headers.

```
sudo apt-get install python3-pyaudio python-pyaudio
```

Install audioled (after cloning repo and in the root directory of the repository).

```
python setup.py develop
```

Install node dependencies

```
npm i express
npm i http
npm i socket.io
npm i readline
```

Open a terminal in the root directory of the repository and run the app.

```
audioled
```

Navigate your browser to http://localhost:5000

