import redis
import sys


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
missed_count = -1
last_count = 0

REDIS_PRODUCER = "data_retriever1"

for message in pubsub.listen():

    last_id = 0
    sleep_ms = 5000

    try:
        while True:
            response = r.xread({REDIS_PRODUCER: "$"}, block = sleep_ms)
            #print(response)
            if response:
                key, messages = response[0]
                last_id, data = messages[0]

                channel = data[b'channel'].decode('utf-8')
                message = data[b'message'].decode('utf-8')
                count = int(data[b'count'].decode('utf-8'))

                # Count any missed messages
                if missed_count == -1:
                    last_count = count - 1;
                    missed_count = 0
                missed_count += count - last_count - 1
                last_count = count
                #print(channel, message, count)
                #print(data)

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
                    print(f"Counts: quotes: {quote_count}, trades: {trades_count}, bars: {bar_count}, updated_bars: {updated_bars_count}, missed: {missed_count}")
               

    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise