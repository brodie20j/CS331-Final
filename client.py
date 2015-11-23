import http.client, time,sys,socket
from html.parser import HTMLParser
from datetime import datetime
import tkinter as tk

"""
HTTP Client
CS331
Jonathan Brodie and Tristan Leigh
All libraries above are owned by their respective owners, we only claim
ownership for code from this point on.
"""
class Client(object):
	def __init__(self):
		super(Client, self).__init__()
		self._cache={}
		self.current_connection=None

	"""If the url requested is already in the cache, it will return the page
		in the cache. If it is not, it will make a new request for the page."""
	def request(self, url):
		if self.check_cache(url):
			print("Cache: the URL \'"+url+"\' is still fresh!\nRetrieving cached page...")
			return self.get_page_from_cache(url)
		else:
			return self.request_cache_miss(url)

	"""Prints the page to standard output"""
	def display(self,page):
		print(page.body)

	"""Checks to see if the response code was ok"""
	def handle_response_code(self, response):
		status=response.status
		if status == 200:
			return True
		else:
			return False

	"""Strip the url and return a tuple with a new url and request body"""
	def strip_url(self, url):
		request_body="/"
		if url.find("http") > -1:
			if url.find("https://") > -1:
				url=url[url.find("https://")+8:]
			elif url.find("http://") > -1:
				url=url[url.find("http://")+7:]
		elif url.find("www") > -1:
			url=url[url.find("www"):]

		if url.find("com") > -1:
			request_body=url[(url.find("com")+3):]
			url=url[:url.find("com")+3]
		elif url.find("edu") > -1:
			request_body=url[(url.find("edu")+3):]
			url=url[:url.find("edu")+3]
		elif url.find("org") > -1:
			request_body=url[(url.find("org")+3):]
			url=url[:url.find("org")+3]
		elif url.find("gov") > -1:
			request_body=url[(url.find("gov")+3):]
			url=url[:url.find("gov")+3]
		return (url, request_body)

	"""Connect to the server, get the page and cache it"""
	def request_cache_miss(self, url):
		response,requesttime,responsetime=self.connect(url)
		if response is None:
			return self.library_error(url, requesttime, responsetime)		
		check=self.handle_response_code(response)
		if check:
			page = HTTPPage(self.parse_header(response.getheaders()),response.read(),url,requesttime,responsetime)
			self.cache_page(url,page)
		else:
			page=self.retry_request(response, self.parse_header(response.getheaders()), url)
			self.cache_page(url,page)

		return page

	"""
	Given a response, try to reconnect
	If this is a 300 status code, get the location in the header and go there
	Otherwise, attempt to reconnect
	"""
	def retry_request(self, response, headers, url):
		status=response.status
		moved = status == 300 or status == 301 or status == 302 or status == 303 or status == 304 or status == 305 or status == 307
		if moved:
			retry_cap=20
			retry=0
			while moved and retry<retry_cap:
				location = headers["Location"]
				response,requesttime,responsetime=self.connect(location)
				if response is None:
					return self.library_error(location,requesttime,responsetime)
				headers=self.parse_header(response.getheaders())
				newpage=HTTPPage(headers,response.read(),location,requesttime,responsetime)


				status=response.status
				retry+=1
				moved = status == 300 or status == 301 or status == 302 or status == 303 or status == 304 or status == 305 or status == 307
			#the response will be cached for the incorrect url, so cache the correct one here
			self._cache[location]=newpage
			if moved:
				sorry_msg="We're sorry... the page you're looking for should exist but keeps changing. Please try another web site."
				newpage=HTTPPage(headers,sorry_msg.encode("utf-8"),location,requesttime,responsetime)
		else:
			retry_cap=10
			retry=0
			print("Something went wrong... Server returned response code: "+str(status))
			while status != 200 and retry > retry_cap:
				response,requesttime,responsetime=self.connect(url)
				if response is None:
					return self.library_error(url,requesttime,responsetime)
				status=response.status
				retry+=1
			newpage=HTTPPage(self.parse_header(response.getheaders()),response.read(),url,requesttime,responsetime)
		return newpage

	"""Submit the actual HTTP request"""
	def connect(self, url):
		requesttime=datetime.now().timetuple()
		newresponse=None
		try:
			url,request_body=self.strip_url(url)
			self.current_connection = http.client.HTTPConnection(url)
			self.current_connection.request("GET",request_body)
			newresponse=self.current_connection.getresponse()

		except http.client.HTTPException as e:
			print("HTTP library error")
			print(e)
		except socket.error as e:
			print("Socket error")
			print(e)

		responsetime=datetime.now().timetuple()
		return (newresponse,requesttime,responsetime)

	"""Handles errors that happen at the socket and http library level"""
	def library_error(self,url, requesttime,responsetime):
		string="There was an error - the web page \'" + url + "\' could not be found"
		return HTTPPage({},string.encode("utf-8"),url,requesttime,responsetime)

	"""Store the page in the cache"""
	def cache_page(self, url, httppage):
		self._cache[url]=httppage

	"""Pull the page from the cache"""
	def get_page_from_cache(self, url):
		if url in self._cache:
			return self._cache[url]

	"""Parse the header into a set of keys and values"""
	def parse_header(self,headers):
		dic={}
		for tup in headers:
			dic[tup[0]]=tup[1]
		return dic

	"""Determines if the url is in the cache, and if it is if it is fresh
	enough to serve to the user"""
	def check_cache(self,url):
		if url not in self._cache:
			return False
		else:
			age_value=None
			if "Age" in self._cache[url].header:
				age_value=self._cache[url].header["Age"]
			if age_value is None:
				age_value=-1
			date_value=self._cache[url].header["Date"]
			requesttime=self._cache[url].requested_time
			responsetime=self._cache[url].response_time
			datevalue=time.strptime(date_value, "%a, %d %b %Y %H:%M:%S %Z")

			age=self.age_calculation(age_value,datevalue,requesttime,responsetime)
			freshness_lifetime=None
			if "max-age" in self._cache[url].header:
				expired=self._cache[url].header["max-age"]
				expired=time.strptime(expired, "%a, %d %b %Y %H:%M:%S %Z")
				freshness_lifetime=time.mktime(expired)
			elif "Expires" in self._cache[url].header:
				expired=time.strptime(self._cache[url].header["Expires"],"%a, %d %b %Y %H:%M:%S %Z")
				freshness_lifetime=time.mktime(expired)-time.mktime(datevalue)
			else:
				freshness_lifetime=-1

			response_is_fresh = (freshness_lifetime > age)
			if response_is_fresh:
				return True
			else:
				return False

	"""Compute the age of the response given the standards of RFC 2616's
	expiration caching model"""
	def age_calculation(self,age_value,date_value,request_time,response_time):
		diff=time.mktime(response_time)-time.mktime(date_value)
		apparent_age=max(0,diff)
		corrected_received_age=max(apparent_age, age_value)
		response_delay = time.mktime(request_time)-time.mktime(response_time)
		corrected_initial_age = corrected_received_age+response_delay
		resident_time = time.mktime(datetime.now().timetuple())-time.mktime(response_time)
		current_age = corrected_initial_age+resident_time
		return current_age

	"""Compute apparent age of response by the standards given in RFC 2616"""
	def apparent_age(self,responsetime,date_value):
		val=(responsetime.tm_year-date_value.tm_year)+(responsetime.tm_mon-date_value.tm_mon)+(responsetime.tm_mday-date_value.tm_mday)+(responsetime.tm_hour-date_value.tm_hour)*60+(responsetime.tm_min-date_value.tm_min)+(responsetime.tm_sec-date_value.tm_sec)
		return max(0,val)

