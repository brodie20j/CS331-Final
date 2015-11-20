class Client(object):
	"""docstring for Client"""
	def __init__(self, arg):
		super(Client, self).__init__()
		self.arg = arg



def main():
	client=Client("Hello world!")
	print(client.arg)

if __name__ == "__main__":
	main()
		