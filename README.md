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

Start the server from root directory of the repository (must be Python 3+).

```
python python/webapp/app.py
```

Navigate your browser to http://localhost:5000

