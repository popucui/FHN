# -*- coding=UTF-8 -*-
from flask import Flask, request, session, g, redirect, abort, render_template, url_for

#from flaskext.babel import lazy_gettext, ngettext
from pymongo import Connection, DESCENDING
from bson.objectid import ObjectId
from datetime import datetime
import urlparse

# configuration
SECRET_KEY = '42af733dc674b992787a9806ce32a4b5'

app = Flask(__name__)
app.config.from_object(__name__)


@app.before_request
def before_request():
	g.conn = Connection()

@app.teardown_request
def teardown_request(exception):
	if hasattr(g, 'conn'):
		g.conn.close()

def domain(url):
	"""
	Return the domain of a URL e.g. http://www.google.com.hk > google.com.hk
	"""
	rv = urlparse.urlparse(url).netloc
	if rv.startswith("www."):
		rv = rv[4:]
	return rv

def timesince(dt, default=None):
	"""
	Return the string representation "time since" e.g. 5 days ago, 8 hours ago etc.
	"""
	if default is None:
		default = u"just now"

	now = datetime.utcnow()
	diff = now - dt

	periods = (
		(diff.days / 365, "year", "years"),
		(diff.days / 30, "month", "months"),
		(diff.days / 7, "week", "weeks"),
		(diff.days, "day", "days"),
		(diff.seconds / 3600, "hour", "hours"),
		(diff.seconds / 60,  "minute", "minutes"),
		(diff.seconds, "second", "seconds"),
	)

	for period, singular, plural in periods:
		if not period:
			continue
		
		if period > 1:
			return u'%d %s ago' % (period, plural)
		else:
			return u'%d %s ago' % (period, singular)
	return default
@app.route('/')
def show_entries():
	db = g.conn.fhn


	entries = [ e for e in db.urls.find()]
	for entry in entries:
		entry['life'] = timesince(entry['submit_time'])
		db.urls.save(entry)

	#按 points 倒排，以表示受欢迎程度
	entries = list(db.urls.find().sort('points', DESCENDING).limit(32))
	return render_template('index.html', entries=enumerate(entries, start=1))

@app.route('/vote')
def vote():
	if not session.get('logged_in', False):
		return redirect(url_for('login'))
	elif request.args.get('dir') == 'up':
		db = g.conn.fhn
		urlid = request.args.get('urlid')
		#以下这段代码无法保证数据库操作的原子性，可能导致 points 与实际不符
		entry = db.urls.find_one({'_id': ObjectId(urlid)})
		if session['user'] not in entry['upvoters'] and not session['user'] == entry['submitter']:
			db.urls.update({'_id': ObjectId(urlid)}, {'$push': {'upvoters': session['user']}, '$inc': {'points': 1}})
	
	return redirect(url_for('show_entries'))


@app.route('/newest')
def show_newest():
	db = g.conn.fhn
	entries = [ e for e in db.urls.find()]
	entries.sort(key = lambda e: e['_id'].generation_time, reverse=True)
	entries = entries[:32]
	return render_template('index.html', entries=enumerate(entries, start=1))

@app.route('/login', methods=['GET', 'POST'])
def login():
	db = g.conn.fhn
	error = None
	if request.method == 'POST':
		user = { 'name': request.form['username'],
				 'password': request.form['password'] }
		if db.users.find_one(user):
			session['logged_in'] = True
			session['user'] = user['name']
			return redirect(url_for('show_entries'))
		else:
			session['logged_in'] = False
			error = '用户名或密码不正确'.decode('utf8')
			return render_template('login.html', error=error)
	return render_template('login.html', error=error)

@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	session.pop('user', None)
	return redirect(url_for('show_entries'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	db = g.conn.fhn
	error = ''
	if request.method == 'POST':
		if db.users.find_one({'name': request.form['username']}):
			error = '用户已经存在。'.decode('utf8')
		if request.form['password'] != request.form['confirm_password']:
			error += '密码不一致'.decode('utf8')

		if error:
			return render_template('signup.html', error=error)
		else:
			user = { 'name': request.form['username'],
					 'password': request.form['password'] }
			db.users.insert(user)
			session['logged_in'] = True
			session['user'] = user['name']
			return redirect(url_for('show_entries'))
	else: # GET
		return render_template('signup.html', error=error)


#用于用户添加一条 news
@app.route('/submit', methods=['GET', 'POST'])
def submit():
	error = None
	if request.method == 'GET':
		return render_template('submit.html', error=error)
	else: # POST
		db = g.conn.fhn
		if request.form['url'] == '' or request.form['title'] == '':
			error = 'URL 和 Title 都不能为空。'.decode('utf8')
			return render_template('submit.html', error=error)
		elif db.urls.find_one({'url': request.form['url']}):
			error = '抱歉，已经有别人提交过此 URL。'.decode('utf8')
			return render_template('submit.html', error=error)
		else:
			url = { 
					'url': request.form['url'],
					'title': request.form['title'],
					'submitter': session['user'],
					'upvoters': [ session['user'] ], #默认当你提交一条 url 时，便投了它一票
					'downvoters': [ ],
					'points': 1,
					'submit_time': datetime.utcnow(),
					'domain': domain(request.form['url'])}
			db.urls.insert(url)
			return redirect(url_for('show_newest'))

# MongoDB 数据库为 fhn，有两个 collection，users 和 urls。
# urls 里的文档暂定这样：
# 看来需要加上 submit_time 字段。
entry_1 = { "url" : "http://blog.devep.net/virushuo/2013/03/19/googlereader.html",
            "title" : "Google的社会化梦想与Reader".decode("utf8"),
            "submitter" : "yfaming",
            "upvoters" : [ "yfaming" ],
            "downvoters" : [ ],
            "points" : 1 }

entry_2 = { "url" : "https://github.com/Yixiaohan/codeparkshare",
            "title" : "零基础学习Python书籍、视频、资料、社区等推荐".decode("utf8"),
            "submitter" : "yfaming",
            "upvoters" : [ "yfaming" ],
            "downvoters" : [ ],
            "points" : 1 }



if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=80)
