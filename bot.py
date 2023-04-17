import redis


r = redis.Redis(host='localhost', port=6379, db=0)

# subscribe to the channel
pubsub = r.pubsub()
pubsub.subscribe('bars')
pubsub.subscribe('quotes')
pubsub.subscribe('trades')
pubsub.subscribe('bars_updated')

quote_count = 0
trades_count = 0
bar_count = 0
updated_bars_count = 0

for message in pubsub.listen():

    if type(message['data']) == int:
        continue
    channel = message['channel'].decode('utf-8')
    message = message['data'].decode('utf-8')

    if channel == 'quotes':
        quote_count += 1

    if channel == 'trades':
        trades_count += 1

    if channel == 'bars':
        print(message)
        bar_count += 1

    if channel == 'bars_updated':
        updated_bars_count += 1

    if quote_count % 100 == 0:
        print(f"Counts: quotes: {quote_count}, trades: {trades_count}, bars: {bar_count}, updated_bars: {updated_bars_count}")

    #print(channel, message)