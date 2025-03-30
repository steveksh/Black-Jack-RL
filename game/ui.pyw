# import customtkinter
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
from PIL import Image, ImageTk
import time 
import numpy as np
import os 
import sys

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Black Jack Env
from GameEngine import GameEngine

class BlackjackUI:
    def __init__(self, root):
        self.root = root

        self.root.title("Blackjack RL - SDSC6007")
        self.root.geometry("1500x700")
        self.root.protocol("WM_DELETE_WINDOW", lambda: (self.root.destroy(), sys.exit()))

        # utils
        self.rank_map = {1: 'ace'}
        self.winnings = []

        # Load the background image
        self.original_bg = Image.open("images/background6.png")

        # Load card images 
        self.card_images = self.load_card_images("images")
        
        # Coins / Props 
        self.coin_image_red = self._load_coin_image("images/coins.png", (40, 40))
        self.coin_image_blue = self._load_coin_image("images/blue-chip.png", (40, 40))

        # Game Status Mapper: 
        self.status_mapper = {1:'✨✨ You Won ✨✨', 0: '💸💸 You Lost'}
        
        # Avatars 
        self.avatars = self.load_avatar("images")

        # Bills
        # self.bills = self._load_coin_image("images/bills.png", (200, 200))

        # arrow 
        self.arrow_image = self._load_coin_image("images/red-left arrow.png", (100, 100))
        

        # Game engine
        self.engine = GameEngine()
        self.obs = self.engine.obs

        # Layout
        self.setup_layout()
    
    def load_avatar(self, folder):
        images = {}
        for filename in os.listdir(folder):
            if filename.endswith(".png") and "avatar" in filename:
                path = os.path.join(folder, filename)
                img = Image.open(path).resize((250, 250))
                key = filename.replace(".png", "")
                images[key] = ImageTk.PhotoImage(img)
        return images


    def load_card_images(self, folder):
        images = {}
        for filename in os.listdir(folder):
            if filename.endswith(".png"):
                path = os.path.join(folder, filename)
                img = Image.open(path).resize((80, 120))
                key = filename.replace(".png", "")
                images[key] = ImageTk.PhotoImage(img)
        return images

    def _load_coin_image(self, path, size_tuples):
        img = Image.open(path).resize(size_tuples)
        return ImageTk.PhotoImage(img)

    def setup_layout(self):
        self.root.configure(bg="#dfe7e2")
        style = ttk.Style()
        style.theme_use("clam")

        # background 
        self.table_frame = tk.LabelFrame(self.root)
        self.table_frame.place(relx=0.01, rely=0.01, relwidth=0.6, relheight=0.98)
        self.table_canvas = tk.Canvas(self.table_frame, bg="black")
        self.table_canvas.pack(fill=tk.BOTH, expand=True)
        self.table_canvas.bind("<Configure>", self.resize_background)

        # logging console 
        # Trend (top-right) – Make it larger
        self.trend = ttk.LabelFrame(self.root, text="Cumulative Winnings")
        self.trend.place(relx=0.62, rely=0.01, relwidth=0.37, relheight=0.4)

        # Dealer Card Distribution – Keep it similar
        self.dealer_bar_frame = ttk.LabelFrame(self.root, text="Dealer Card Distribution")
        self.dealer_bar_frame.place(relx=0.62, rely=0.42, relwidth=0.37, relheight=0.28)

        # Game Log – Make it shorter
        self.log_frame = ttk.LabelFrame(self.root, text="Game Log")
        self.log_frame.place(relx=0.62, rely=0.71, relwidth=0.37, relheight=0.27)

        self.log_text = tk.Text(
            self.log_frame,
            height=10,
            bg="black",
            fg="white",
            font=("Roboto", 8)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Hit button
        self.hit_button = tk.Button(
            self.table_frame,
            text="Hit",
            bg="red",
            fg="white",
            font=("Minecraftia", 12, "bold"),
            relief="flat",
            cursor="hand2"              # Hand cursor on hover
        )
        self.hit_button.place(relx=0.15, rely=0.9, relwidth=0.2, relheight=0.06)
        self.hit_button.config(command=lambda: self.handle_action(1))

        # Stay button
        self.stick_button = tk.Button(
            self.table_frame,
            text="Stay",
            bg="green",
            fg="white",
            font=("Minecraftia", 12, "bold"),
            relief="flat",
            cursor="hand2"              # Hand cursor on hover
        )
        self.stick_button.place(relx=0.4, rely=0.9, relwidth=0.2, relheight=0.06)
        self.stick_button.config(command=lambda: self.handle_action(0))

        
        # Policy 
        # Replace tk.Button with this:
        self.policy_button = tk.Button(
            self.table_frame,
            text="Q*(S, A)",
            bg="blue",               # Modern teal
            fg="white",                 # White text
            font=("Minecraftia", 12, "bold"),
            relief="flat",              # Flat, modern style
            cursor="hand2"              # Hand cursor on hover
        )
        self.policy_button.place(relx=0.65, rely=0.9, relwidth=0.2, relheight=0.06)
        # self.policy_button.config(command=lambda: self.handle_action(0))

        # Avatars 
        # self.avatar_image_id = self.table_canvas.create_image(
        #     250, 100,  # x, y position within the canvas — adjust as needed
        #     anchor="ne",
        #     image=self.avatars['losing_streak_avatar']
        # )

        # Keep a reference to avoid garbage collection
        # self.table_canvas.image = self.avatars['losing_streak_avatar']
        # self.draw_dealer_distribution()
    
    def draw_game_state(self, event):
        """ This function is used to draw the game state at launch"""
        player_sum, dealer_card, usable_ace = self.obs
        info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_card}"
        self.refresh_layout(info_text, mode = 'sys')
        self.display_cards()

    def refresh_layout(self, info_text, mode = 'regular'):
        """ This function is used to refresh the gane state after launch"""

        canvas_width = self.table_canvas.winfo_width()
        canvas_height = self.table_canvas.winfo_height()

        # Clear canvas before drawing new info
        self.table_canvas.delete("state")

        if mode == 'sys':
            self.obs = self.engine.obs
            player_sum, dealer_card, usable_ace = self.obs
            info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_card}"
            self.create_text(canvas_width, canvas_height, info_text)
            self.draw_dealer_distribution()
            
        else:
            self.create_text(canvas_width, canvas_height, info_text)

        self.display_cards()

    def update_arrow(self,mode='dealer'):
        self.table_canvas.delete("arrow")

        canvas_width = self.table_canvas.winfo_width()
        canvas_height = self.table_canvas.winfo_height()

        if mode == 'dealer':
            self.table_canvas.create_image(canvas_width*0.9, 
                                        canvas_height*0.2, 
                                        image=self.arrow_image, 
                                        tags="arrow")
        else:
            self.table_canvas.create_image(canvas_width*0.9, 
                                        canvas_height*0.6, 
                                        image=self.arrow_image, 
                                        tags="arrow")

    def display_cards(self):

        self.table_canvas.delete("player-cards")
        self.table_canvas.delete("dealer-cards")

        #-------------------------------------------------------# 
        # Loading Player Cards 

        player_hand = self.engine.player_hand  # Assuming these are tuples like (rank, suit)
        player_hand_suit = self.engine.player_hand_suit

        canvas_width = self.table_canvas.winfo_width()
        canvas_height = self.table_canvas.winfo_height()

        for i, rank in enumerate(player_hand):
        
            suit = player_hand_suit[i]
            rank = self.rank_map.get(rank, rank)

            file_name = f"{rank}_of_{suit}"
            img = self.card_images[file_name]
            self.table_canvas.create_image(canvas_width/2 - len(player_hand) * 50 + i * canvas_width/10, 
                                            canvas_height / 2, 
                                            anchor=tk.NW, 
                                            image=img, 
                                            tags="player-cards")
            
        #-------------------------------------------------------# 
        # Loading Dealer Top Card

        dealer_hand = self.engine.dealer_hand[0]  # Assuming these are tuples like (rank, suit)
        dealer_hand_suit = self.engine.dealer_hand_suit[0]
        rank = self.rank_map.get(dealer_hand, dealer_hand)

        for i, f in enumerate([f"{rank}_of_{dealer_hand_suit}", "back"]):
            self.table_canvas.create_image(canvas_width/2.2 - 25 - 20 + i * canvas_width/10, 
                                            canvas_height / 8, 
                                            anchor=tk.NW, 
                                            image=self.card_images[f], 
                                            tags="dealer-cards")
    def logger(self, logs):
        self.log_text.insert(tk.END, logs)
        self.log_text.see(tk.END)

    def dealer_reveal(self, revealed_cards):
        canvas_width = self.table_canvas.winfo_width()
        canvas_height = self.table_canvas.winfo_height()
        dealer_hand_suit = self.engine.dealer_hand_suit
        buffer = 20

        job_list = []
        for idx, rank in enumerate(revealed_cards):
            rank = self.rank_map.get(rank, rank)
            job_list.append(f"{rank}_of_{dealer_hand_suit[idx]}")

        if len(job_list) < len(dealer_hand_suit):
            job_list.append("back")

        if len(job_list)>2:
            self.table_canvas.delete("dealer-cards")
            buffer = 100

        print(job_list)

        for i, f in enumerate(job_list):
            self.table_canvas.create_image(canvas_width/2.2 - buffer - len(revealed_cards) * 25 + i * canvas_width/10, 
                                            canvas_height / 8, 
                                            anchor=tk.NW, 
                                            image=self.card_images[f], 
                                            tags="dealer-cards")

    def handle_action(self, action):
        """
        This function is the main game loop.

        Parameters:
        ---
        Handles user actions: 0 = Hit, 1 = Stay
        
        """

        # Step through the game with the user action
        obs, reward, terminated, truncated, _ = self.engine.step(action)
        player_sum, dealer_card = obs[0], obs[1]

        # Display player's current state
        info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_card}"
        self.refresh_layout(info_text)

        # If the game is over due to busting
        if action == 1 and terminated and player_sum > 21:
            # self.log_text.insert(tk.END, f"Game Over — BUST! (Reward: {reward})\n")
            # self.log_text.see(tk.END)
            self.logger(f"Game Over — BUST! (Reward: {reward})\n")
            self.logger(f"{'--'}"*50 + '\n')

            self.winnings.append(reward)

            self.engine._new_game()
            info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_card}"
            self.refresh_layout(info_text, mode='sys')
            self.update_arrow('player')

        # If terminated, show dealer's full hand one card at a time (with delay)
        if terminated and player_sum <= 21:
            self.hit_button.config(state="disabled")
            self.stick_button.config(state="disabled")
            
            
            # self.log_text.insert(tk.END, "\nDealer's Hand Revealed:\n")
            # self.log_text.see(tk.END)
            self.logger("\nDealer's Hand Revealed:\n")
            self.update_arrow('dealer')

            revealed_cards = []
            for idx, card in enumerate(self.engine.dealer_hand):
                revealed_cards.append(card)

                # Update canvas with new dealer info
                dealer_hand_text = ", ".join(str(c) for c in revealed_cards)
                info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_hand_text}"
                self.refresh_layout(info_text)
                self.dealer_reveal(revealed_cards)

                # Log each card
                # self.log_text.insert(tk.END, f"{card}\n")
                # self.log_text.see(tk.END)
                self.logger(f"{card}\n")

                self.root.update()
                time.sleep(1)

            # Show game result
            result_text = self.status_mapper.get(reward, 'Push (draw)')
            self.winnings.append(reward)

            # self.log_text.insert(tk.END, f"\nGame Over — {result_text} (Reward: {reward})\n")
            # self.log_text.see(tk.END)
            self.logger(f"\nGame Over — {result_text} (Reward: {reward})\n")
            self.logger(f"{'--'}"*50 + '\n')
            
            self.engine._new_game()
            time.sleep(0.5)
            self.refresh_layout(info_text, mode='sys')
            self.update_arrow('player')

        self.hit_button.config(state="active")
        self.stick_button.config(state="active")

    def draw_dealer_distribution(self):
        # Clear old canvas if it exists
        if hasattr(self, 'dealer_chart_canvas'):
            self.dealer_chart_canvas.get_tk_widget().destroy()
            self.dealer_chart_canvas = None

        # Create the figure and plot
        fig, ax = plt.subplots(figsize=(5, 3))
        x = np.arange(len(self.winnings))
        y = np.cumsum(self.winnings)

        # Plot the cumulative winnings
        ax.plot(
            x, y,
            label="Cumulative Winnings",
            color="#00eaff",              # bright cyan
            linewidth=2.5,
            marker="o",
            markersize=5,
            markerfacecolor="white"
        )

        # Break-even line
        ax.axhline(
            0,
            color="#ff5555",              # soft red
            linestyle="--",
            linewidth=1.5,
            label="Break-even"
        )

        # Aesthetic updates
        ax.set_facecolor("#2b2b3d")
        ax.set_title("Player Cumulative Winnings", color="black", 
                     fontsize=8)
        ax.set_xlabel("Round", fontsize=8)
        ax.set_ylabel("Winnings", fontsize=8)
        ax.grid(color="#444444", linestyle="--", linewidth=0.5)
        ax.legend(facecolor="#2b2b3d", edgecolor="gray", 
                  labelcolor="white", loc="upper left",
                  fontsize=8)

        fig.tight_layout()

        # Embed the plot in the Tkinter frame
        canvas = FigureCanvasTkAgg(fig, master=self.trend)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.dealer_chart_canvas = canvas


    def create_text(self, canvas_width, canvas_height, info_text):
        self.table_canvas.create_text(
            10, 10,  # Fixed position near top-left
            anchor="nw",  # Anchor text to top-left corner of the (10, 10) point
            text=info_text,
            font=("Roboto", 10, "bold"),
            fill="white",
            tags="state"
        )

    def resize_background(self, event):
        resized = self.original_bg.resize((event.width, event.height))
        self.bg_image = ImageTk.PhotoImage(resized)

        self.table_canvas.delete("all")
        self.table_canvas.create_image(0, 0, image=self.bg_image, anchor="nw", tags="background")

        # Bills
        # self.table_canvas.create_image(event.width/2, event.height/2, anchor=tk.CENTER, image=self.bills, tags="bills")

        # Arrow 
        self.table_canvas.create_image(event.width*0.9, 
                                       event.height*0.6, 
                                       image=self.arrow_image, 
                                       tags="arrow")

        # Observation display
        self.draw_game_state(event)
        self.draw_dealer_distribution()

if __name__ == "__main__":
    root = tk.Tk()
    app = BlackjackUI(root)
    root.mainloop()
    
