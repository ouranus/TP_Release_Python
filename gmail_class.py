from __future__ import print_function
import pickle
import mimetypes
import base64
import os.path
from pprint import pprint
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient import errors
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class gmail():

	def __init__(self, creds=None, service=None, trello_cards=None, SCOPES=None):
		self.label_seinfra_id = "Label_305199959114039743"
		self.creds = creds
		self.service = service
		self.trello_cards = {}
		if SCOPES is None:
			self.SCOPES = ['https://www.googleapis.com/auth/gmail.readonly','https://www.googleapis.com/auth/gmail.modify']
		else:
			self.SCOPES = SCOPES

	def config_gmail(self):
		# The file token.pickle stores the user's access and refresh tokens, and is
		# created automatically when the authorization flow completes for the first
		# time.
		if os.path.exists('token.pickle'):
			with open('token.pickle', 'rb') as token:
				self.creds = pickle.load(token)
		# If there are no (valid) credentials available, let the user log in.
		if not self.creds or not self.creds.valid:
			if self.creds and self.creds.expired and self.creds.refresh_token:
				self.creds.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file(
					'credentials.json', self.SCOPES)
				self.creds = flow.run_local_server(port=0)
			# Save the credentials for the next run
			with open('token.pickle', 'wb') as token:
				pickle.dump(self.creds, token)
		self.service = build('gmail', 'v1', credentials=self.creds)
		return self.service

	def saveAttachments(self, payload, ids):
		for part in payload['parts']:
			if part['filename']:
				if 'data' in part['body']:
					data = part['body']['data']
				else:
					att_id = part['body']['attachmentId']
					att = self.service.users().messages().attachments().get(userId="me", messageId=ids, id=att_id).execute()
					data = att['data']
				file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
				new_path = './attachments/' + str(ids) + '/' + part['filename']
				if not os.path.isdir('./attachments/' + str(ids) + '/'):
					os.makedirs('./attachments/' + str(ids))
				if not os.path.isfile(new_path):
					with open(new_path, 'wb') as f:
						f.write(file_data)

	def getMessageBatchRequest(self, request_id, response, exception):
		if exception is not None:
			print('Batch Falhou para o request {}: {}'.format(request_id, exception))
			exit()
		else:
			ids = response.get('id')
			payload = response.get('payload')
			self.saveAttachments(payload, ids)
			body = self.readMessage(response)
			try:
				for x in payload.get('headers'):
					if x.get("name") == "Date":
						d = x.get('value')
					elif x.get("name") == "From":
						f = x.get('value')
					elif x.get("name") == "Subject":
						t = x.get('value')
					pass
				self.trello_cards[request_id] = {"id": ids, "date": d, "from": f, "title": t, "body": body}
			except Exception as e:
				pprint(e)
				# exit()

	def inboxMailData(self, service):
		# Call the Gmail API
		services = service.users()
		batch = service.new_batch_http_request(callback = self.getMessageBatchRequest)
		messages = services.messages().list(userId='me', q="label:SEINFRA").execute()
		if messages.get("resultSizeEstimate") != 0:
			for msg_id in messages.get('messages'):
				batch.add(services.messages().get(userId='me', id=msg_id.get('id')))
			batch.execute()
			return self.trello_cards

	def moveAddedEmails(self, emails_id_vector):
		services = self.service.users()
		body = {'ids': emails_id_vector, 'addLabelIds': [], 'removeLabelIds': ['UNREAD', self.label_seinfra_id]}
		resp = services.messages().batchModify(userId='me', body=body).execute()
		print("Response ==> %s" % resp)

	def SendMessage(self, service, message):
		try:
			message = (service.users().messages().send(userId="me", body=message).execute())
			print('Id da mensagem: %s' % message['id'])
			return message
		except errors.HttpError as error:
			print( 'Ocorreu um erro: %s' % error)
			exit()


	def CreateMessage(sender, to, subject, message_text):
		# Create a message for an email.

		# Args:
		#   sender: Email address of the sender.
		#   to: Email address of the receiver.
		#   subject: The subject of the email message.
		#   message_text: The text of the email message.

		# Returns:
		#   An object containing a base64url encoded email object.

		message = MIMEText(message_text)
		message['to'] = to
		message['from'] = sender
		message['subject'] = subject
		return {'raw': base64.urlsafe_b64encode(message.as_string())}

	def readMessage(self, content)->str:
		message = None
		if "data" in content['payload']['body']:
			message = content['payload']['body']['data']
			message = self.data_encoder(message)
		elif "data" in content['payload']['parts'][0]['body']:
			message = content['payload']['parts'][0]['body']['data']
			message = self.data_encoder(message)
		elif "data" in content['payload']['parts'][0]['parts'][0]['body']:
			message = content['payload']['parts'][0]['parts'][0]['body']['data']
			message = self.data_encoder(message)
		else:
			print("body has no data.")
		return message

	def data_encoder(self, text):
		if len(text) > 0:
			message = base64.urlsafe_b64decode(text)
			message = str(message, 'utf-8')
			# message = quopri.decodestring(message).decode('utf8')
			# message = email.message_from_string(message)
		return message