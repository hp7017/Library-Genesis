from kivy.app import App
from bs4 import BeautifulSoup
from kivy.network.urlrequest import UrlRequest
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.factory import Factory
from functools import partial
import webbrowser as wb
import os
from kivy.utils import get_color_from_hex as ut
import plyer
import json

class MainScreen(BoxLayout):

	def __init__(self, path, server, **kwargs):
		super(MainScreen, self).__init__(**kwargs)
		try:
			self.path1 = path
			self.server = server
			self.downloads_docs = []
			self.not_added = [True, True]
			self.flat_colors = ['#1abc9c', '#2ecc71', '#3498db', '#9b59b6', '#e67e22', '#e74c3c', '#1abc9c', '#2ecc71', '#3498db', '#9b59b6']
			self.collection_docs()
			UrlRequest(self.server + '/top_10_books/', on_success=self.show_top_10_books, on_failure=self.fail, on_error=self.fail)
			Clock.schedule_once(self.post_init, .5)
			self.unique_id = plyer.uniqueid.id
			UrlRequest(self.server + '/cusers/{0}/'.format(self.unique_id), on_failure=self.create_user, on_error=self.fail)
			self.version = '1.0'
		except Exception as r:
			print(r)

	def create_user(self, req, res):
		self.login_popup.open()

	def show_top_10_books(self, req, res):
		print('show_top_10_books')
		for color, book in zip(self.flat_colors, res):
			# print(color, book['name'])
			topbook = Factory.TopBook()
			topbook.text = book['name']
			topbook.back_color = ut(color)
			self.showcase.box.add_widget(topbook)

	def collection_docs(self):
		print('collection_docs')
		self.downloads_docs = [f for f in os.listdir(self.path1) if os.path.isfile(os.path.join(self.path1, f))]

	def post_init(self, dt):
		self.downloaded_docs = Factory.DownloadedDocs()
		self.login_popup = Factory.Login()
		# self.login_popup.open()
		self.app_update = Factory.AppUpdate()
		# self.app_update.open()
		self.booklist = Factory.BookList()
		self.downloads = Factory.Downloads()
		for docs in self.downloads_docs:
			available_book = Factory.AvailablBook()
			available_book.label_name.text = docs
			available_book.path = self.path1 + '\\' + docs
			self.downloaded_docs.box.add_widget(available_book)

	def show_docs(self):
		self.downloaded_docs.open()

	def delete_book(self, path, ref):
		os.remove(path)
		self.downloaded_docs.box.remove_widget(ref)

	def search_book(self):
		self.booklist.boxlayout.clear_widgets()
		query = self.searchbook.textinput.text
		query = query.replace(' ', '+')
		UrlRequest('http://gen.lib.rus.ec/search.php?req={0}'.format(query), on_success=self.get_all_book, on_failure=self.fail, on_error=self.fail)
		self.waiting = Factory.Waiting()
		self.waiting.open()

	def get_all_book(self, req, res):
		bsobj = BeautifulSoup(res)
		try:
			for tr in bsobj.findAll('table')[2].findAll('tr')[1:]:
				tds = tr.findAll('td')
				author = tds[1].a.get_text()
				all_a = tds[2].findAll('a')
				a = None
				if len(all_a) == 2:
					a = all_a[1]
				else:
					a = all_a[0]
				title = a.contents[0]	
				size = tds[7].get_text()
				extension = tds[8].get_text()
				link = tds[10].a['href']
				book = Factory.Book()
				book.label_name.text = title
				book.label_author.text = author
				book.label_size.text = size
				book.label_extension.text = extension
				book.link = link
				book.detail = {
					'name': title,
					'author': author,
					'size': size,
					'extension': extension
				}
				self.booklist.boxlayout.add_widget(book)
			self.waiting.dismiss()
			if self.not_added[0]:
				self.box.remove_widget(self.showcase)
				self.box.add_widget(self.booklist)
				self.not_added[0] = False
		except IndexError as e:
			self.waiting.label.text = 'No result found!'
			self.waiting.auto_dismiss = True

	def fail(self, req, res):
		print(res)

	def download_book(self, link, detail, self_btn):
		self_btn.disabled =True
		new_link = link
		ind = new_link.index
		if new_link[new_link.index(':')-1] != 's':
			new_link = new_link[:new_link.index(':')] + 's' + new_link[new_link.index(':'):]
		downloaded_book = Factory.DownloadedBook()
		downloaded_book.label_name.text = detail['name']
		downloaded_book.detail = detail
		UrlRequest(new_link, on_success=partial(self.get_link, downloaded_book=downloaded_book), on_failure=self.fail, on_error=self.fail)

	def get_link(self, req, res, downloaded_book):
		bsobj = BeautifulSoup(res)
		link = bsobj.find('table').findAll('tr')[0].findAll('td')[1].a['href']
		new_name = self.path1 +  '\\' + downloaded_book.detail['name'] + '.' + downloaded_book.detail['extension']
		print(new_name)
		downloaded_book.path = new_name
		if self.not_added[1]:
			self.box.add_widget(self.downloads)
			self.not_added[1] = False
		self.downloads.boxlayout.add_widget(downloaded_book)
		req = UrlRequest(link, file_path=new_name, on_failure=self.fail, on_error=self.fail, on_progress=partial(self.downloading_progress, downloaded_book=downloaded_book), on_success=partial(self.open_downloaded_book, downloaded_book=downloaded_book))
		downloaded_book.req = req

	def cancel_downloading(self, downloaded_book):
		downloaded_book.req.cancel()
		self.downloads.boxlayout.remove_widget(downloaded_book)


	def downloading_progress(self, req, cs, ts, downloaded_book):
		downloaded_book
		progress = cs/ts*100
		downloaded_book.pb.value = progress

	def open_downloaded_book(self, req, res, downloaded_book):
		openbutton = Factory.OpenButton()
		openbutton.path = downloaded_book.path
		downloaded_book.remove_widget(downloaded_book.box)
		downloaded_book.add_widget(openbutton)

	def button_added(self, path):
		wb.open(path)

	def button_addedd(self, path):
		wb.open(path)

	def login(self):
		if self.login_popup.textinput_name.text == '' or self.login_popup.textinput_email.text == '':
			self.login_popup.label_msg.text = 'Oops! You have missed a detail.'
		else:
			header = {
				"Content-Type": "application/json"
			}
			body = {
				'name' : self.login_popup.textinput_name.text,
				'email' : self.login_popup.textinput_email.text,
				'uid' : self.unique_id,
				'platform' : 'Desktop',
				'version' : self.version,
				'status' : 'ON',
			}
			UrlRequest(self.server + '/cusers/', req_body=json.dumps(body), req_headers=header, on_success=self.login_success, on_error=self.fail, on_failure=self.fail)

	def login_success(self, req, res):
		self.login_popup.dismiss()

class LibraryGenesis(App):
	def build(self):
		self.icon = 'icon.png'
		path = self.user_data_dir
		server = 'https://hp7017.pythonanywhere.com/libgen'
		try:
			os.mkdir(path)
		except Exception as e:
			print(e)
		self.mainscreen = MainScreen(path=path, server=server)
		return self.mainscreen

if __name__ == '__main__':
	import sys
	def resourcePath():
		'''Returns path containing content - either locally or in pyinstaller tmp file'''
		if hasattr(sys, '_MEIPASS'):
			return os.path.join(sys._MEIPASS)

		return os.path.join(os.path.abspath("."))
	from kivy import resources
	resources.resource_add_path(resourcePath())
	LibraryGenesis().run()