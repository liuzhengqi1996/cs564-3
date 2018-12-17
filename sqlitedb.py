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
	query_string = 'select * from Items'
	if dict['itemID'] != '' or dict['minPrice'] != '' or dict['maxPrice'] != '' 
		or dict['status'] != 'all' or dict['category'] != '' or dict['description'] != '':
		query_string += ' where'
	
	# if item id is invalid
	if dict['itemID'] == '':
		# if min price is valid
		if dict['minPrice'] != '':
			min_price = dict['minPrice']
			# add min price info
			query_string += ' Currently >= minPrice, ' + min_price
			if dict['maxPrice'] != '':
				query_string += ' and'
		# if max price is valid
		if dict['maxPrice'] != '':
			max_price = dict['maxPrice']
			# add max price info
			query_string += ' Currently <= maxPrice, ' + max_price
	
	# if item id is valid
	if dict['itemID'] != '':
		item_id = dict['itemID']
        query_string += ' ItemID = ' + item_id
		# if min price is valid
		if dict['minPrice'] != '':
			min_price = dict['minPrice']
			# add min price info
			query_string += ' and Currently >= minPrice, ' + min_price
		# if max price is valid
		if dict['maxPrice'] != '':
			max_price = dict['maxPrice']
			# add max price info
			query_string += ' and Currently <= maxPrice, ' + max_price
	
	# if status is valid
    if dict['status'] != 'all':
		if dict['itemID'] != '' or dict['minPrice'] != '' or dict['maxPrice'] != '':
			query_string += ' and'
		# add status info
		if dict['status'] == 'open':
			query_string += ' Items.Started <= (select time from CurrentTime) and Items.Ends > (select time from CurrentTime)'
		if dict['status'] == 'close':
			query_string += ' Items.Ends < (select time from CurrentTime)'
		if dict['status'] == 'notStarted':
			query_string += ' Items.Started > (select time from CurrentTime)'
	
	# if category is valid
    if dict['category'] != '':
		if dict['itemID'] != '' or dict['minPrice'] != '' or dict['maxPrice'] != '' or dict['status'] != 'all':
			query_string += ' and'
		# add category info
		category = dict['category']
		query_string += ' ItemID in (select ItemID from Categories where Category = ' + category + ')'
	
	# if description is valid
    if dict['description'] != '':
		if dict['itemID'] != '' or dict['minPrice'] != '' or dict['maxPrice'] != '' or dict['status'] != 'all' or dict['category'] != '':
			query_string += ' and'
		# add description info
		description = dict['description']
		query_string += ' Description like ' + description
	
    return query(query_string)
