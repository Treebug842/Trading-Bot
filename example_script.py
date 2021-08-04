from trading.binanceAPI import Binance
from webserver.reciever import CreateServer

trade = Binance()

def trigger(message):
    if message['token'] != "qOhiFrlxexemLklph":
        print("UNAUTHORIZED ATTEMPT!!")
        return
    
    coin = message['coin']
    scoin = message['scoin']

    if message['type'] == "buyall":
        trade.market_buyAll(coin, scoin)
        print("Bought all {}".format(coin.replace(scoin, "")))
    elif message['type'] == "sellall":
        trade.market_sellAll(coin, scoin)
        print("Sold All {}".format(scoin))

Server = CreateServer()
Server.trigger = trigger
Server.runServer()

