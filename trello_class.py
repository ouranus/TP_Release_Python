from __future__ import print_function
from pprint import pprint
import os.path
import json
from trello import TrelloClient
from requests_oauthlib import OAuth1Session
import requests
import webbrowser
from datetime import datetime
from datetime import timedelta


class tllo():
	"""docstring for trello"""
	def __init__(self, token, key, ATTACHMENTS_URL = None):
		super(trello, self).__init__()
		if ATTACHMENTS_URL is None:
			ATTACHMENTS_URL = 'https://api.trello.com/1/cards/%s/attachments'
			pass
		self.token = token
		self.key = key		
		self.request_token_url = 'https://trello.com/1/OAuthGetRequestToken'
		self.authorize_url = 'https://trello.com/1/OAuthAuthorizeToken'
		self.authorization_url = 'https://trello.com/1/token/approves'
		self.access_token_url = 'https://trello.com/1/OAuthGetAccessToken'
		self.resource_owner_key = ''
		self.resource_owner_secret = ''

	def OAuth(self, creds):
		expiration = "never"
		scope = 'read,write'
		trello_key = creds.get('api')
		trello_secret = creds.get('secret')
		name = creds.get('app_name')
		session = OAuth1Session(client_key=trello_key, client_secret=trello_secret)
		response = session.fetch_request_token(self.request_token_url)
		self.resource_owner_key, self.resource_owner_secret = response.get('oauth_token'), response.get('oauth_token_secret')
		print("Request Token:")
		print("    - oauth_token        = %s" % self.resource_owner_key)
		print("    - oauth_token_secret = %s" % self.resource_owner_secret)
		print("")
		print("Go to the following link in your browser:")
		auth_page = "{authorize_url}?oauth_token={oauth_token}&scope={scope}&expiration={expiration}&name={name}".format(
		  authorize_url=self.authorize_url,
		  oauth_token=self.resource_owner_key,
		  expiration=expiration,
		  scope=scope,
		  name=name
		)
		# TODO: Pegar a chave automaticamente da pagina que abrir (SELENIUM)
		session = OAuth1Session(client_key=trello_key, client_secret=trello_secret,
		                        resource_owner_key=self.resource_owner_key, resource_owner_secret=self.resource_owner_secret,
		                        verifier="0c85db33a2ff4f67004eefc6347c0e58")
		try:
			access_token = session.fetch_access_token(self.access_token_url)
			pass
		except Exception as e:
			pprint(e)
			webbrowser.open(auth_page)
			try:
			  inputFunc = raw_input
			except NameError:
			  inputFunc = input
			accepted = 'n'
			while accepted.lower() == 'n':
			  accepted = inputFunc('Have you authorized me? (y/n) ')
			verifier = inputFunc('What is the PIN? ')
			session = OAuth1Session(client_key=self.trello_key, client_secret=self.trello_secret,
		                        resource_owner_key=self.resource_owner_key, resource_owner_secret=self.resource_owner_secret,
		                        verifier=verifier)
			self.access_token = session.fetch_access_token(access_token_url)
			raise
		else:
			print("Access Token:")
			print("    - oauth_token        = %s" % access_token['oauth_token'])
			print("    - oauth_token_secret = %s" % access_token['oauth_token_secret'])
			print("")
			print("You may now access protected resources using the access tokens above.")
			print("")
		return access_token

	def config_trello():
		if os.path.exists('trello_credentials.json'):
			with open('trello_credentials.json', 'r') as cred_json:
				creds = json.loads(cred_json.read())
		token = OAuth(creds)
		# TODO: Write cliente object credentials and use if exists.
		# But to do that have to build a function that check if token is valid
		client = TrelloClient(
	    api_key=creds.get('api'),
	    api_secret=creds.get('secret'),
	    token=token.get('oauth_token'),
	    token_secret=token.get('oauth_token_secret')
		)
		return client

	def createCard(email_info, inbox):
		date_convert = datetime.strptime(email_info.get("date"), '%a, %d %b %Y %H:%M:%S %z') + timedelta(days=7)
		date_convert = date_convert.isoformat()
		card = inbox.add_card(email_info.get("title"), email_info.get("body"), None, date_convert)
		# pprint(card)
		# pprint(email_info)
		files = getAttachFile(email_info.get("id"))
		if files is not None:
			for x in files:
				pprint("Tipo: %s" % type(x))
				pprint("Anexando arquivo: %s" % x)
				card.attach(None, None, x)
				pass
			pass
		# pprint(files)

	def getAttachFile(ids):
		file_path = "attachments/" + ids + '/'
		if os.path.isdir(file_path):
			try:
				lst = os.listdir(file_path)
				attach_v = []
				for x in lst:
					with open(file_path + '/' + x, 'rb') as f:
						attach_v.append(f)
					pass
				return attach_v
			except Exception as e:
				pprint(e)
		else:
			pprint("Mensagem de id: %s não tem anexos" % ids)


	def upload_file_to_trello_card(self, key, token, card_id, file_path):
		"""
		Upload a local file to a Trello card as an attachment.
		File must be less than 10MB (Trello API limit).
		:param key: Trello API app key
		:param token: Trello user access token - must have write access
		:param card_id: The relevant card id
		:param file_path: path to the file to upload
		Returns a request Response object. It's up to you to check the
		  status code.
		"""
		params = {'key': self.resource_owner_key, 'token': token}
		files = {'file': open(file_path, 'rb')}
		url = ATTACHMENTS_URL % card_id
		return requests.post(url, params=params, files=files)