# -*- coding=UTF-8 -*-
from flask import Flask, request, session, g, redirect, abort, render_template
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
	app.run(debug=True)
