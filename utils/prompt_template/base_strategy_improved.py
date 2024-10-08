import backtrader as bt


# Define a base strategy class for handling buy and sell signals and order notifications.
class BaseStrategy(bt.Strategy):
    def __init__(self, debug=True):
        """
        Initialize the strategy with parameters.

        Args:
        - debug (bool): If True, enable debug logging.

        Attributes:
        - countBuy (int): Counter for buy signals.
        - countSell (int): Counter for sell signals.
        - final_signal (int or None): Final signal for trading: 1 (long), 0 (neutral), -1 (sell).
        - debug (bool): Flag for debug mode.
        """
        self.countBuy = 0
        self.countSell = 0
        self.final_signal = None
        self.debug = debug
        self.cbuy = 0
        self.csell = 0

    def log(self, txt, dt=None):
        """
        Logging function for displaying strategy events.

        Args:
        - txt (str): Text message to log.
        - dt (datetime, optional): Date and time of the log event.
        """
        if self.debug:
            dt_day = self.datas[0].datetime.date(0)
            dt_value = dt or self.datas[0].datetime.time(0)
            print("%sT%s, %s" % (dt_day, dt_value.isoformat(), txt))

    def notify_order(self, order):
        """
        Notify when an order status changes.

        Args:
        - order (backtrader.Order): Order object containing order details.
        """
        if order.status in [order.Submitted, order.Accepted]:
            return  # Ignore submitted/accepted orders

        if order.status == order.Completed:
            if order.isbuy():
                if self.countSell > 0:
                    info_trade = "CLOSE SELL"
                    self.countSell -= 1
                else:
                    info_trade = "BUY EXECUTED"
                    self.countBuy += 1
                self.log(
                    f"{info_trade}, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm,
                    )
                )
            else:  # Sell order executed
                if self.countBuy > 0:
                    info_trade = "CLOSE BUY"
                    self.countBuy -= 1
                else:
                    info_trade = "SELL EXECUTED"
                    self.countSell += 1
                self.log(
                    f"{info_trade}, Price: %.2f, Cost: %.2f, Comm %.2f"
                    % (
                        order.executed.price,
                        order.executed.value,
                        order.executed.comm,
                    )
                )

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")

        self.order = None  # Reset the order attribute

    def execute(self) -> int:
        """
        Placeholder for executing trading logic.

        Returns:
        - int: Trading signal: 1 (long), 0 (neutral), -1 (sell), or None if no signal.
        """
        raise NotImplementedError

    def next(self):
        """
        Execute trading decisions based on the final signal generated by `execute()`.
        """
        self.final_signal = self.execute()
        if self.final_signal is None:
            return

        if self.final_signal > 0:  # Long signal
            if self.position:
                if self.countSell:
                    self.order = (
                        self.close()
                    )  # Close sell position if counter is set
            else:
                self.order = self.buy()  # Open buy position
                self.cbuy += 1

        elif self.final_signal < 0:  # Short signal
            if self.position:
                if self.countBuy:
                    self.order = (
                        self.close()
                    )  # Close buy position if counter is set
            else:
                self.order = self.sell()  # Open sell position
                self.csell += 1

