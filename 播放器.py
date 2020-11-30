import json
import os
import sys
import time
import random
import configparser
from urllib import parse
from urllib.request import urlretrieve

import qtawesome
# from PyQt5.QtGui import *
import requests
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *

'''音乐播放器'''

'''下载音乐 线程'''
class DownMusic (QThread):
	def __init__(self, msg, path):
		super ().__init__ ()

		self.sing_msg = msg
		self.cur_path = path

	def run(self):

		content_json = requests.get (url=self.sing_msg['url'])
		json2 = json.loads (content_json.text)

		# 音乐详情页----
		url_ip = json2['req']['data']['freeflowsip'][1]
		purl = json2['req_0']['data']['midurlinfo'][0]['purl']
		downlad = url_ip + purl

		if self.cur_path:
			try:
				print ('开始下载...')
				urlretrieve (url=downlad, filename='{}/{}.mp3'.format (self.cur_path,self.sing_msg['title']))

			# print ('{}.mp3下载完成！'.format (music_name[id - 1]))
			except Exception as e:
				print (e, '对不起，你没有该歌曲的版权！')
		else:
			try:
				os.mkdir ('QQ音乐')
			except:
				pass
			finally:
				try:
					print ('开始下载...')
					urlretrieve (url=downlad, filename='./QQ音乐/{}.mp3'.format (self.sing_msg['title']))

				# print ('{}.mp3下载完成！'.format (music_name[id - 1]))
				except Exception as e:
					print (e, '对不起，你没有该歌曲的版权！')

		print ('歌曲下载完毕')


'''搜索音乐线程'''


class REsing (QThread):
	# 创建自定义信号
	start_search_signal = pyqtSignal (str)

	def __init__(self, signal, sing_json):
		super ().__init__ ()
		self.return_signal = signal
		self.sing_msg = sing_json

	def run(self):
		if not self.sing_msg:
			return
		print ('搜索音乐：', self.sing_msg)
		w = parse.urlencode ({'w': self.sing_msg})

		url = 'https://c.y.qq.com/soso/fcgi-bin/client_search_cp?ct=24&qqmusic_ver=1298&new_json=1&remoteplace=txt.yqq.song&searchid=63229658163010696&t=0&aggr=1&cr=1&catZhida=1&lossless=0&flag_qc=0&p=1&n=10&%s&g_tk=5381&loginUin=0&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq.json&needNewCode=0' % (
			w)
		content = requests.get (url, )
		json1 = json.loads (content.text)
		song_list = json1['data']['song']['list']

		str_3 = '''https://u.y.qq.com/cgi-bin/musicu.fcg?-=getplaysongvkey5559460738919986&g_tk=5381&loginUin=0&hostUin=0&format=json&inCharset=utf8&outCharset=utf-8&notice=0&platform=yqq.json&needNewCode=0&data={"req":{"module":"CDN.SrfCdnDispatchServer","method":"GetCdnDispatch","param":{"guid":"1825194589","calltype":0,"userip":""}},"req_0":{"module":"vkey.GetVkeyServer","method":"CgiGetVkey","param":{"guid":"1825194589","songmid":["%s"],"songtype":[0],"uin":"0","loginflag":1,"platform":"20"}},"comm":{"uin":0,"format":"json","ct":24,"cv":0}}'''
		# self.url_list = []
		self.dict_sings = {}

		for i in range (len (song_list)):
			sing = {}
			sing['title'] = song_list[i]['name'] + '-' + song_list[i]['singer'][0]['name']
			sing['singer'] = song_list[i]['singer'][0]['name']
			sing['url'] = str_3 % song_list[i]['mid']
			self.dict_sings[i] = sing

			# self.url_list.append (str_3 % (song_list[i]['mid']))

		# 准备数据
		# list_sings = {
		# 	0: {"title": "断桥浅雪", "url": "www.wangyi123.com"},
		# 	1: {"title": "死了都要爱", "url": "www.wangyi123.com"},
		# 	2: {"title": "木头的心", "url": "www.wangyi123.com"},
		# 	3: {"title": "朱云指引", "url": "www.wangyi123.com"}
		# }

		self.return_signal.emit (json.dumps (self.dict_sings))
		# self.return_signal.emit (json.dumps (list_sings))


'''下载按钮'''


class DowdFileBtn (QPushButton):
	def __init__(self, file_name, name='下载音乐'):
		super ().__init__ (name)
		self.clicked.connect (self.down_file)
		self.file_name = file_name

	def down_file(self):
		print ('下载音乐---')


'''音乐表格列表'''


