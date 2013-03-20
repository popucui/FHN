# -*- coding=UTF-8 -*-
from flask import Flask, request, session, g, redirect, abort, render_template, url_for
from pymongo import Connection

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

@app.route('/')
def show_entries():
	db = g.conn.fhn
	#这个查询得修改完善
	entries = [ e for e in db.urls.find().limit(50)]
	return render_template('index.html', entries=enumerate(entries))

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
			error = 'Bad username or password'
			return render_template('login.html', error=error)
	return render_template('login.html', error=error)

@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	return redirect(url_for('show_entries'))

#用于用户添加一条 news
@app.route('/submit', methods=['GET', 'POST'])
def submit():
	error = None
	if request.method == 'GET':
		return render_template('submit.html', error=error)
	else: # POST
		db = g.conn.fhn
		if db.urls.find_one(request.form['url']):
			error = '抱歉，已经有别人提交过此 URL。'.decode('utf8')
			return render_template('submit.html', error=error)
		else:
			url = { 'url': request.form['url'],
					'title': request.form['title'],
					'submitter': session['user'],
					'upvoters': [ session['user'] ],
					'downvoters': [ ],
					'points': 1 }
			db.urls.insert(url)
			return redirect(url_for('show_entries'))

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
