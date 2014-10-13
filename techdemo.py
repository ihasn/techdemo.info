#imports
import tornado.ioloop
import tornado.web
import os.path
import boto.route53
import boto.dynamodb2
from boto.dynamodb2.fields import HashKey
from boto.dynamodb2.table import Table
from time import gmtime, strftime

#Class to setup communications to AWS Route53 and DynamoDB
class AWS_Comms():
    #Sets up AWS keys for each service
    aws_access_key_id='xxxxxxxxxxxxxxxxxxxxx'
    aws_secret_access_key='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    curr_zone = 'xxxxxxxxxxxxxxx'


    #Sets up the connection to Route53
    def route53(self):
        conn = boto.route53.connect_to_region('us-east-1', aws_access_key_id=AWS_Comms.aws_access_key_id, aws_secret_access_key=AWS_Comms.aws_secret_access_key)
        return conn

    #Sets up the connection to Dynamodb
    def dynamodb(self):
        comms = Table('comms',connection= boto.dynamodb2.connect_to_region("us-east-1", aws_access_key_id=AWS_Comms.aws_access_key_id, aws_secret_access_key=AWS_Comms.aws_secret_access_key))
        return comms

#A Record section
class Aname(tornado.web.RequestHandler):
    def get(self):
        self.render("aname.html")

    def post(self):
        self.set_header("Content-Type", "text/plain")
        #Inform user DNS is updated
        self.write("DNS should now resolve " + self.get_body_argument("host") + '.techdemo.info to ' + self.get_body_argument("ip_addr"))

        #Calls AWS_Comms to setup connections
        AWS_Comm = AWS_Comms()
        conn = AWS_Comm.route53()
        comms = AWS_Comm.dynamodb()

        #Setup zone
        curr_zone = AWS_Comms.curr_zone
        zone = boto.route53.record.ResourceRecordSets(conn, curr_zone)

	#Date, time stuff to setup entry in DynamoDB
        date = strftime("%Y%m%d", gmtime())
        time = strftime("%Y%m%d%H%M%S", gmtime())

        #Get hostname and ip address from input
        hostname = self.get_body_argument("host") + '.techdemo.info.'
        ip_addr = self.get_body_argument("ip_addr")

        #Setup entry for A record
        record = zone.add_change("CREATE", hostname, "A")
        record.add_value(ip_addr)
        #Commit to zone
        result = zone.commit()
        #Print result to console
        print result

        #Update dynamoDB
        comms.put_item(data={'key_id': 'A', 'time': time, 'hostname': hostname, 'ip': ip_addr})

#CNAME section
class Cname(tornado.web.RequestHandler):
    def get(self):
        self.render("cname.html")

    def post(self):
        self.set_header("Content-Type", "text/plain")
        #Inform user DNS is updated
        self.write("DNS should now resolve " + self.get_body_argument("host") + '.techdemo.info to ' + self.get_body_argument("cname") + '.')

        #Calls AWS_Comms to setup connections
        AWS_Comm = AWS_Comms()
        conn = AWS_Comm.route53()
        comms = AWS_Comm.dynamodb()

        #Setup zone
        curr_zone = AWS_Comms.curr_zone
        zone = boto.route53.record.ResourceRecordSets(conn, curr_zone)

        #Date, time stuff to setup entry in DynamoDB
        date = strftime("%Y%m%d", gmtime())
        time = strftime("%Y%m%d%H%M%S", gmtime())
        hostname = self.get_body_argument("host") + '.techdemo.info.'
        cname = self.get_body_argument("cname") + '.'

        #Setup entry for CNAME
        record = zone.add_change("CREATE", hostname, "CNAME")
        record.add_value(cname)
        #Commit to zone
        result = zone.commit()
        #Print result to console
        print result

        #Update dynamoDB
        comms.put_item(data={'key_id': 'CNAME', 'time': time, 'hostname': hostname, 'cname': cname})

class Index(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")

    def post(self):
        self.set_header("Content-Type", "text/plain")
        self.write("Index")

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", Index),
            (r"/aname/", Aname),
            (r"/cname/", Cname),
        ]
        settings = {
            "debug": True,
            "template_path": os.path.join('./', "templates"),
            "static_path": os.path.join('./', "static"),
        }
        tornado.web.Application.__init__(self, handlers, **settings)

if __name__ == "__main__":
    app = Application()
    port = '8888' 
    app.listen(port)
    print "Starting tornado server on port %s" % (port)
    tornado.ioloop.IOLoop.instance().start()
