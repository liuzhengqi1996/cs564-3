import web

db = web.database(dbn='sqlite',
        db='AuctionBase.db'
    )

######################BEGIN HELPER METHODS######################

# Enforce foreign key constraints
# WARNING: DO NOT REMOVE THIS!
def enforceForeignKey():
    db.query('PRAGMA foreign_keys = ON')

# initiates a transaction on the database
def transaction():
    return db.transaction()

# returns the current time from your database
def getTime():
	# TODO: update the query string to match
    # the correct column and table name in your database
    query_string = 'select time from CurrentTime'
    results = query(query_string)
    # alternatively: return results[0]['currenttime']
    return results[0].time # TODO: update this as well to match the
                           # column name

# returns a single item specified by the Item's ID in the database
# Note: if the `result' list is empty (i.e. there are no items for a
# a given ID), this will throw an Exception!
def getItemById(item_id):
    # TODO: rewrite this method to catch the Exception in case `result' is empty
    query_string = 'select * from Items where ItemID = $itemID'
    result = query(query_string, {'itemID': item_id})
    try:
        return result[0]
    except:
        return None

# wrapper method around web.py's db.query method
# check out http://webpy.org/cookbook/query for more info
def query(query_string, vars = {}):
    return list(db.query(query_string, vars))

#####################END HELPER METHODS#####################

#TODO: additional methods to interact with your database,
# e.g. to update the current time

# updates the current time
def updateTime(curr_time):
    t = db.transaction()
    try: db.update('CurrentTime', where = 'time', Time = curr_time)
    except Exception as exception:
        t.rollback()
        print(str(exception))
        return 0
    else:
        t.commit()
        return 1

# gets category from item id
def getCategoryById(item_id):
    query_string = 'select Category from Categories where ItemID = $itemID'
    result = query(query_string, {'itemID': item_id})
    try:
        return result
    except Exception as exception:
        return None

# gets bids from item id
def getBidsById(item_id):
    query_string = 'select * from Bids where ItemID = $itemID'
    result = query(query_string, {'itemID': item_id})
    try:
        return result
    except Exception as exception:
        return None

# check if a bid is active
def isBidActive(item_id):
    item = getItemById(item_id)
	curr_time = getTime()
	# bid is invalid if there is no item
	if item == None: 
		return False
	else:
		start_time = item.Started
        end_time = item.Ends
        buy_price = item.Buy_Price
        curr_price = item.Currently
		# check if the buy price is higher than current bid price
		if buy_price > curr_price:
			# check if current time is between the start and end time of bid
			return (start_time <= curr_time and end_time >= curr_time)
		else:
			return False

# gets user from user id
def getUserByUserId(user_id):
    query_string = 'select * from Users where UserID = $userId'
    result = query(query_string, {'user_id': user_id})
    try:
        return result[0]
    except Exception as exception:
        return False

# gets the winner from item id
def getWinnerById(item_id):
    query_string = 'select UserID from Bids where ItemID = $itemID'
    results = query(query_string, {'item_id': item_id})
    try:
        return results
    except Exception as exception:
        return None

# searches for items in the auction
def searchInAuction(dict = {}):
    # initialize flags for various conditions
    status_flag = False
    item_flag = False
	if dict['itemID'] != '': item_flag = True
    category = False
	if dict['category'] != '': category_flag = True
    minprice = False
	if dict['minPrice'] != '': minprice_flag = True
    maxprice = False
	if dict['maxPrice'] != '': maxprice_flag = True
    description = False
    if dict['description'] != '': description_flag = True

    query_string = 'SELECT * FROM Items'
    if item_flag or category_flag or minprice_flag or maxprice_flag or description_flag or dict['status'] != 'all':
        query_string = 'SELECT * FROM Items WHERE'

    if item_flag:
        item_id = dict['itemID']
        query_string += ' ItemID = ' + item_id
        if minprice_flag or maxprice_flag:
            min_price = dict['minPrice']
            query_string += ' AND Currently >= ' + min_price
        if maxprice_flag:
            max_price = dict['maxPrice']
            query_string += ' AND Currently <= ' + max_price
    else:
        if minprice_flag:
            min_price = dict['minPrice']
            query_string += ' Currently >= ' + min_price
            if maxprice_flag:
                query_string += 'AND'
        if maxprice_flag:
            max_price = dict['maxPrice']
            query_string += ' Currently <= ' + max_price

    if dict['status'] != 'all':
        status_flag = True
        if maxprice_flag or minprice_flag or item_flag:
            if dict['status'] == 'open':
                query_string += ' AND Started <= (SELECT Time FROM CurrentTime) AND Ends >= (SELECT Time FROM CurrentTime) '
            if dict['status'] == 'close':
                query_string += ' AND Ends < (SELECT Time FROM CurrentTime) '
            if dict['status'] == 'notStarted':
                query_string += ' AND Started > (SELECT Time FROM CurrentTime) '
        else:
            if dict['status'] == 'open':
                query_string += ' Started <= (SELECT Time FROM CurrentTime) AND Ends >= (SELECT Time FROM CurrentTime) '
            if dict['status'] == 'close':
                query_string += ' Ends < (SELECT Time FROM CurrentTime) '
            if dict['status'] == 'notStarted':
                query_string += ' Started > (SELECT Time FROM CurrentTime) '

    if category_flag:
        if item_flag or minprice_flag or maxprice_flag or status_flag:
            query_string += ' AND ItemID in (SELECT ItemID FROM Categories WHERE Category = \'%s\') ' % (dict['category'])
        else:
            query_string += ' ItemID in (SELECT ItemID FROM Categories WHERE Category = \'%s\') ' % (dict['category'])

    if description_flag:
        if item_flag or minprice_flag or maxprice_flag or status_flag or category_flag:
            query_string += ' AND Description LIKE \'%%%s%%\' ' % (dict['description'])
        else:
            query_string += ' Description LIKE \'%%%s%%\' ' % (dict['description'])

    return query(query_string)
