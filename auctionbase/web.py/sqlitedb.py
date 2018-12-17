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
    # the correct column and table name in your database
    query_string = 'select time as time from CurrentTime'
    results = query(query_string)
    # alternatively: return results[0]['currenttime']
    return results[0].time

# returns a single item specified by the Item's ID in the database
# Note: if the `result' list is empty (i.e. there are no items for a
# a given ID), this will throw an Exception!
def getItemById(item_id):
    # TODO: rewrite this method to catch the Exception in case `result' is empty
    query_string = 'select * from Items where ItemID = $itemID'
    result = query(query_string, {'itemID': item_id})
    try:
        result[0]
        return result[0]
    except:
        return None


# wrapper method around web.py's db.query method
# check out http://webpy.org/cookbook/query for more info
def query(query_string, vars={}):
    return list(db.query(query_string, vars))

#####################END HELPER METHODS#####################

#TODO: additional methods to interact with your database,
# e.g. to update the current time

def updateTime(new_time):
    t = db.transaction()
    try:
        db.update('CurrentTime', where='time', Time=new_time)
    except Exception as e:
        t.rollback()
        print str(e)
        return 0
    else:
        t.commit()
        return 1

def searchItems(dict={}):
    # define the existence of various values
    status_flag = False
    item_falg = False
    category_falg = False
    minprice_falg = False
    maxprice_falg = False
    description_falg = False
    if dict['itemID'] != '':
        item_falg = True
    if dict['category'] != '':
        category_falg = True
    if dict['maxPrice'] != '':
        maxprice_falg = True
    if dict['minPrice'] != '':
        minprice_falg = True
    if dict['description'] != '':
        description_falg = True

    # initialize query string
    query_string = 'SELECT * FROM Items'
    if item_falg or category_falg or minprice_falg or maxprice_falg or description_falg or dict['status'] != 'all':
        query_string = 'SELECT * FROM Items WHERE'

    # check for item
    if item_falg:
        item_id = dict['itemID']
        query_string += ' ItemID = ' + item_id
        if minprice_falg or maxprice_falg:
            min_price = dict['minPrice']
            query_string += ' AND Currently >= ' + min_price
        if maxprice_falg:
            max_price = dict['maxPrice']
            query_string += ' AND Currently <= ' + max_price
    else:
        if minprice_falg:
            min_price = dict['minPrice']
            query_string += ' Currently >= ' + min_price
            if maxprice_falg:
                query_string += 'AND'
        if maxprice_falg:
            max_price = dict['maxPrice']
            query_string += ' Currently <= ' + max_price

    # check for status
    if dict['status'] != 'all':
        status_flag = True
        if maxprice_falg or minprice_falg or item_falg:
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


    # check for category
    if category_falg:
        if item_falg or minprice_falg or maxprice_falg or status_flag:
            query_string += ' AND ItemID in (SELECT ItemID FROM Categories WHERE Category = \'%s\') ' % (dict['category'])
        else:
            query_string += ' ItemID in (SELECT ItemID FROM Categories WHERE Category = \'%s\') ' % (dict['category'])

    # check for description
    if description_falg:
        if item_falg or minprice_falg or maxprice_falg or status_flag or category_falg:
            query_string += ' AND Description LIKE \'%%%s%%\' ' % (dict['description'])
        else:
            query_string += ' Description LIKE \'%%%s%%\' ' % (dict['description'])

    return query(query_string)
    
def bidisOpen(item_id):
    item = getItemById(item_id)
    if item != None:
        currTime = getTime()
        startTime = item.Started
        endTime = item.Ends
        buyPrice = item.Buy_Price
        currBidPrice = item.Currently
        return (startTime <= currTime and currTime <= endTime and currBidPrice <= buyPrice)
    else:
        return False

def getUser(user_id):
        query_string = 'select * from Users where UserID = $user_id'
        result = query(query_string, {'user_id': user_id})
        try:
            return result[0]
        except Exception as e:
            return False

def getCategory(item_id):
        query_string = 'select Category from Categories where ItemID = $item_id'
        result = query(query_string, {'itemID': item_id})
        try:
            return result
        except Exception as e:
            return None

def getBids(item_id):
        query_string = 'select * from Bids where ItemID = $item_id'
        result = query(query_string, {'itemID': item_id})
        try:
            return result
        except Exception as e:
            return None

def getWinner(item_id):
    query_string = 'select UserID from Bids where ItemID = $item_id'
    results = query(query_string, {'item_id': item_id})
    try:
        return results
    except Exception as e:
        return None