"""
HTTP Page Class for holding the header, body and transmission time info
"""
class HTTPPage(HTMLParser):
	def __init__(self, headermap, body,url,requested_time,response_time):
		super(HTTPPage,self).__init__()
		self.url=url
		self.header=headermap
		self.body=None
		self.script=False
		self.style=False
		self.requested_time=requested_time
		self.response_time=response_time
		self.loadPage(body)

	"""Load the page"""
	def loadPage(self, data):
		self.body=None
		self.feed(data.decode("utf-8"))

	"""
	Overriden function from HTMLParser, called whenever a tag opens
	"""
	def handle_starttag(self,tag,attrs):
		if "script" in tag:
			self.script=True
		elif "style" in tag:
			self.style=True

		if "div" in tag or "h1" in tag or "h2" in tag or "h3" in tag or "h4" in tag or "h5" in tag or "h6" in tag or "h7" in tag or "br" in tag:
			self.put_body("\n")
	"""
	Overriden function from HTMLParser, called whenever a tag closes
	"""
	def handle_endtag(self,tag):
		if "script" in tag:
			self.script=False
		elif "style" in tag:
			self.style=False

		if "div" in tag:
			self.put_body("\n")
		if "p" in tag:
			self.put_body("\n")
	"""
	Overriden function from HTMLParser, called whenever parser sees data
	"""
	def handle_data(self, data):
		self.put_body(data)	

	"""
	Puts the data into the body during the feed
	"""
	def put_body(self, data):
		if not self.script and not self.style:
			if self.body is not None:
				self.body+=data
			else:
				self.body=data		

"""
GUI Class using Tkinter to provide a good user experience
"""
class GUI(tk.Frame):

	def __init__(self, master=None,arg="www.stanfordrejects.com"):
		tk.Frame.__init__(self,master)
		self.client = Client()
		self.root=master
		self.current_page=self.client.request(arg)
		self.display_text=None
		self.pack()
		self.setupApp()

	"""
	Set up the widgets on the application
	"""
	def setupApp(self):
		self.address_field=tk.Entry(self.root)
		self.address_field.insert(0,self.current_page.url)
		self.address_field.pack(side = tk.TOP)

		"""
		callback for the 'go' button to tell the client to request the 
		url
		"""
		def button_go():
			print("Requesting... "+self.address_field.get()+"\n")
			self.current_page=self.client.request(self.address_field.get())

			self.address_field.delete(0,tk.END)
			self.address_field.insert(0,self.current_page.url)
			self.address_field.pack(side = tk.TOP)
			self.display_text.delete('1.0', tk.END)
			self.display_text.insert('1.0', self.current_page.body)
			self.display_text.pack(side = tk.LEFT)

		button=tk.Button(self.root, text="Go",command=lambda: button_go())
		button.pack(fill=tk.BOTH, expand=1, side=tk.TOP)
		self.display_text =tk.Text(self.root)
		self.display_text.insert('1.0',self.current_page.body)
		self.display_text.pack(side= tk.BOTTOM)

"""
Main function
"""
def main():
	root=tk.Tk()
	root.wm_title("CS331 Internet Browser")
	if (len(sys.argv) > 1):
		app=GUI(master=root,arg=sys.argv[1])
	else:
		app=GUI(master=root)
	root.mainloop()

if __name__ == "__main__":
	main()
		