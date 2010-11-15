#!/usr/bin/env python

import os

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

class TaskCategory(db.Model):
    owner = db.UserProperty()
    name = db.CategoryProperty()

class Task(db.Model):
    owner = db.UserProperty()
    category = db.ReferenceProperty(TaskCategory)
    description = db.StringProperty(multiline=True)
    is_done = db.BooleanProperty()
    date_added = db.DateTimeProperty(auto_now_add=True)

class TaskManager(webapp.RequestHandler):
    def post(self):
        if not users.get_current_user():
            self.redirect(users.create_login_url('/'))
        else:
            action = self.request.get('action')
            if action == 'add':
                selected_category_key = self.request.get('category')
                if selected_category_key == "":
                    new_category_name = self.request.get('new_category')
                    if new_category_name == "":
                        new_category_name = 'Default'
                    selected_category_key = self.get_category_key(new_category_name)
                else:
                    selected_category_key = db.Key(selected_category_key)
                task_category = db.get(selected_category_key)
                task = Task()
                task.owner = users.get_current_user()
                task.category = task_category
                task.description = self.request.get('description')
                task.is_done = False
                task.put()
            elif action == 'mark as done':
                task = db.get(db.Key(self.request.get('key')))
                task.is_done = True
                task.put()
            elif action == 'mark as undone':
                task = db.get(db.Key(self.request.get('key')))
                task.is_done = False
                task.put()
            elif action == 'delete':
                db.delete(db.Key(self.request.get('key')))
            self.redirect('/')

    def get_tasks(self):
        todo_tasks = Task.all().filter('is_done = ', False).filter('owner = ', users.get_current_user())
        todo_tasks = todo_tasks.order('-date_added') # todo: pagination
        done_tasks = Task.all().filter('is_done = ', True).filter('owner = ', users.get_current_user())
        done_tasks = done_tasks.order('-date_added') # todo: pagination
        tasks = {
            'todo': todo_tasks,
            'done': done_tasks
        }
        return tasks

    def get_categories(self):
        categories = TaskCategory.all().filter('owner = ', users.get_current_user()).order('name')
        return categories

    def get_category_key(self, category_name):
        category = TaskCategory.all().filter('name = ', category_name).filter('owner = ', users.get_current_user()).get()
        if not category:
            category = TaskCategory()
            category.owner = users.get_current_user()
            category.name = category_name
            category.put()
        return category.key()

class MainHandler(webapp.RequestHandler):
    def get(self):
        if not users.get_current_user():
            self.redirect(users.create_login_url(self.request.uri))
        else:
            path = os.path.join(os.path.dirname(__file__), "main.html")
            task_manager = TaskManager()
            template_values = {
                'tasks': task_manager.get_tasks(),
                'categories': task_manager.get_categories(),
                'user_info': 'Signed in as %s' % users.get_current_user(),
                'logout_url': users.create_logout_url('/')
            }
            self.response.out.write(template.render(path, template_values))

def main():
    application = webapp.WSGIApplication([
                            ('/', MainHandler), 
                            ('/change_task', TaskManager)
                            ],
                            debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
