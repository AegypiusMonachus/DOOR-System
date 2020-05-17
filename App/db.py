from flask import Flask
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from App import app
from App.users.model import db

#app = app.app
#app = Flask(__name__)
app.config.from_object('App.config')

#db.init_app(app)


migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    print("manager.run()")
    manager.run()