import os
import urllib
import os
import MySQLdb
import jinja2
import webapp2
import json
import random
import string

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)




def connect_to_cloudsql():
    # These environment variables are configured in app.yaml.
    CLOUDSQL_CONNECTION_NAME = os.environ.get('CLOUDSQL_CONNECTION_NAME')
    CLOUDSQL_USER = os.environ.get('CLOUDSQL_USER')
    CLOUDSQL_PASSWORD = os.environ.get('CLOUDSQL_PASSWORD')

    # When deployed to App Engine, the `SERVER_SOFTWARE` environment variable
    # will be set to 'Google App Engine/version'.
    if os.getenv('SERVER_SOFTWARE', '').startswith('Google App Engine/'):
        # Connect using the unix socket located at
        # /cloudsql/cloudsql-connection-name.
        cloudsql_unix_socket = os.path.join(
            '/cloudsql', CLOUDSQL_CONNECTION_NAME)

        db = MySQLdb.connect(
            unix_socket=cloudsql_unix_socket,
            user=CLOUDSQL_USER,
            db="prisonDatabase",
            passwd=CLOUDSQL_PASSWORD)

    # # If the unix socket is unavailable, then try to connect using TCP. This
    # # will work if you're running a local MySQL server or using the Cloud SQL
    # # proxy, for example:
    # #
    # #   $ cloud_sql_proxy -instances=your-connection-name=tcp:3306
    #
    else:
        db = MySQLdb.connect(
            host='127.0.0.1', user=CLOUDSQL_USER, passwd=CLOUDSQL_PASSWORD)

    return db

class TestPage(webapp2.RequestHandler):
    def get(self):
        template_values = {
            'greeting' : "Hello, World!"
        }
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

class Logon(webapp2.RedirectHandler):
    def post(self):
        #connect to database
        db = connect_to_cloudsql()

        #get user data
        logonData = {}
        logonData['username'] = self.request.get('username')
        logonData['password'] = self.request.get('password')

        #find matching query
        cursor = db.cursor()
        cursor.execute("SELECT username FROM inmate WHERE username = %s and password = %s;",
                       (logonData['username'], logonData['password']))
        row = cursor.fetchone()
        cursor.close()

        #test that values are not null
        if row is not None:
            #if not null render user splash page -- this page also will have session data, specifically the username
            template_values = {'username': row[0]}
            template = JINJA_ENVIRONMENT.get_template('splash.html')
            self.response.write(template.render(template_values))

        #if null redirect back to login page
        else:
            message = {'error' : 'username and/or password do not match'}
            template = JINJA_ENVIRONMENT.get_template('start.html')
            self.response.write(template.render(message = message))

    def get(self):
        template = JINJA_ENVIRONMENT.get_template("start.html")
        message = {}
        self.response.write(template.render(message = message))





class Prisoner(webapp2.RedirectHandler):
    def get(self):
        """This end point is used to display all current inmates in the database"""
        template = JINJA_ENVIRONMENT.get_template('prisonerdemo.html')
        self.response.write(template.render())


    def post(self):
        """This end point is used to add an inmate user to the database"""
        #connect to database
        db = connect_to_cloudsql()

        inmateToAdd = {}
        inmateToAdd['fname'] = self.request.get('fname')
        inmateToAdd['minit'] = self.request.get('minit')
        inmateToAdd['lname'] = self.request.get('lname')
        inmateToAdd['dob'] = self.request.get('dob')

        inmateToAdd['username'] = str(inmateToAdd['fname']) + str(inmateToAdd['minit'])+ str(inmateToAdd['lname'])
        inmateToAdd['password'] = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(12))
        inmateToAdd['wallet'] = 100

        cursor = db.cursor()
        cursor.execute("INSERT INTO inmate (fname, minit, lname, dob, username, password, wallet) VALUES (%s, %s, %s, %s, %s, %s, %s);",
                       (inmateToAdd['fname'], inmateToAdd['minit'], inmateToAdd['lname'],
                        inmateToAdd['dob'], inmateToAdd['username'], inmateToAdd['password'],
                        inmateToAdd['wallet']))

        db.commit()
        db.close()

        template_values = {
            "fname" : inmateToAdd['fname'],
            "minit" : inmateToAdd['minit'],
            "lname" : inmateToAdd['lname'],
            "dob":inmateToAdd['dob'],
            "username":inmateToAdd['username'],
            'password':inmateToAdd['password'],
            'wallet': inmateToAdd['wallet']
        }

        #self.response.write(json.dumps(inmateToAdd))
        template = JINJA_ENVIRONMENT.get_template('confirmAdd.html')

        self.response.write(template.render(template_values))



# [START app]
app = webapp2.WSGIApplication([
    ('/', TestPage),
    ('/start.html', Logon),
    ('/logon', Logon),
    ('/prisoner', Prisoner)
], debug=True)
# [END app]
