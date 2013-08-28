import SimpleHTTPServer
import SocketServer
import devutil
import json

PORT = 50010

class TestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    """The test example handler."""

    def do_POST(self):
        """Handle a post request by returning the square of the number."""
        length = int(self.headers.getheader('content-length'))        
        data_string = self.rfile.read(length)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')        
        self.end_headers()

        o = json.loads(data_string)
        
        if o["command"] == "PUT":
            # Do what should be done during PUT
            pass
        elif o["command"] == "TAG":
            # Replace this line with real action
            o["content"] = o["content"] + "Hello world"
            
            self.wfile.write(json.dumps(o))


httpd = SocketServer.TCPServer(("", PORT), TestHandler)

if __name__ == "__main__":
    print "serving at port", PORT
    httpd.serve_forever()
