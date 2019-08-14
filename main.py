import imp
import sys

class ImportBlocker(object):

	def __init__(self, *args):
		self.black_list = args

	def find_module(self, name, path=None):
		if name in self.black_list:
			return self

		return None

	def load_module(self, name):
		module = imp.new_module(name)	
		module.__all__ = [] # Necessary because of how bs4 inspects the module

		return module

sys.meta_path = [ImportBlocker('bs4.builder._htmlparser')]
from bs4 import BeautifulSoup

from jnius import autoclass
try:
	Environment = autoclass('android.os.Environment')
	sdpath = Environment.getExternalStorageDirectory().getAbsolutePath()

except Exception as e:
	print(e)

# sdpath = 'D:/'
server = 'http://hp7017.pythonanywhere.com'

from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.network.urlrequest import UrlRequest
from kivy.factory import Factory
from kivy.clock import Clock
from functools import partial
from kivy.graphics import *
from kivy.animation import Animation
import json

class MainScreen(BoxLayout):

	def __init__(self, **kwargs):
		super(MainScreen, self).__init__(**kwargs)
		self.userid = '1'
		try:
			file = open('{0}/Download/id.txt'.format(sdpath))
			self.userid = file.readline()
			file.close()
			if self.userid != '1':
				Clock.schedule_once(self.welcome_user, .1)
		except:
			file = open('{0}/Download/id.txt'.format(sdpath), 'w')
			file.write('1')
			file.close()

	def welcome_user(self, dt):
		self.carousel.load_slide(self.searchbook)
		Clock.schedule_once(self.remove_user, .2)

	def remove_user(self, dt):
		self.user.parent.remove_widget(self.user)
		UrlRequest('{0}/libgen/app/1'.format(server), on_success=self.check_update, on_failure=self.show_msg, on_error=self.show_msg)

	def check_update(self, req, res):
		if res['update'] == 1:
			update = Factory.Update()
			update.open()

	def signup(self):
		body = {
			'username': self.user.ids.susername.text,
			'email': self.user.ids.semail.text,
			'password': self.user.ids.spassword.text
		}
		print(body)
		headers = {
			'Content-Type': 'application/json'
		}
		UrlRequest('{0}/libgen/cusers/'.format(server), on_success=self.login, on_failure=self.show_msg, on_error=self.show_msg, req_body=json.dumps(body), req_headers=headers, method='POST')

	def login(self, req, res):
		print('login')
		self.userid = res['id']
		print(self.userid)
		file = open('{0}/Download/id.txt'.format(sdpath), 'w')
		file.write(str(self.userid))
		file.close()
		self.welcome_user(0)

	def search_book(self):
		self.popup = Factory.Waiting()
		self.popup.open()
		self.bookslist.content.clear_widgets()
		book_title = self.searchbook.book_search_box.text
		body = {
			'search': book_title,
			'user': self.userid
		}
		headers = {
			'Content-Type': 'application/json'
		}
		print(self.userid)
		UrlRequest('{0}/libgen/searchs/'.format(server), on_failure=self.show_msg, on_error=self.show_msg, req_body=json.dumps(body), req_headers=headers, method='POST')
		book_title = book_title.replace(' ', '+')
		UrlRequest('http://gen.lib.rus.ec/search.php?req={0}&open=0&res=25&view=simple&phrase=1&column=def'.format(book_title), on_success=self.get_books, on_failure=self.show_msg, on_error=self.show_msg)

	def get_books(self, request, result):
		bsobj = BeautifulSoup(result, 'html5lib')
		trs = bsobj.find(class_='c').findAll('tr')
		books = []
		for tr in trs[1:]:
			tds = tr.findAll('td')
			title = tds[2].get_text()
			author = tds[1].get_text()
			link = tds[9].a.attrs['href']
			size = tds[7].get_text()
			format_ = tds[8].get_text()
			books.append({'title':title, 'author':author, 'link':link, 'size':size, 'format':format_})
		self.show_books(books)

	def show_books(self, books):
		for book_ in books:
			book = Factory.Book()
			book.title.text = book_['title']
			book.author.text = book_['author']
			book.link = book_['link']
			book.size_.text = book_['size']
			book.format_.text = book_['format']
			self.bookslist.content.add_widget(book)
		self.popup.dismiss()
		self.carousel.load_slide(self.bookslist)

	def download_book(self, book):
		book.download_btn.disabled = True
		if self.userid == '1':
			self.carousel.load_slide(self.user)
		else:
			bookdownload = Factory.BookDownload()
			bookdownload.title.text = book.title.text
			bookdownload.format_ = book.format_.text
			UrlRequest(book.link, on_success=partial(self.get_download_page, bookdownload=bookdownload), on_failure=self.show_msg, on_error=self.show_msg)

	def get_download_page(self, req, result, bookdownload):
		bsobj = BeautifulSoup(result, 'html5lib')
		td = bsobj.find(id='info')
		cover = td.div.img.attrs['src']
		pre = 'http://93.174.95.29'
		download_link = pre + td.h2.a.attrs['href']
		bookdownload.img.source = pre + cover
		self.downloads.content.add_widget(bookdownload)
		self.carousel.load_slide(self.downloads)
		UrlRequest(download_link, file_path=u'{0}/Download/{1}.{2}'.format(sdpath, bookdownload.title.text, bookdownload.format_), on_progress=partial(self.downloading, bookdownload=bookdownload))

	def downloading(self, req, current_size, total_size, bookdownload):
		percentage = float(current_size)*100/float(total_size)
		bookdownload.progress.value = percentage

	def show_msg(self, req, result):
		try:
			self.popup.dismiss()
		finally:
			error = Factory.Error()
			error.error.text = str(result)
			error.open()

class LibraryGenesisApp(App):
	pass

if __name__ == '__main__':
	LibraryGenesisApp().run()