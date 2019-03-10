import threading

from subprocess import Popen, PIPE

import wtforms
import flask
import flask_wtf
import flask_bootstrap


class SettingsForm(flask_wtf.FlaskForm):
    source = wtforms.StringField(default='python audioled/mic.py')
    effect = wtforms.StringField(default='python audioled/effect.py spectrum --pixels 100 --rate 30')
    display = wtforms.StringField(default='node ledsocket/server.js')
    submit = wtforms.SubmitField()


app = flask.Flask(__name__)
app.config['WTF_CSRF_ENABLED'] = False
app.config['SECRET_KEY'] = b'123'
flask_bootstrap.Bootstrap(app)

lock = threading.Lock()
source = None
effect = None
display = None


@app.route('/', methods=['GET', 'POST'])
def index():

    global source
    global effect
    global display
    form = SettingsForm()

    if flask.request.method == 'POST' and form.validate():
        with lock:
            for p in (source, effect, display):
                if isinstance(p, Popen):
                    p.kill()

            print(form.source.data)
            print(form.effect.data)
            print(form.display.data)
            print('Starting!')

            try:
                source = Popen(form.source.data, stdout=PIPE)
            except OSError as e:
                form.source.errors.append(e)
                return flask.render_template('index.html', form=form)

            try:
                effect = Popen(form.effect.data, stdin=source.stdout, stdout=PIPE)
            except OSError as e:
                form.effect.errors.append(e)
                return flask.render_template('index.html', form=form)

            try:
                display = Popen(form.display.data, stdin=effect.stdout)
            except OSError as e:
                form.display.errors.append(e)
                return flask.render_template('index.html', form=form)

    return flask.render_template('index.html', form=form)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
