import http.client
from html.parser import HTMLParser
from datetime import datetime
import time

"""
Jonathan Brodie and Tristan Leigh
"""
class Client(object):
	"""docstring for Client"""
	def __init__(self, arg=None):
		super(Client, self).__init__()
		self._cache={}
		self._cache
		self.current_connection=None
		if (arg is not None):
			self.display(self.request(arg))

	def request(self, url):
		if self.check_cache(url):
			print("Cache hit!")
			return self.get_page_from_cache(url)
		else:
			return self.request_cache_miss(url)

	def display(self,page):
		print(page.body)

	def handle_response_code(self, response, headers):
		status=response.status
		if status == 200:
			return None
		elif status == 300 or status == 301 or status == 302 or status == 303 or status == 304 or status == 305 or status == 307:
			location = headers["Location"]
			return self.request(location)
		else:
			print("Something went wrong... Server returned response code: "+str(status))
			return None

	def request_cache_miss(self, url):
		requesttime=datetime.now().timetuple()
		request_body="/"
		try:
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
			self.current_connection = http.client.HTTPConnection(url)
		except http.client.HTTPException as e:
			print(e)
		except http.client.URLError as e:
			print(e)
		
		self.current_connection.request("GET",request_body)
		r1=self.current_connection.getresponse()
		responsetime=datetime.now().timetuple()

		headers=self.parse_header(r1.getheaders())
		check=self.handle_response_code(r1,headers)
		page=None
		if check is not None:
			page=check
		else:
			page = HTTPPage(headers,r1.read())
		page.requested_time=requesttime
		page.response_time=responsetime
		self.cache_page(url,page)
		return page

	def cache_page(self, url, httppage):
		self._cache[url]=httppage

	def convert_servertime_to_struct(self, servertime):
		return time.strptime(servertime, "%a, %d %b %Y %H:%M:%S %Z")

	def get_page_from_cache(self, url):
		return self._cache[url]

	def parse_header(self,headers):
		dic={}
		for tup in headers:
			dic[tup[0]]=tup[1]
		return dic

	def apparent_age(self,responsetime,date_value):
		val=(responsetime.tm_year-date_value.tm_year)+(responsetime.tm_mon-date_value.tm_mon)+(responsetime.tm_mday-date_value.tm_mday)+(responsetime.tm_hour-date_value.tm_hour)*60+(responsetime.tm_min-date_value.tm_min)+(responsetime.tm_sec-date_value.tm_sec)
		return max(0,val)

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

	def age_calculation(self,age_value,date_value,request_time,response_time):
		diff=time.mktime(response_time)-time.mktime(date_value)
		apparent_age=max(0,diff)
		corrected_received_age=max(apparent_age, age_value)
		response_delay = time.mktime(request_time)-time.mktime(response_time)
		corrected_initial_age = corrected_received_age+response_delay
		resident_time = time.mktime(datetime.now().timetuple())-time.mktime(response_time)
		current_age = corrected_initial_age+resident_time
		return current_age

class HTTPPage(HTMLParser):
	def __init__(self, headermap, body):
		super(HTTPPage,self).__init__()
		self.header=headermap
		self.body=None
		self.script=False
		self.style=False
		self.requested_time=None
		self.response_time=None
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
		if "div" in tag:
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
	while True:
		new_request=input('Enter new request: ')
		client.display(client.request(new_request))

if __name__ == "__main__":
	main()
		