class Search_table (QWidget):
	def __init__(self):
		super ().__init__ ()
		self.__init_ui ()

	def __init_ui(self):
		# --表格类型
		self.table = QTableWidget (0, 3)  # 4行3列
		self.table.setHorizontalHeaderLabels (['音乐名称', '歌手', '操作'])

		self.table.horizontalHeader ().setSectionResizeMode (QHeaderView.Stretch)
		self.table.horizontalHeader ().setSectionResizeMode (1, QHeaderView.Interactive)  # 第2列的宽度随内容自适应
		self.table.horizontalHeader ().setSectionResizeMode (2, QHeaderView.Interactive)

		layout = QVBoxLayout ()
		layout.addWidget (self.table)
		self.setLayout (layout)


'''音乐播放器 主窗口'''


class MusicPlayer (QWidget):
	ret_sing_signal = pyqtSignal (str)

	def __init__(self):
		super ().__init__ ()
		self.__initialize ()

	'''初始化'''

	def __initialize(self):
		self.setWindowTitle ('音乐播放器v0.1.0')

		self.songs_list = []
		self.song_formats = ['mp3', 'm4a', 'flac', 'wav', 'ogg']
		self.settingfilename = 'setting.ini'
		self.player = QMediaPlayer ()

		# 添加文件路径
		self.cur_path = os.path.abspath (os.path.dirname (__file__))
		self.cur_playing_song = ''
		self.is_switching = False
		self.is_pause = True

		# 界面元素
		# --播放时间
		self.label1 = QLabel ('00:00')
		self.label1.setStyle (QStyleFactory.create ('Fusion'))
		self.label2 = QLabel ('00:00')
		self.label2.setStyle (QStyleFactory.create ('Fusion'))
		# --滑动条
		self.slider = QSlider (Qt.Horizontal, self)
		self.slider.sliderMoved[int].connect (lambda: self.player.setPosition (self.slider.value ()))
		self.slider.setStyle (QStyleFactory.create ('Fusion'))
		# --播放按钮
		self.play_button = QPushButton ('播放', self)
		self.play_button.clicked.connect (self.playMusic)
		self.play_button.setStyle (QStyleFactory.create ('Fusion'))
		# --上一首按钮
		self.preview_button = QPushButton ('上一首', self)
		self.preview_button.clicked.connect (self.previewMusic)
		self.preview_button.setStyle (QStyleFactory.create ('Fusion'))
		# --下一首按钮
		self.next_button = QPushButton ('下一首', self)
		self.next_button.clicked.connect (self.nextMusic)
		self.next_button.setStyle (QStyleFactory.create ('Fusion'))
		# --打开文件夹按钮
		self.open_button = QPushButton ('打开文件夹', self)
		self.open_button.setStyle (QStyleFactory.create ('Fusion'))
		self.open_button.clicked.connect (self.openDir)
		# --显示音乐列表
		self.qlist = QListWidget ()
		self.qlist.itemDoubleClicked.connect (self.doubleClicked)
		self.qlist.setStyle (QStyleFactory.create ('windows'))

		# --如果有初始化setting, 导入setting
		self.loadSetting ()
		# --播放模式
		self.cmb = QComboBox ()
		self.cmb.setStyle (QStyleFactory.create ('Fusion'))
		self.cmb.addItem ('顺序播放')
		self.cmb.addItem ('单曲循环')
		self.cmb.addItem ('随机播放')
		# --计时器
		self.timer = QTimer (self)
		self.timer.start (1000)
		self.timer.timeout.connect (self.playByMode)

		# -- 搜索框
		self.right_bar_widget = QWidget ()  # 右侧顶部搜索框部件
		self.right_bar_layout = QGridLayout ()  # 右侧顶部搜索框网格布局
		self.right_bar_widget.setLayout (self.right_bar_layout)
		# self.search_icon = QLabel (chr (0xf002) + ' ' + '搜索  ')
		# self.search_icon.setFont (qtawesome.font ('fa', 16))
		self.search_btn = QPushButton ('搜索')
		self.right_bar_widget_search_input = QLineEdit ()
		self.right_bar_widget_search_input.setPlaceholderText ("输入歌手、歌曲或用户，")
		# self.right_bar_widget_search_input.clicked.connect(self.search_sing)

		self.right_bar_layout.addWidget (self.search_btn, 0, 0, 1, 1)
		self.right_bar_layout.addWidget (self.right_bar_widget_search_input, 0, 1, 1, 8)

		# sing_lists = [i["title"] for i in list_sings.values ()]

		# sing_lists = list_sings.keys()
		# print (sing_lists)
		self.search_list = QListWidget ()

		self.search_list.itemDoubleClicked.connect (self.down_music)
		self.view_table = Search_table ()

		# 界面布局
		self.grid = QGridLayout ()
		self.setLayout (self.grid)
		self.grid.addWidget (self.qlist, 0, 0, 5, 10)  # 音乐列表
		self.grid.addWidget (self.label1, 0, 11, 1, 1)  # 播放时间
		self.grid.addWidget (self.slider, 0, 12, 1, 1)  # 滑动条
		self.grid.addWidget (self.label2, 0, 13, 1, 1)  #
		self.grid.addWidget (self.play_button, 0, 14, 1, 1)  # 播放按钮
		self.grid.addWidget (self.next_button, 1, 11, 1, 2)  # 下一首音乐
		self.grid.addWidget (self.preview_button, 2, 11, 1, 2)  # 上一首
		self.grid.addWidget (self.cmb, 3, 11, 1, 2)  # 播放按钮
		self.grid.addWidget (self.open_button, 4, 11, 1, 2)  # 文件夹按钮
		self.grid.addWidget (self.right_bar_widget, 5, 0, 1, 14)  # 搜索框
		self.grid.addWidget (self.search_list, 6, 0, 1, 14)  # 搜索框

		# self.grid.addWidget (self.view_table.table, 6, 0, 1, 14)

		# 绑定 槽函数
		self.search_btn.clicked.connect (self.search_sing)

		# 绑定 信号  ---- 返回的歌曲信息 显示到 窗口
		self.ret_sing_signal.connect (self.sing_windows)

		# self.setWindowOpacity (0.9)  # 设置窗口透明度
		# self.setAttribute (QtCore.Qt.WA_TranslucentBackground)  # 设置窗口背景透明
		# self.setWindowFlags (QtCore.Qt.FramelessWindowHint)  # 隐藏边框
		# self.grid.setSpacing (0)

	'''显示 搜索歌曲到屏'''

	def sing_windows(self, ret_json):
		self.list_sings = json.loads (ret_json)
		print ('收到信息-----')
		# print(list_sings)
		# self.view_table.table.setRowCount (len (list_sings.keys ()))
		# all_row = self.view_table.table.rowCount()
		# print('当前表格总行数：', all_row)
		# for k in list_sings.keys ():
		# 	# print (list_sings[k]['title'])
		# 	print('----1----')
		# 	self.view_table.table.setRowCount(all_row + 1)
		# 	self.view_table.table.setItem (k, 0, QTableWidgetItem (list_sings[k]['title']))
		# 	self.view_table.table.setItem (k, 1, QTableWidgetItem (list_sings[k]['url']))
		# 	self.view_table.table.setCellWidget (k, 2, DowdFileBtn (list_sings[k]['title']))
		# 	print('-----2-----')
		# print('加载完毕')
		# 清除元素，清除上一次的数据
		self.search_list.clear()
		for k in self.list_sings.keys ():
			print (self.list_sings[k]['title'])
			self.search_list.addItem (self.list_sings[k]['title'])


	'''下载 音乐的槽函数'''
	def down_music(self):
		# sing_title = self.search_list.currentItem ().text ()
		# 获取元素的 所在的行数
		current_row = self.search_list.currentRow ()
		# print(sing_title)
		# print(current_row)

		# print(self.list_sings)
		# 创建 下载音乐线程
		# print (self.list_sings[str(current_row)]['url'])

		self.down_thread = DownMusic(self.list_sings[str(current_row)], self.cur_path)

		self.down_thread.start()

	''' 传递歌曲信息，给 搜索子线程'''

	def search_sing(self):
		ret = self.right_bar_widget_search_input.text ()

		# 创建 音乐搜索子线程
		self.resing = REsing (self.ret_sing_signal, ret)

		# # 将要创建的子线程类中的信号进行绑定
		self.resing.start_search_signal.connect (self.sing_windows)
		# # 让子线程开始工作
		self.resing.start ()
		print ('线程开始---')

	'''键盘事件'''
	# 检测键盘回车按键，函数名字不要改，这是重写键盘事件
	# def keyPressEvent(self, event):
	# 	# 这里event.key（）显示的是按键的编码
	# 	# print ("按下：" + str (event.key ()))
	#
	# 	if event.key () == Qt.Key_Return:
	# 		# print ('Space')
	# 		ret = self.right_bar_widget_search_input.text ()
	# 		print (ret)
	# 		self.resing.start_search_signal.emit(json.dumps({"msg": ret}))

	'''根据播放模式播放音乐'''

	def playByMode(self):
		if (not self.is_pause) and (not self.is_switching):
			self.slider.setMinimum (0)
			self.slider.setMaximum (self.player.duration ())
			self.slider.setValue (self.slider.value () + 1000)
		self.label1.setText (time.strftime ('%M:%S', time.localtime (self.player.position () / 1000)))
		self.label2.setText (time.strftime ('%M:%S', time.localtime (self.player.duration () / 1000)))
		# 顺序播放
		if (self.cmb.currentIndex () == 0) and (not self.is_pause) and (not self.is_switching):
			if self.qlist.count () == 0:
				return
			if self.player.position () == self.player.duration ():
				self.nextMusic ()
		# 单曲循环
		elif (self.cmb.currentIndex () == 1) and (not self.is_pause) and (not self.is_switching):
			if self.qlist.count () == 0:
				return
			if self.player.position () == self.player.duration ():
				self.is_switching = True
				self.setCurPlaying ()
				self.slider.setValue (0)
				self.playMusic ()
				self.is_switching = False
		# 随机播放
		elif (self.cmb.currentIndex () == 2) and (not self.is_pause) and (not self.is_switching):
			if self.qlist.count () == 0:
				return
			if self.player.position () == self.player.duration ():
				self.is_switching = True
				self.qlist.setCurrentRow (random.randint (0, self.qlist.count () - 1))
				self.setCurPlaying ()
				self.slider.setValue (0)
				self.playMusic ()
				self.is_switching = False

	'''打开文件夹'''

	def openDir(self):
		self.cur_path = QFileDialog.getExistingDirectory (self, "选取文件夹", self.cur_path)
		if self.cur_path:
			self.showMusicList ()
			self.cur_playing_song = ''
			self.setCurPlaying ()
			self.label1.setText ('00:00')
			self.label2.setText ('00:00')
			self.slider.setSliderPosition (0)
			self.is_pause = True
			self.play_button.setText ('播放')

	'''导入setting'''

	def loadSetting(self):
		if os.path.isfile (self.settingfilename):
			config = configparser.ConfigParser ()
			config.read (self.settingfilename)
			self.cur_path = config.get ('MusicPlayer', 'PATH')
			self.showMusicList ()

	'''更新setting'''

	def updateSetting(self):
		config = configparser.ConfigParser ()
		config.read (self.settingfilename)
		if not os.path.isfile (self.settingfilename):
			config.add_section ('MusicPlayer')
		config.set ('MusicPlayer', 'PATH', self.cur_path)
		config.write (open (self.settingfilename, 'w'))

	'''显示文件夹中所有音乐'''

	def showMusicList(self):
		self.qlist.clear ()
		self.updateSetting ()
		for song in os.listdir (self.cur_path):
			if song.split ('.')[-1] in self.song_formats:
				self.songs_list.append ([song, os.path.join (self.cur_path, song).replace ('\\', '/')])
				self.qlist.addItem (song)
		self.qlist.setCurrentRow (0)
		if self.songs_list:
			self.cur_playing_song = self.songs_list[self.qlist.currentRow ()][-1]

	'''双击播放音乐'''

	def doubleClicked(self):
		self.slider.setValue (0)
		self.is_switching = True
		self.setCurPlaying ()
		self.playMusic ()
		self.is_switching = False

	'''设置当前播放的音乐'''

	def setCurPlaying(self):
		self.cur_playing_song = self.songs_list[self.qlist.currentRow ()][-1]
		self.player.setMedia (QMediaContent (QUrl (self.cur_playing_song)))

	'''提示'''

	def Tips(self, message):
		QMessageBox.about (self, "提示", message)

	'''播放音乐'''

	def playMusic(self):
		if self.qlist.count () == 0:
			self.Tips ('当前路径内无可播放的音乐文件')
			return
		if not self.player.isAudioAvailable ():
			self.setCurPlaying ()
		if self.is_pause or self.is_switching:
			self.player.play ()
			self.is_pause = False
			self.play_button.setText ('暂停')
		elif (not self.is_pause) and (not self.is_switching):
			self.player.pause ()
			self.is_pause = True
			self.play_button.setText ('播放')

	'''上一首'''

	def previewMusic(self):
		self.slider.setValue (0)
		if self.qlist.count () == 0:
			self.Tips ('当前路径内无可播放的音乐文件')
			return
		pre_row = self.qlist.currentRow () - 1 if self.qlist.currentRow () != 0 else self.qlist.count () - 1
		self.qlist.setCurrentRow (pre_row)
		self.is_switching = True
		self.setCurPlaying ()
		self.playMusic ()
		self.is_switching = False

	'''下一首'''

	def nextMusic(self):
		self.slider.setValue (0)
		if self.qlist.count () == 0:
			self.Tips ('当前路径内无可播放的音乐文件')
			return
		next_row = self.qlist.currentRow () + 1 if self.qlist.currentRow () != self.qlist.count () - 1 else 0
		self.qlist.setCurrentRow (next_row)
		self.is_switching = True
		self.setCurPlaying ()
		self.playMusic ()
		self.is_switching = False


'''run'''
if __name__ == '__main__':
	app = QApplication (sys.argv)
	gui = MusicPlayer ()
	gui.show ()
	app.exec ()
