#**Charting app to analyse Chart using LLM**

#Creating a Virtual environment

python3 -m venv venv
. venv/bin/activate

**#Installing Dependencies**
Now that we have our virtual environment set up, we can install the packages we will be using. We will do this using the pip command.

First installing the lightweight-charts package:

pip install lightweight-charts

**#Next download the TWS API. Be sure to download the latest stable package for your operating system. Place the zip file in your project directory (eg. ib-trading) and unzip it.**

Change to the IBJts/source/pythonclient directory. Then type:

python3 setup.py install

# create a queue for data coming from Interactive Brokers API
data_queue = queue.Queue()

# a list for keeping track of any indicator lines
current_lines = []

# initial chart symbol to show
INITIAL_SYMBOL = "TSM"

# settings for live trading vs. paper trading mode
LIVE_TRADING = False
LIVE_TRADING_PORT = 7496
PAPER_TRADING_PORT = 7497
TRADING_PORT = PAPER_TRADING_PORT
if LIVE_TRADING:
    TRADING_PORT = LIVE_TRADING_PORT

# these defaults are fine
DEFAULT_HOST = '127.0.0.1'
DEFAULT_CLIENT_ID = 1

# Client for connecting to Interactive Brokers
class PTLClient(EWrapper, EClient):
     
    def __init__(self, host, port, client_id):
        EClient.__init__(self, self) 
        
        self.connect(host, port, client_id)

        # create a new Thread
        thread = Thread(target=self.run)
        thread.start()


    def error(self, req_id, code, msg, misc):
        if code in [2104, 2106, 2158]:
            print(msg)
        else:
            print('Error {}: {}'.format(code, msg))

 


    # callback when all historical data has been received
    def historicalDataEnd(self, reqId, start, end):
        print(f"end of data {start} {end}")
            
        # we can update the chart once all data has been received
        update_chart()


    # callback to log order status, we can put more behavior here if needed
    def orderStatus(self, order_id, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        print(f"order status {order_id} {status} {filled} {remaining} {avgFillPrice}")    


    # callback for when a scan finishes
    def scannerData(self, req_id, rank, details, distance, benchmark, projection, legsStr):
        super().scannerData(req_id, rank, details, distance, benchmark, projection, legsStr)
        print("got scanner data")
        print(details.contract)

        data = {
            'secType': details.contract.secType,
            'secId': details.contract.secId,
            'exchange': details.contract.primaryExchange,
            'symbol': details.contract.symbol
        }

        print(data)
        
        # Put the data into the queue
        data_queue.put(data)


# called by charting library when the
def get_bar_data(symbol, timeframe):
    print(f"getting bar data for {symbol} {timeframe}")

    contract = Contract()
    contract.symbol = symbol
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    what_to_show = 'TRADES'
    
    #now = datetime.datetime.now().strftime('%Y%m%d %H:%M:%S')
    chart.spinner(True)

    client.reqHistoricalData(
        2, contract, '', '30 D', timeframe, what_to_show, True, 2, False, []
    )

    time.sleep(1)
       
    chart.watermark(symbol)



    
    
      
      
# implement an Interactive Brokers market scanner
def do_scan(scan_code):
    scannerSubscription = ScannerSubscription()
    scannerSubscription.instrument = "STK"
    scannerSubscription.locationCode = "STK.US.MAJOR"
    scannerSubscription.scanCode = scan_code

    tagValues = []
    tagValues.append(TagValue("optVolumeAbove", "1000"))
    tagValues.append(TagValue("avgVolumeAbove", "10000"))

    client.reqScannerSubscription(7002, scannerSubscription, [], tagValues)
    time.sleep(1)

    display_scan()

    client.cancelScannerSubscription(7002)


#  get new bar data when the user enters a different symbol
def on_search(chart, searched_string):
    get_bar_data(searched_string, chart.topbar['timeframe'].value)
    chart.topbar['symbol'].set(searched_string)


# get new bar data when the user changes timeframes
def on_timeframe_selection(chart):
    print("selected timeframe")
    print(chart.topbar['symbol'].value, chart.topbar['timeframe'].value)
    get_bar_data(chart.topbar['symbol'].value, chart.topbar['timeframe'].value)
    

# callback for when the user changes the position of the horizontal line
def on_horizontal_line_move(chart, line):
    print(f'Horizontal line moved to: {line.price}')




    # create a table on the UI, pass callback function for when a row is clicked
    table = chart.create_table(
                    width=0.4, 
                    height=0.5,
                    headings=('symbol', 'value'),
                    widths=(0.7, 0.3),
                    alignments=('left', 'center'),
                    position='left', func=on_row_click
                )

    # poll queue for any new scan results
    try:
        while True:
            data = data_queue.get_nowait()
            # create a new row in the table for each scan result
            table.new_row(data['symbol'], '')
    except queue.Empty:
        print("empty queue")
    finally:
        print("done")


# called when we want to update what is rendered on the chart 
def update_chart():
    global current_lines

    try:
        bars = []
        while True:  # Keep checking the queue for new data
            data = data_queue.get_nowait()
            bars.append(data)
    except queue.Empty:
        print("empty queue")
    finally:
        # once we have received all the data, convert to pandas dataframe
        df = pd.DataFrame(bars)
        print(df)

        # set the data on the chart
        chart.set(df)
        
        if not df.empty:
            # draw a horizontal line at the high
            chart.horizontal_line(df['high'].max(), func=on_horizontal_line_move)

            # if there were any indicator lines on the chart already (eg. SMA), clear them so we can recalculate
            if current_lines:
                for l in current_lines:
                    l.delete()
            
            current_lines = []

            # calculate any new lines to render
            # create a line with SMA label on the chart
            line = chart.create_line(name='SMA 50')
            line.set(pd.DataFrame({
                'time': df['date'],
                f'SMA 50': df['close'].rolling(window=50).mean()
            }).dropna())
            current_lines.append(line)

            # once we get the data back, we don't need a spinner anymore
            chart.spinner(False)


  #analyse using ChatGPT4

    
import base64
from openai import OpenAI

OPENAI_API_KEY = ""
OPENAI_ORG_ID = ""

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

client = OpenAI(organization=OPENAI_ORG_ID)

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
  
def analyze_chart(chart_path):
    base64_image = encode_image(chart_path)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this chart. Include the symbol and discuss the price action."},
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                },
                },
            ],
            }
        ]
    )

    return response.choices[0].message.content
