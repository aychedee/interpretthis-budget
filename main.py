#!/usr/bin/env python
#
# Copyright 2011 Hansel Dunlop - hansel@interpretthis.org.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


"""
Todo: 
    1. Option to select currency symbol from a dropdown.
    2. Improve look and feel, centre the whole app and put it in a smallish box
    3. Header and footer that is the same on each page
    4. Different css for different media - iPhone, laptop etc
    
"""
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util, template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import os

def format_currency_string(cents, budget):
    amount = cents / 100.0
    cur_string = '%s%.2f' % (budget.currency, amount)
    return cur_string

def convert_to_cents(amount):
    cents = int(round(amount, 2) * 100)
    return cents

class Budget(db.Model):        
    """

    """
    owner = db.UserProperty()
    amount = db.StringProperty()
    cents = db.IntegerProperty()
    currency = db.StringProperty() #Todo - implement currency selection, maybe if budget.currency is null, prompt user to enter their currency symbol.

    def set_cents(self, user, amount):
        self.cents += convert_to_cents(amount)
        self.amount = format_currency_string(self.cents, self)

    @staticmethod
    def get_by_owner(user):
        """Returns an instance of Budget by owner.

        db.Query returns a list of instances, this method returns an 
        actual instance. 
        """
        query = db.Query(Budget).filter('owner =', user)
        result = query.fetch(limit=1)
        # the if block solves a problem which occurs if there is no 
        # existing budget for the user. 
        if not result:
            result = Budget()
            result.owner = users.get_current_user()
            result.cents = 0
            result.amount = u'0'
            result.currency = u'\xA3'
            return result
        else:
            return result[0]


class Transaction(db.Model):
    owner = db.UserProperty()
    amount = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    note = db.StringProperty(multiline=True)
    pretty_date = db.StringProperty()
    cents = db.IntegerProperty()


    def set_cents(self, budget, amount):
        self.cents = convert_to_cents(amount)
        self.amount = format_currency_string(self.cents, budget)

    @staticmethod
    def get_all_by_owner(user):
        
        query = db.Query(Transaction).filter('owner =', user).order('-date')
        result = query.fetch(limit=1000)
        return result
            

class MainHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            budget = Budget.get_by_owner(user)
            url = self.request.url + 'transactions'
            url_linktext = 'View transactions'
            template_values = {'budget': budget,
                               'user': user,
                               'url': url,
                               'url_linktext': url_linktext,
                               }

            path = os.path.join(os.path.dirname(__file__), 'index.html')
            self.response.out.write(template.render(path, template_values))

        else: 
            self.redirect(users.create_login_url(self.request.uri))


class Edit(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user() 
        budget = Budget.get_by_owner(user)
        if user:
            budget.owner = users.get_current_user()
            if not self.request.get('amount'):
                pass
            else:
                try:
                    budget.set_cents(user, float(self.request.get('amount')))
                except ValueError:
                    pass
                else:
                    trans = Transaction()
                    trans.owner = user
                    trans.set_cents(budget, float(self.request.get('amount')))
                    trans.note = self.request.get('note')
                    trans.pretty_date = trans.date.strftime('%c')
                    trans.put()
                    budget.put()
            self.redirect('/')
        else: 
            self.redirect(users.create_login_url(self.request.uri))

class Transactions(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            trans = Transaction.get_all_by_owner(user)
            l_url = self.request.url
            url = l_url.rsplit('/', 1)[0]
            url_linktext = 'Back'
                
            template_values = {'trans': trans,
                               'user': user,
                               'url': url,
                               'url_linktext': url_linktext,
                              }


            path = os.path.join(os.path.dirname(__file__), 'transactions.html')
            self.response.out.write(template.render(path, template_values))

        else:
            self.redirect(users.create_login_url(self.request.uri))

class Settings(webapp.RequestHandler):
    def get(self):
        pass


def main():
    application = webapp.WSGIApplication(
                                         [('/', MainHandler),
                                          ('/edit', Edit),
                                          ('/transactions', Transactions),
                                          ('/settings', Settings)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
