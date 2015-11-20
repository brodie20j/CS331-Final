import http.client
from html.parser import HTMLParser


class Client(object):
	"""docstring for Client"""
	def __init__(self, arg=None):
		super(Client, self).__init__()
		self.current_connection=None
		if (arg is not None):
			self.request(arg)


	def request(self, url):
		try:
			self.current_connection = http.client.HTTPConnection(url)
		except http.client.HTTPException as e:
			print(e)
		
		self.current_connection.request("GET","/")
		r1=self.current_connection.getresponse()

		page = HTTPPage(r1.getheaders,r1.read())
		print(page.body)

class HTTPPage(HTMLParser):
	def __init__(self, headermap, body):
		super(HTTPPage,self).__init__()
		self.header=headermap
		self.body=None
		self.script=False
		self.style=False
		self.loadPage(body)

	def loadPage(self, data):
		self.body=None
		self.feed(data.decode("utf-8"))

	def handle_starttag(self,tag,attrs):
		if "script" in tag:
			self.script=True
		elif "style" in tag:
			self.style=True

	def handle_endtag(self,tag):
		if "script" in tag:
			self.script=False
		elif "style" in tag:
			self.style=False
		self.put_body("\n")

	def handle_data(self, data):
		self.put_body(data)	

	def put_body(self, data):
		if not self.script and not self.style:
			if self.body is not None:
				self.body+=data
			else:
				self.body=data		




def main():
	client=Client("www.google.com")

if __name__ == "__main__":
	main()
		