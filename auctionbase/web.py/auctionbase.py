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
		'/', 'page',
        '/addbid', 'add_bid',
        '/search', 'search',
        '/iteminfo', 'item_info'
        )

class page:
    # A simple GET request
    def GET(self):
        return render_template('page.html')

class search:
    # A GET request, to '/search'
    def GET(self):
        return render_template('search.html')
    
    # A POST request
    def POST(self):
        post_params = web.input()
        
        dict = {}
        dict['itemID'] = post_params['itemID']
        dict['minPrice'] = post_params['minPrice']
        dict['maxPrice'] = post_params['maxPrice']
        dict['status'] = post_params['status']
        dict['category'] = post_params['category']
        dict['description'] = post_params['description']
        result = sqlitedb.searchInAuction(dict)
        
        return render_template('search.html', search_result = result)

class add_bid:
    # A GET request, to '/addbid'
    def GET(self):
        return render_template('add_bid.html')

    # A POST request
    def POST(self):
        current_time = sqlitedb.getTime()
        post_params = web.input()
        item_id = post_params['itemID']
        user_id = post_params['userID']
        amount = float(post_params['price'])
        
        # if the user is valid
        if sqlitedb.getUserByUserId(userID):
            # if the item is valid
            if sqlitedb.getItemById(item_id) is not None:
                # if the bid is active
                if sqlitedb.isBidActive(item_id):
                    t = sqlitedb.transaction()
                    query_string = 'INSERT INTO Bids (itemID, UserID, Amount, Time) VALUES ($itemID, $userId, $price, $time) '
                    try:
                        if item_id == '':
                            return render_template('add_bid.html', message = 'no itemID')
                        if user_id == '':
                            return render_template('add_bid.html', message = 'no userID')
                        if amount == '':
                            return render_template('add_bid.html', message = 'no amount')
                        sqlitedb.query(query_string, {'itemID': item_id, 'userid': user_id, 'price': amount, 'time': current_time})
                    except Exception as exception:
                        t.rollback()
                        print str(exception)
                        result = False
                        update_message = 'Error when add a bid'
                        return render_template('add_bid.html', add_result = result, message = update_message)
                    else:
                        t.commit()
                        result = True
                        update_message = 'Successfully add a bid'
                        return render_template('add_bid.html', add_result = result, message = update_message)
                # if the bid is not active
                else:
                    result = False
                    update_message = 'The bid is closed now'
                    return render_template('add_bid.html', add_result = result, message = update_message)
            # if the item can't be found
            else:
                result = False
                update_message = 'Cannot get the item with item id'
                return render_template('add_bid.html', add_result = result, message = update_message)
        # if the user can't be found
        else:
            result = False
            update_message = 'Cannot get the user with user id'
            return render_template('add_bid.html', add_result = result, message = update_message)

class item_info:
    # A GET request, to '/iteminfo'
    def GET(self):
        return render_template('item_info.html')

    # A POST request
    def POST(self):
        post_params = web.input()
        item_id = post_params['item_id']
        bid = sqlitedb.getBidsById(item_id)
        item = sqlitedb.getItemById(item_id)
        category = sqlitedb.getCategoryById(item_id)
        time = sqlitedb.getTime()
        buy_price = item['Buy_Price']
        winner = None
        
        # the bid is open before the end time and when current bid price is lower than buy price
        if time < item['Ends'] and item['Currently'] < buy_price:
            open = True
        # the bid is open when there is no bid
        elif item['Number_of_Bids'] <= 0:
            open = True
        else:
            # get the winner of the item
            winner = sqlitedb.getWinnerById(item_id, item['Currently'])['UserID']
            open = False

        return render_template('item_info.html', bid_result = bid, item = item, categories = category, open = open, winner = winner)

class curr_time:
    # A simple GET request, to '/currtime'
    #
    # Notice that we pass in `current_time' to our `render_template' call
    # in order to have its value displayed on the web page
    def GET(self):
        current_time = sqlitedb.getTime()
        return render_template('curr_time.html', time = current_time)


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
            error_message = 'All new bids must be placed at the time which matches the current time of your AuctionBase system.'
            return render_template('select_time.html', message = error_message)
        # Here, we assign `update_message' to `message', which means
        # we'll refer to it in our template as `message'
        else:
            return render_template('select_time.html', message = update_message)

###########################################################################################
##########################DO NOT CHANGE ANYTHING BELOW THIS LINE!##########################
###########################################################################################

if __name__ == '__main__':
    web.internalerror = web.debugerror
    app = web.application(urls, globals())
    app.add_processor(web.loadhook(sqlitedb.enforceForeignKey))
    app.run()
