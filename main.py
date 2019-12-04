from bs4 import BeautifulSoup

from jnius import autoclass
try:
	Environment = autoclass('android.os.Environment')
	sdpath = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).getPath()
except Exception as e:
	print(e)


server = 'http://hp7017.pythonanywhere.com'
# server = 'http://127.0.0.1:8000'

from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
from kivy.network.urlrequest import UrlRequest
from kivy.factory import Factory
from kivy.clock import Clock
from functools import partial
from kivy.graphics import *
from kivy.animation import Animation
import json
import plyer
import requests
from android.permissions import request_permissions, Permission

class MainScreen(BoxLayout):

	def __init__(self, **kwargs):
		super(MainScreen, self).__init__(**kwargs)
		print(kwargs)
		self.headers = {
			'Content-Type': 'application/json'
		}
		self.id = plyer.uniqueid.get_uid()
		self.version = '1.1'
		self.user = {'status': 'OFF', 'version': self.version, 'uid': self.id}
		self.query_id = 1
		self.path = sdpath 
		UrlRequest('{0}/libgen/cusers/{1}/'.format(server, self.id), on_success=self.user_exist, on_failure=self.user_not_exist, on_error=self.show_msg)

	def check_update(self, req, res):
		if res['version'] != self.user['version']:
			popup = Factory.Update()
			popup.open()

	def user_exist(self, req, res):
		self.user = res
		UrlRequest('{0}/libgen/app/1/'.format(server), on_success=self.check_update, on_failure=self.show_msg, on_error=self.show_msg)
		self.change_user_status_on()

	def user_not_exist(self, req, res):
		self.login = Factory.Login()
		self.login.open()

	def create_user(self):
		self.user['email'] = self.login.email.text
		self.user['name'] = self.login.name.text
		UrlRequest('{0}/libgen/cusers/'.format(server), req_headers=self.headers, req_body=json.dumps(self.user), method='POST', on_success=self.account_created, on_failure=self.show_msg, on_error=self.show_msg)

	def account_created(self, req, res):
		self.login.dismiss()
		UrlRequest('{0}/libgen/app/1/'.format(server), on_success=self.check_update, on_failure=self.show_msg, on_error=self.show_msg)
		self.change_user_status_on()

	def change_user_status_on(self):
		body = {
			'status': 'ON'
		}
		UrlRequest('{0}/libgen/cusers/{1}/'.format(server, self.id), method='PATCH', req_body=json.dumps(body), req_headers=self.headers)

	def change_user_status_off(self):
		body = {
			'status': 'OFF'
		}
		requests.patch('{0}/libgen/cusers/{1}/'.format(server, self.id), data=json.dumps(body), headers=self.headers)

	def search_book(self):
		self.popup = Factory.Waiting()
		self.popup.open()
		self.bookslist.content.clear_widgets()
		self.query = book_title = self.searchbook.book_search_box.text
		body = {
			'search': book_title,
			'user': self.id
		}
		headers = {
			'Content-Type': 'application/json'
		}
		UrlRequest('{0}/libgen/searchs/'.format(server), on_failure=self.show_msg, on_error=self.show_msg, req_body=json.dumps(body), req_headers=headers, method='POST', on_success=self.set_query_id)
		book_title = book_title.replace(' ', '+')
		UrlRequest('http://gen.lib.rus.ec/search.php?req={0}&open=0&res=25&view=simple&phrase=1&column=def'.format(book_title), on_success=self.get_books, on_failure=self.show_msg, on_error=self.show_msg)

	def set_query_id(self, req, res):
		self.query_id = res['id']

	def get_books(self, request, result):
		bsobj = BeautifulSoup(result, "lxml")
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
		bookdownload = Factory.BookDownload()
		bookdownload.title.text = book.title.text
		bookdownload.format_ = book.format_.text
		UrlRequest(book.link, on_success=partial(self.get_download_page, bookdownload=bookdownload), on_failure=self.show_msg, on_error=self.show_msg)
		body = {
			'search': self.query_id,
			'name': bookdownload.title.text
		}
		UrlRequest('{0}/libgen/books/'.format(server), req_headers=self.headers, method='POST', req_body=json.dumps(body), on_failure=self.show_msg, on_error=self.show_msg)

	def get_download_page(self, req, result, bookdownload):
		bsobj = BeautifulSoup(result, 'lxml')
		td = bsobj.find(id='info')
		cover = td.div.img.attrs['src']
		pre = 'http://93.174.95.29'
		download_link = pre + td.h2.a.attrs['href']
		bookdownload.img.source = pre + cover
		self.downloads.content.add_widget(bookdownload)
		self.carousel.load_slide(self.downloads)
		print('{0}/{1}.{2}'.format(self.path, bookdownload.title.text, bookdownload.format_))
		UrlRequest(download_link, file_path='{0}/{1}.{2}'.format(self.path, bookdownload.title.text, bookdownload.format_), on_progress=partial(self.downloading, bookdownload=bookdownload))

	def downloading(self, req, current_size, total_size, bookdownload):
		percentage = float(current_size)*100/float(total_size)
		bookdownload.progress.value = percentage

	def show_msg(self, req, result):
		try:
			self.popup.dismiss()
		except:
			pass
		finally:
			error = Factory.Error()
			error.error.text = str(result)
			error.open()

class LibraryGenesisApp(App):

	def build(self):
		request_permissions([Permission.WRITE_EXTERNAL_STORAGE])
		self.mainscreen = MainScreen()
		return self.mainscreen

	def on_pause(self):
		self.mainscreen.change_user_status_off()
		return True

	def on_resume(self):
		self.mainscreen.change_user_status_on()

	def on_stop(self):
		self.mainscreen.change_user_status_off()

if __name__ == '__main__':
	LibraryGenesisApp().run()