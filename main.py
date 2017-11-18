import os
import urllib
import os
import MySQLdb
import jinja2
import webapp2
import json

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
        inmateToAdd['lname'] = self.request.get('lname')
        inmateToAdd['dob'] = self.request.get('dob')

        cursor = db.cursor()
        cursor.execute("INSERT INTO inmate (fname, lname, dob) VALUES (%s, %s, %s);", (inmateToAdd['fname'],inmateToAdd['lname'], inmateToAdd['dob']))

        db.commit()
        db.close()

        self.response.write(json.dumps(inmateToAdd))




# [START app]
app = webapp2.WSGIApplication([
    ('/', TestPage),
    ('/prisoner', Prisoner)
], debug=True)
# [END app]
