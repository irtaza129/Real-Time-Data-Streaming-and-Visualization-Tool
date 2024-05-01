import json
import websocket
import threading
import tkinter as tk
from tkinter import messagebox
from collections import deque
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import numpy as np
import matplotlib.pyplot as plt

# Your API token and App ID
api_token = "shkAzg7EtSVd17Z"
app_id = "51742"

# Deques to hold the last X ticks for processing for two different streams
tick_data = deque(maxlen=100)
tick_data_second = deque(maxlen=100)

# Counters for the occurrences of the last digit of ticks for two different streams
digit_counts = {str(digit): 0 for digit in range(10)}
digit_counts_second = {str(digit): 0 for digit in range(10)}

# GUI setup with increased size to accommodate two sets of data streams
root = tk.Tk()
root.title("Deriv API Data Stream")
root.geometry("1200x800")


# Function to create user input fields
def create_input_fields(frame, var_dict):
  for text, var in var_dict.items():
    tk.Label(frame, text=text).pack(side=tk.LEFT)
    tk.Entry(frame, textvariable=var, width=7).pack(side=tk.LEFT)


# Store user inputs for the first and second sets of data streams
user_inputs = {
    "Probability Confidence": tk.DoubleVar(),
    "Probability Threshold": tk.DoubleVar(),
    "Number of Ticks": tk.IntVar(value=100),  # Default value set to 100
    "Winning Digit": tk.IntVar(),
    "Losing Digit": tk.IntVar()
}
user_inputs_second = {
    "Probability Confidence": tk.DoubleVar(),
    "Probability Threshold": tk.DoubleVar(),
    "Number of Ticks": tk.IntVar(value=100),  # Default value set to 100
    "Winning Digit": tk.IntVar(),
    "Losing Digit": tk.IntVar()
}


# Function to update the number of ticks for processing for both streams
def update_number_of_ticks(*args):
  new_maxlen = user_inputs["Number of Ticks"].get()
  global tick_data, tick_data_second
  tick_data = deque(maxlen=new_maxlen)
  tick_data_second = deque(maxlen=new_maxlen)


# Bind the update function to the "Number of Ticks" input for both sets of inputs
user_inputs["Number of Ticks"].trace("w", update_number_of_ticks)
user_inputs_second["Number of Ticks"].trace("w", update_number_of_ticks)


# Function to process a tick and calculate percentages for both data streams
def process_tick(tick, digit_counts):
  tick_str = "{:.4f}".format(tick)
  digit = tick_str[-2] if tick_str[-1] == '0' else tick_str[-1]
  digit_counts[digit] += 1
  total_counts = sum(digit_counts.values())
  digit_percentages = {
      digit: (count / total_counts) * 100
      for digit, count in digit_counts.items()
  }
  return digit_percentages


# Real-time data plotting setup for two sets of data streams
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8), dpi=100)


# Initialize the plots with empty data
def init_plots():
  ax1.set_ylim(0, 100)
  ax1.set_xlim(0, 9)
  ax2.set_ylim(0, 100)
  ax2.set_xlim(0, 9)
  ax3.set_ylim(0, 100)
  ax3.set_xlim(0, 9)
  ax4.set_ylim(0, 100)
  ax4.set_xlim(0, 9)
  return []


# Update functions for real-time plotting for both sets of data streams
def update_plots(frame):
  # Update the first set of plots
  if tick_data:
    ax1.clear()
    ax2.clear()
    digits, percentages = zip(*sorted(
        (digit, count / max(1, sum(digit_counts.values())) * 100)
        for digit, count in digit_counts.items()))
    bars = ax1.bar(digits, percentages)
    for bar, pct in zip(bars, percentages):
      ax1.text(bar.get_x() + bar.get_width() / 2,
               bar.get_height(),
               f'{pct:.2f}%',
               ha='center',
               va='bottom')
    ax2.plot(digits, np.cumsum(percentages), label='Cumulative')
    ax2.legend()

  # Update the second set of plots
  if tick_data_second:
    ax3.clear()
    ax4.clear()
    digits_second, percentages_second = zip(*sorted(
        (digit, count / max(1, sum(digit_counts_second.values())) * 100)
        for digit, count in digit_counts_second.items()))
    bars_second = ax3.bar(digits_second, percentages_second)
    for bar, pct in zip(bars_second, percentages_second):
      ax3.text(bar.get_x() + bar.get_width() / 2,
               bar.get_height(),
               f'{pct:.2f}%',
               ha='center',
               va='bottom')
    ax4.plot(digits_second, np.cumsum(percentages_second), label='Cumulative')
    ax4.legend()


# Embed the plots in the Tkinter GUI
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

# Animation for real-time plotting for both sets of data streams
ani = animation.FuncAnimation(fig,
                              update_plots,
                              init_func=init_plots,
                              interval=1000,
                              blit=False,
                              cache_frame_data=False)

# WebSocket event handlers


# WebSocket event handlers
def on_message(ws, message):
  data = json.loads(message)
  if 'tick' in data:
    tick = float(data['tick']['quote'])
    tick_data.append(tick)
    tick_data_second.append(
        tick)  # For demonstration, we use the same tick for the second stream
    percentages = process_tick(tick, digit_counts)
    percentages_second = process_tick(
        tick, digit_counts_second)  # Process tick for the second set


def on_error(ws, error):
  messagebox.showerror("WebSocket Error", str(error))


def on_close(ws, close_status_code, close_msg):
  messagebox.showinfo("WebSocket Closed",
                      "The WebSocket connection has been closed")


# Function to initialize WebSocket connection
def on_open(ws):

  def run(*args):
    auth_message = json.dumps({"authorize": api_token})
    ws.send(auth_message)
    vol_index_symbol = "R_10"  # Confirm this symbol
    msg = json.dumps({"ticks": [vol_index_symbol], "subscribe": 1})
    ws.send(msg)

  threading.Thread(target=run).start()


# Prepare and start the WebSocket connection
def connect_to_api():
  global ws
  websocket_url = f"wss://ws.binaryws.com/websockets/v3?app_id={app_id}"
  ws = websocket.WebSocketApp(websocket_url,
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
  ws.run_forever()


# Start WebSocket in a new thread for non-blocking operation
threading.Thread(target=connect_to_api, daemon=True).start()

# Add input fields to the GUI for both sets of data streams
input_frame = tk.Frame(root)
input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
create_input_fields(input_frame, user_inputs)

input_frame_second = tk.Frame(root)
input_frame_second.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
create_input_fields(input_frame_second, user_inputs_second)


# Add a button to trigger suggestions (you might want to have separate buttons for each set of inputs)
def make_suggestions():
  probability_confidence = user_inputs["Probability Confidence"].get()
  probability_threshold = user_inputs["Probability Threshold"].get()
  num_of_ticks = user_inputs["Number of Ticks"].get()
  # Ensure the string is on a single line
  suggestion = f"Confidence: {probability_confidence}, Threshold: {probability_threshold}, Ticks: {num_of_ticks}"
  messagebox.showinfo("Suggestion", suggestion)


tk.Button(root, text="Get Suggestions",
          command=make_suggestions).pack(side=tk.BOTTOM)

tk.Button(root, text="Get Suggestions",
          command=make_suggestions).pack(side=tk.BOTTOM)


def on_closing():
  if messagebox.askokcancel("Quit", "Do you want to quit?"):
    ani.event_source.stop()
    if ws:
      ws.close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
