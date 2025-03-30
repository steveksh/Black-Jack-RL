import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
import numpy as np
import sys

from GameEngine import GameEngine

matplotlib.use('Agg')

class BlackjackUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Blackjack RL - SDSC6007")
        self.root.geometry("1400x900")

        self.engine = GameEngine()
        self.winnings = []
        self.total_reward = 0
        self.game_count = 0
        self.game_ended = False
        self.dealer_card_counts = [0] * 11

        self.card_images = self.load_card_images("images")
        self.coin_image_red = self.load_coin_image("images/coins.png")
        self.coin_image_blue = self.load_coin_image("images/blue-chip.png")
        self.bg_image_raw = Image.open("images/background.gif")
        self.win_image = ImageTk.PhotoImage(Image.open("images/win.png").resize((400, 400)))
        self.lose_image = ImageTk.PhotoImage(Image.open("images/lose.png").resize((400, 400)))
        self.back_card_image = ImageTk.PhotoImage(Image.open("images/back.png").resize((100, 150)))
        self.bg_image = None

        self.player_hand = []
        self.dealer_hand = []
        self.player_hand_values = []
        self.dealer_hand_values = []
        self.suit_memory = {}

        self.setup_layout()
        self.start_new_game()

    def load_card_images(self, folder):
        images = {}
        for filename in os.listdir(folder):
            if filename.endswith(".png") and "_of_" in filename:
                path = os.path.join(folder, filename)
                img = Image.open(path).resize((100, 150))
                key = filename.replace(".png", "")
                images[key] = ImageTk.PhotoImage(img)
        return images

    def load_coin_image(self, path):
        if os.path.exists(path):
            img = Image.open(path).resize((40, 40))
            return ImageTk.PhotoImage(img)
        return None

    def value_to_card_image_key(self, value):
        if value in self.suit_memory:
            return self.suit_memory[value]
        suits = ['spades', 'hearts', 'clubs', 'diamonds']
        suit = random.choice(suits)
        if value == 0 or value == 1:
            rank = 'ace'
        elif value == 10:
            rank = random.choice(['10', 'jack', 'queen', 'king'])
        else:
            rank = str(value)
        key = f"{rank}_of_{suit}"
        self.suit_memory[value] = key
        return key

    def setup_layout(self):
        self.root.configure(bg="#dfe7e2")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Red.TButton", font=("Roboto", 16), padding=10, foreground="red")
        style.configure("Blue.TButton", font=("Roboto", 16), padding=10, foreground="blue")

        self.table_frame = ttk.Frame(self.root)
        self.table_frame.place(relx=0.01, rely=0.01, relwidth=0.6, relheight=0.98)
        self.table_canvas = tk.Canvas(self.table_frame, bg="black")
        self.table_canvas.pack(fill=tk.BOTH, expand=True)
        self.table_canvas.bind("<Configure>", self.resize_background)

        self.dealer_bar_frame = ttk.LabelFrame(self.root, text="Dealer Card Distribution")
        self.dealer_bar_frame.place(relx=0.62, rely=0.01, relwidth=0.37, relheight=0.3)

        self.chart_frame = ttk.LabelFrame(self.root, text="Winnings Trend")
        self.chart_frame.place(relx=0.62, rely=0.32, relwidth=0.37, relheight=0.3)

        self.log_frame = ttk.LabelFrame(self.root, text="Game Log")
        self.log_frame.place(relx=0.62, rely=0.63, relwidth=0.37, relheight=0.3)
        self.log_text = tk.Text(self.log_frame, height=20, bg="black", fg="white", font=("Roboto", 12))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.hit_button = ttk.Button(self.table_frame, text="Hit", style="Red.TButton", command=self.hit)
        self.hit_button.place(relx=0.25, rely=0.92, relwidth=0.2)
        self.stick_button = ttk.Button(self.table_frame, text="Stick", style="Blue.TButton", command=self.stick)
        self.stick_button.place(relx=0.55, rely=0.92, relwidth=0.2)

        self.next_button = ttk.Button(self.table_frame, text="Next Game", command=self.start_new_game)

    def resize_background(self, event):
        self.table_canvas.delete("bg")
        if self.bg_image_raw:
            resized = self.bg_image_raw.resize((event.width, event.height))
            self.bg_image = ImageTk.PhotoImage(resized)
            self.table_canvas.create_image(0, 0, anchor=tk.NW, image=self.bg_image, tags="bg")
        self.display_cards()

    def log_action(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def display_cards(self):
        self.table_canvas.delete("cards")

        # Always reveal full dealer hand if game ended (bust or stick)
        dealer_display = self.dealer_hand
        dealer_title = "Dealer's Hand"
        player_total = sum([min(10, v) if v > 1 else 11 for v in self.player_hand_values])
        player_title = f"Player's Hand (Total: {player_total})"

        dealer_card_x = 400 + (len(dealer_display) - 1) * 55
        self.table_canvas.create_text(dealer_card_x, 30, text=dealer_title, fill="white", font=("Roboto", 18, "bold"), tags="cards")

        for i, card in enumerate(dealer_display):
            y = 60
            if card in self.card_images:
                self.table_canvas.create_image(400 + i * 110, y, anchor=tk.NW, image=self.card_images[card], tags="cards")

        for i, card in enumerate(self.player_hand):
            y = 470
            if card in self.card_images:
                self.table_canvas.create_image(400 + i * 110, y, anchor=tk.NW, image=self.card_images[card], tags="cards")

        player_card_x = 400 + (len(self.player_hand) - 1) * 55
        self.table_canvas.create_text(player_card_x, 640, text=player_title, fill="white", font=("Roboto", 18, "bold"), tags="cards")

        # Centered coin cluster
        coin_x = 700
        coin_y = 300
        self.table_canvas.create_image(coin_x - 20, coin_y, anchor=tk.CENTER, image=self.coin_image_red, tags="cards")
        self.table_canvas.create_image(coin_x + 20, coin_y + 10, anchor=tk.CENTER, image=self.coin_image_blue, tags="cards")

    def display_result_banner(self, result):
        if result == "YOU WIN!":
            self.table_canvas.create_image(700, 360, anchor=tk.CENTER, image=self.win_image, tags="cards")
        elif result == "YOU LOSE!":
            self.table_canvas.create_image(700, 360, anchor=tk.CENTER, image=self.lose_image, tags="cards")
        else:
            self.table_canvas.create_text(700, 360, text=result, font=("Roboto", 48, "bold"), fill="gold", tags="cards")

    def draw_trend(self):
        fig, ax = plt.subplots(figsize=(5, 2))
        x = np.arange(len(self.winnings))
        y = np.cumsum(self.winnings)
        ax.plot(x, y, label='Cumulative Winnings', color='blue')
        ax.axhline(0, color='red', linestyle='--', linewidth=2, label='Break-even')
        ax.set_title("Cumulative Winnings")
        ax.legend()
        fig.tight_layout()

        if hasattr(self, 'chart_canvas'):
            self.chart_canvas.get_tk_widget().destroy()

        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


    def display_result_banner(self, result):
        if result == "YOU WIN!":
            self.table_canvas.create_image(700, 360, anchor=tk.CENTER, image=self.win_image, tags="cards")
        elif result == "YOU LOSE!":
            self.table_canvas.create_image(700, 360, anchor=tk.CENTER, image=self.lose_image, tags="cards")
        else:
            self.table_canvas.create_text(700, 360, text=result, font=("Roboto", 48, "bold"), fill="gold", tags="cards")

    def draw_bar_chart(self):
        fig, ax = plt.subplots(figsize=(5, 2))
        ax.bar(range(1, 12), self.dealer_card_counts, color='#708090')
        ax.set_xticks(range(1, 12))
        ax.set_title("Dealer Card Value Distribution")
        fig.tight_layout()

        if hasattr(self, 'bar_canvas'):
            self.bar_canvas.get_tk_widget().destroy()

        self.bar_canvas = FigureCanvasTkAgg(fig, master=self.dealer_bar_frame)
        self.bar_canvas.draw()
        self.bar_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def hit(self):
        if self.game_ended:
            return
        raw_player, raw_dealer, reward, terminated, truncated = self.engine.play(1)
        self.player_hand_values = raw_player
        self.dealer_hand_values = raw_dealer
        self.player_hand = [self.value_to_card_image_key(v) for v in raw_player]
        self.dealer_hand = [self.value_to_card_image_key(v) for v in raw_dealer]
        self.total_reward += reward
        self.log_action("Action: Hit")
        self.log_action(f"Player hand: {self.player_hand}")

        if terminated or truncated:
            self.game_ended = True

        self.display_cards()
        self.draw_trend()

        if terminated or truncated:
            self.end_game(reward)

    def stick(self):
        if self.game_ended:
            return
        while True:
            raw_player, raw_dealer, reward, terminated, truncated = self.engine.play(0)
            if terminated or truncated:
                break
        self.player_hand_values = raw_player
        self.dealer_hand_values = raw_dealer
        self.player_hand = [self.value_to_card_image_key(v) for v in raw_player]
        self.dealer_hand = [self.value_to_card_image_key(v) for v in raw_dealer]
        self.total_reward += reward
        self.log_action("Action: Stick")
        self.log_action(f"Player hand: {self.player_hand}")
        self.game_ended = True
        self.display_cards()
        self.draw_trend()
        self.end_game(reward)

    def end_game(self, reward):
        self.game_ended = True
        self.winnings.append(self.total_reward)
        self.game_count += 1
        if reward > 0:
            self.display_result_banner("YOU WIN!")
        elif reward < 0:
            self.display_result_banner("YOU LOSE!")
        else:
            self.display_result_banner("DRAW")
        self.hit_button.state(["disabled"])
        self.stick_button.state(["disabled"])
        self.next_button.place(relx=0.4, rely=0.85, relwidth=0.2)
        self.log_action(f"Final Reward: {reward}")
        self.log_action("-"*50)

    def start_new_game(self):
        self.engine.new_game()
        self.total_reward = 0
        self.game_ended = False
        self.suit_memory = {}
        raw_player = self.engine.get_player_hand()
        raw_dealer = self.engine.get_dealer_hand(reveal=False)
        self.player_hand_values = raw_player
        self.dealer_hand_values = raw_dealer
        self.player_hand = [self.value_to_card_image_key(v) for v in raw_player]
        self.dealer_hand = [self.value_to_card_image_key(v) for v in raw_dealer]

        for card_val in raw_dealer:
            index = min(card_val if card_val > 0 else 1, 10)
            self.dealer_card_counts[index - 1] += 1

        self.display_cards()
        self.hit_button.state(["!disabled"])
        self.stick_button.state(["!disabled"])
        self.next_button.place_forget()
        self.draw_bar_chart()
        self.log_action(f"Game {self.game_count + 1} started.")
        self.log_action(f"Dealer hand: {self.dealer_hand[:1]} + [Hidden]")
        self.log_action(f"Player hand: {self.player_hand}")
        self.log_action("-"*50)

if __name__ == "__main__":
    root = tk.Tk()
    app = BlackjackUI(root)
    root.mainloop()