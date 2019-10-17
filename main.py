from __future__ import print_function
from pprint import pprint
import os
from gmail_class import gmail
from trello_class import tllo as t

def main():
	g = gmail()
	t = tllo()
	service = g.config_gmail()
	client = t.config_trello()
	trello_data = g.inboxMailData(service)
	if trello_data is not None:
		atendimento = client.get_board('5d30b255dea9ed86b364e96b')
		inbox = atendimento.all_lists()[0]
		cards = inbox.list_cards()
		# pprint(cards)
		for x in cards:
			# pprint(x.id)
			x.delete()
		added_emails = []
		for x in trello_data.values():
			# TODO5: Função que cria cards colocar pra adicionar anexos
			# TODO6: Ao criar cartão mandar e-mail falando que foi recebida a solicitação
			t.createCard(x, inbox)
			added_emails.append(x.get('id'))
		g.moveAddedEmails(added_emails)
	else:
		pprint("Sem novas requisições")


if __name__ == '__main__':
	main()