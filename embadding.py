#my_app/layout.py

import dash_html_components as html

layout = html.Div([
    html.Button('Click me', id='btn'),
    html.Div(id='output')
])

#my_app/callbacks.py

from dash.dependencies import Output, Input

def register_callbacks(app):

    @app.callback(Output('output', 'children'), [Input('btn', 'n_clicks')])
    def on_click(n_clicks):
        return 'Clicked {} times'.format(n_clicks)


#app.py

import dash
from my_app.layout import layout
from my_app.callbacks import register_callbacks

app = dash.Dash
app.layout = layout
register_callbacks(app)




praskovy commented on Oct 31, 2018 • 
edited 
Hey @numpynewb , maybe if it would be interesting for you, I found a solution :)

@Volodymyrk suggested this structure: #70 and it perfectly worked for my case - allowed me to render the .html template and return my Dash apps.

Thank you, @Volodymyrk!
################################################
server.py
from flask import Flask
server = Flask(__name__)

app1.py
import dash
from server import server
app = dash.Dash(name='app1', sharing=True, server=server, url_base_pathname='/app1')

app2.py
import dash
from server import server
app = dash.Dash(name='app2', sharing=True, server=server, url_base_pathname='/app2')

run.py
from server import server
from app1 import app as app1
from app2 import app as app2
if __name__ == '__main__':
server.run()

########################################
Thanks a lot!
 👍 4
 @ned2 ned2 mentioned this issue on Oct 31, 2018
Documenting strategies for embedding Dash apps in an existing Flask app #246
 Closed
@ned2
  
Contributor
ned2 commented on Oct 31, 2018
Just a heads up that I'm keen to finally get something into the docs about this and have created an issue over at plotly/dash-docs#246. If you have any thoughts to add about the strategies I've suggested there, or any additional strategies, please chime in :)
 @pukkinming pukkinming mentioned this issue on Nov 10, 2018
The link to app.py gist is not working #456
 Open
@sidd-hart
  
sidd-hart commented on Dec 3, 2018
Hey @numpynewb , maybe if it would be interesting for you, I found a solution :)

@Volodymyrk suggested this structure: #70 and it perfectly worked for my case - allowed me to render the .html template and return my Dash apps.

Thank you, @Volodymyrk!
################################
server.py
from flask import Flask
server = Flask(__name__)

app1.py
import dash
from server import server
app = dash.Dash(name='app1', sharing=True, server=server, url_base_pathname='/app1')

app2.py
import dash
from server import server
app = dash.Dash(name='app2', sharing=True, server=server, url_base_pathname='/app2')

run.py
from server import server
from app1 import app as app1
from app2 import app as app2
if __name__ == '__main__':
server.run()
#######################################
Thanks a lot!
Were you able to use flask-login with this solution?
 👍 2
 @numpynewb
  
numpynewb commented on Dec 14, 2018 • 
edited 
That does indeed seem to work, and in a more concise way. Awesome PR! That in combination with guidance in #377 as @rmarren1 suggests makes this actually quite simple and natural. Dash is really moving fast :)
 @Motta23
  
Motta23 commented on Dec 24, 2018
I had been struggling with this, and might have found a solution by cobbling together a few things that I found on Stack Overflow and deep within other GitHub threads:
######################################################


from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.serving import run_simple
import flask
from flask import Flask, Response, redirect, url_for, request, session, abort
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user 
from dash import Dash
import dash_html_components as html


def protect_views(app):
    for view_func in app.server.view_functions:
        if view_func.startswith(app.url_base_pathname):
            app.server.view_functions[view_func] = login_required(app.server.view_functions[view_func])
    
    return app


server = flask.Flask(__name__)

server.config.update(
    DEBUG = True,
    SECRET_KEY = 'secret_xxx'
)

# flask-login
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = "login"


# user model
class User(UserMixin):

    def __init__(self, id):
        self.id = id
        self.name = str(id)
        self.password = "secret"
        
    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password)


# create some users with ids 1 to 20       
users = [User("numpynewb")]
 
# somewhere to login
@server.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']        
        if password == "secret":
            id = username
            user = User(id)
            login_user(user)
            return flask.redirect(request.args.get("next"))
        else:
            return abort(401)
    else:
        return Response('''
        <form action="" method="post">
            <p><input type=text name=username>
            <p><input type=password name=password>
            <p><input type=submit value=Login>
        </form>
        ''')

# somewhere to logout
@server.route("/logout")
@login_required
def logout():
    logout_user()
    return Response('<p>Logged out</p>')


# handle login failed
@server.errorhandler(401)
def page_not_found(e):
    return Response('<p>Login failed</p>')
    
    
# callback to reload the user object        
@login_manager.user_loader
def load_user(userid):
    return User(userid)

dash_app1 = Dash(__name__, server = server, url_base_pathname='/dashboard' )
dash_app2 = Dash(__name__, server = server, url_base_pathname='/reports')
dash_app1.layout = html.Div([html.H1('Hi there, I am app1 for dashboards')])
dash_app2.layout = html.Div([html.H1('Hi there, I am app2 for reports')])


dash_app1 = protect_views(dash_app1)
dash_app2 = protect_views(dash_app2)

@server.route('/')
@server.route('/hello')
@login_required
def hello():
    return 'hello world!'

@server.route('/dashboard')
def render_dashboard():
    return flask.redirect('/dash1')


@server.route('/reports')
def render_reports():
    return flask.redirect('/dash2')


app = DispatcherMiddleware(server, {
    '/dash1': dash_app1.server,
    '/dash2': dash_app2.server
})

run_simple('0.0.0.0', 8080, app, use_reloader=True, use_debugger=True)
#############################################
Let me know if anyone finds this useful!