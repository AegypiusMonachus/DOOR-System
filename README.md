# dy background 
---

### Dependent Package
* Flask 1.0.3  
* Flask-Cache 0.13.1
* Jinja2 2.10.1	
* PyMySQL 0.9.3
* xlrd 1.2.0	
* xlwt 1.3.0
* gunicorn 19.9.0

### Run

* python3环境，直接python3 run.py启动
* 现在采用了gunicorn 应该用这个启动
  1. sudo gunicorn -w 4 -b 0.0.0.0:2333 "run:new_app()" --log-level=debug --threads=10 --worker-class=gevent --reload
  2. 关进程如果直接control+c没有用的话
  3. 先 pstree -ap | grep gunicorn 查pid （或者用sudo lsof -i tcp:2333）
  4.  然后 kill -9 pid