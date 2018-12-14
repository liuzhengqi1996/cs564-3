#!/usr/bin/env python

import sys; sys.path.insert(0, 'lib') # this line is necessary for the rest
import os                             # of the imports to work!

import web
import sqlitedb
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

###########################################################################################
##########################DO NOT CHANGE ANYTHING ABOVE THIS LINE!##########################
###########################################################################################

######################BEGIN HELPER METHODS######################

# helper method to convert times from database (which will return a string)
# into datetime objects. This will allow you to compare times correctly (using
# ==, !=, <, >, etc.) instead of lexicographically as strings.

# Sample use:
# current_time = string_to_time(sqlitedb.getTime())

def string_to_time(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

# helper method to render a template in the templates/ directory
#
# `template_name': name of template file to render
#
# `**context': a dictionary of variable names mapped to values
# that is passed to Jinja2's templating engine
#
# See curr_time's `GET' method for sample usage
#
# WARNING: DO NOT CHANGE THIS METHOD
def render_template(template_name, **context):
    extensions = context.pop('extensions', [])
    globals = context.pop('globals', {})

    jinja_env = Environment(autoescape=True,
            loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
            extensions=extensions,
            )
    jinja_env.globals.update(globals)

    web.header('Content-Type','text/html; charset=utf-8', unique=True)

    return jinja_env.get_template(template_name).render(context)

#####################END HELPER METHODS#####################

urls = ('/currtime', 'curr_time',
        '/selecttime', 'select_time',
        '/add_bid', 'add_bid',
        '/', 'front_page',
        '/search', 'search',
        '/auction_detail', 'auction_detail'
        )

class front_page:
    def GET(self):
        return render_template('app_base.html')

class add_bid:
    def GET(self):
        return render_template('add_bid.html')

    def POST(self):
        current_time = sqlitedb.getTime()
        post_params = web.input()
        itemID = post_params['itemID']
        userID = post_params['userID']
        price = float(post_params['price'])

        if sqlitedb.getUser(userID):
            if sqlitedb.getItemById(itemID) is None:
                result = False
                update_message = 'Item is invalid'
                return render_template('add_bid.html', add_result=result, message=update_message)
            else:
                if sqlitedb.bidisOpen(itemID):
                    t = sqlitedb.transaction()
                    query_string = 'INSERT INTO Bids (itemID, UserID, Amount, Time) VALUES ($itemID, $userid, $price, $time) '
                    try:
                        if user_id == '' or item_id == '' or amount == '':
                            return render_template('add_bid.html', message='empty fields')
                        sqlitedb.query(query_string, {'itemID': itemID, 'userid': userID, 'price': price, 'time': current_time})
                    except Exception as e:
                        t.rollback()
                        print str(e)
                        update_message = 'An error has occurred'
                        result = False
                        return render_template('add_bid.html', add_result=result, message=update_message)
                    else:
                        t.commit()
                        update_message = 'Add bid successfully!'
                        result = True
                        return render_template('add_bid.html', add_result=result, message=update_message)
                else:
                    update_message = 'Bid is closed'
                    result = False
                    return render_template('add_bid.html', add_result=result, message=update_message)
        else:
            result = False
            update_message = 'User is invalid'
            return render_template('add_bid.html', add_result=result, message=update_message)


class search:
    def GET(self):
        return render_template('search.html')

    def POST(self):
        post_params = web.input()

        dict = {}
        dict['itemID'] = post_params['itemID']
        dict['category'] = post_params['category']
        dict['description'] = post_params['description']
        dict['minPrice'] = post_params['minPrice']
        dict['maxPrice'] = post_params['maxPrice']
        dict['status'] = post_params['status']

        result = sqlitedb.searchItems(dict)
        return render_template('search.html', search_result=result)


class auction_detail:
    def GET(self):
        return render_template('auction_detail.html')

    def POST(self):
        post_params = web.input()
        item_id = post_params['item_id']
        bid = sqlitedb.getBids(item_id)
        item = sqlitedb.getItemById(item_id)
        category = sqlitedb.getCategory(item_id)
        time = sqlitedb.getTime()
        price = item['Buy_Price']

        winner = None
        if item['Ends'] > time and item['Currently'] < price:
            open = True
        else:
            if item['Number_of_Bids'] > 0:
                winner = sqlitedb.getWinner(item_id, item['Currently'])['UserID']
            open = False

        return render_template('auction_detail.html', bid_result=bid, item=item, categories=category, open=open,
                               winner=winner)


class curr_time:
    # A simple GET request, to '/currtime'
    #
    # Notice that we pass in `current_time' to our `render_template' call
    # in order to have its value displayed on the web page
    def GET(self):
        current_time = sqlitedb.getTime()
        return render_template('curr_time.html', time=current_time)


class select_time:
    # Aanother GET request, this time to the URL '/selecttime'
    def GET(self):
        return render_template('select_time.html')

    # A POST request
    #
    # You can fetch the parameters passed to the URL
    # by calling `web.input()' for **both** POST requests
    # and GET requests
    def POST(self):
        post_params = web.input()
        MM = post_params['MM']
        dd = post_params['dd']
        yyyy = post_params['yyyy']
        HH = post_params['HH']
        mm = post_params['mm']
        ss = post_params['ss']
        enter_name = post_params['entername']

        selected_time = '%s-%s-%s %s:%s:%s' % (yyyy, MM, dd, HH, mm, ss)
        update_message = '(Hello, %s. Previously selected time was: %s.)' % (enter_name, selected_time)
        # TODO: save the selected time as the current time in the database
        flag = sqlitedb.updateTime(selected_time)
        if flag == 0:
            error_message = 'Update time failed!'
            return render_template('select_time.html', message=error_message)
        # Here, we assign `update_message' to `message', which means
        # we'll refer to it in our template as `message'
        else:
            return render_template('select_time.html', message=update_message)

###########################################################################################
##########################DO NOT CHANGE ANYTHING BELOW THIS LINE!##########################
###########################################################################################

if __name__ == '__main__':
    web.internalerror = web.debugerror
    app = web.application(urls, globals())
    app.add_processor(web.loadhook(sqlitedb.enforceForeignKey))
    app.run()
