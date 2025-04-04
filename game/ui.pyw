import time 
import os 
import sys
import json 
import random

import torch

import numpy as np
import pandas as pd 

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import seaborn as sns

# loading the balance PG shell 
from models.BalancePG import BalancePG, generate_policy, create_grids

# Black Jack Env
from GameEngine import GameEngine

class BlackjackUI:
    def __init__(self, root):
        self.root = root

        self.root.title("Blackjack RL - SDSC6007")
        self.root.geometry("1500x750")
        self.root.protocol("WM_DELETE_WINDOW", lambda: (self.root.destroy(), sys.exit()))
        
        # money
        self.money = 64
        self.balance_pg = BalancePG(4,2,self.money)
        self.balance_pg.load_state_dict(torch.load('./checkpoints/Balance_PG.pth'))
        
        # RL Algorithms 
        self.policy_options = [("Stand Only", "Stand_Only"),
                               ("Deep Q Learning (No Counting Cards)", "Deep_Q_learning"),
                               ("Policy Gradient (No Counting Cards)", "Batch_Policy_Gradient"),
                               ("Policy Gradient (Balance Driven)", "Balance_PG"),
                               ("Policy Gradient Actor + Critic", "AC_Policy_Gradient"),
                               ("PPO", "PPO"),
                               ("Basic Strategy", "basic_strategy")]
        
        # coins 
        self.coin_image = self._load_coin_image("images/coins.png", (50, 50)) 
        
        # Load an initial Random Policy 
        with open(f'./policies/Stand_Only.json', 'r') as f:
            self.q = json.load(f)

        # utils
        self.rank_map = {1: 'ace'}
        self.winnings = []

        # Load the background image
        self.original_bg = Image.open("images/background6.png")

        # Load card images 
        self.card_images = self.load_card_images("images")

        # Game Status Mapper: 
        self.status_mapper = {1:'✨✨ You Won ✨✨', -1: '💸💸 You Lost', 0: 'Push 🥶🥶🥶'}
        
        # arrow 
        self.arrow_image = self._load_coin_image("images/red-left arrow.png", (80, 40))
        
        # Game engine
        self.engine = GameEngine()
        self.obs = self.engine.obs

        # Layout
        self.setup_layout()

    def show_endgame_screen(self, result_text):
        self.hit_button.config(state="disabled")
        self.stick_button.config(state="disabled")
        self.policy_button.config(state="disabled")
        self.simulate_button.config(state="disabled")

        # Disable buttons
        # Draw overlay
        canvas_width = self.table_canvas.winfo_width()
        canvas_height = self.table_canvas.winfo_height()

        self.overlay = self.table_canvas.create_rectangle(
            0, 0, canvas_width, canvas_height,
            fill="grey", stipple="gray50", tags="endgame"
        )

        # Banner image
        image_path_map = {
            '✨✨ You Won ✨✨': "images/win.png",
            '💸💸 You Lost': "images/lose.png",
            'Push 🥶🥶🥶': "images/push.png"
        }
        result_img_path = image_path_map.get(result_text, "images/push.png")
        img = Image.open(result_img_path).resize((550, 550))
        self.result_image = ImageTk.PhotoImage(img)

        self.result_img_id = self.table_canvas.create_image(
            canvas_width // 2,
            canvas_height // 2 - 90,
            image=self.result_image,
            tags="endgame"
        )

        # Countdown
        self.countdown_text = self.table_canvas.create_text(
            canvas_width // 2,
            canvas_height // 2 + 190,
            text="NEXT GAME IN 3...",
            fill="black",
            font=("Roboto", 30, "bold"),
            tags="endgame"
        )

        # Bring overlay to front
        self.table_canvas.tag_raise("endgame")
        self.countdown_timer(3)

    def countdown_timer(self, seconds):
        if seconds > 0:
            self.table_canvas.itemconfigure(self.countdown_text, text=f"NEXT GAME IN {seconds}...")
            self.root.after(1000, lambda: self.countdown_timer(seconds - 1))

            self.hit_button.config(state="disable")
            self.stick_button.config(state="disable")
            self.policy_button.config(state="disable")
            self.simulate_button.config(state="disabled")

        else:
            self.table_canvas.itemconfigure(self.countdown_text, text="Starting new game...")

            # Re-enable buttons or reset game state here
            self.hide_endgame_screen()
            self.engine._new_game()
            
            player_sum, dealer_card = self.engine.obs[0], self.engine.obs[1]
            info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_card}\n"
            self.refresh_layout(info_text, mode='sys')
            self.update_arrow('player')

            # Re-enable buttons if needed
            self.hit_button.config(state="normal")
            self.stick_button.config(state="normal")
            self.policy_button.config(state="normal")
            self.simulate_button.config(state="normal")

    def hide_endgame_screen(self):
        self.table_canvas.delete("endgame")

        # Re-show everything
        self.table_canvas.itemconfigure("player-cards", state="normal")
        self.table_canvas.itemconfigure("dealer-cards", state="normal")
        self.table_canvas.itemconfigure("arrow", state="normal")
        self.table_canvas.itemconfigure("state", state="normal")

        self.hit_button.config(state="active")
        self.stick_button.config(state="active")
        self.policy_button.config(state="active")
        self.simulate_button.config(state="active")

    def load_card_images(self, folder):
        images = {}
        for filename in os.listdir(folder):
            if filename.endswith(".png"):
                path = os.path.join(folder, filename)
                img = Image.open(path).resize((70, 110))
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

        # toggles 
        self.plot_mode = tk.StringVar(value="Cumulative")

        plot_selector = ttk.OptionMenu(
            self.trend,
            self.plot_mode,
            "Cumulative",  # default value
            "Cumulative",
            "Rolling Avg",
            "Summary Bars",
            command=lambda _: self.draw_dealer_distribution()
        )
        plot_selector.pack(anchor="ne", padx=0, pady=(2, 0))

        self.dealer_bar_frame = ttk.LabelFrame(self.root, text="Optimized Policy Selection")
        self.dealer_bar_frame.place(relx=0.62, rely=0.42, relwidth=0.37, relheight=0.28)
        self.dealer_bar_frame.configure(style="White.TLabelframe")

        self.radio_frame = ttk.Frame(self.dealer_bar_frame, style="White.TFrame")
        self.radio_frame.pack(side="left", fill="y", padx=5, pady=5)

        self.plot_frame = ttk.Frame(self.dealer_bar_frame, style="White.TFrame")
        self.plot_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self.option_var = tk.StringVar(value="Stand_Only")  # default option

        # Define the policy options
        # Add radio buttons inside the dealer_bar_frame
        for text, value in self.policy_options:
            rb = ttk.Radiobutton(
                self.radio_frame,
                text=text,
                variable=self.option_var,
                value=value,
                command=self.update_option
            )
            rb.pack(anchor="w", pady=2)

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
        self.hit_button.place(relx=0.05, rely=0.9, relwidth=0.2, relheight=0.06)
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
        self.stick_button.place(relx=0.275, rely=0.9, relwidth=0.2, relheight=0.06)
        self.stick_button.config(command=lambda: self.handle_action(0))
        
        # Policy 
        self.policy_button = tk.Button(
            self.table_frame,
            text="Q*(S, A)",
            bg="blue",               # Modern teal
            fg="white",                 # White text
            font=("Minecraftia", 12, "bold"),
            relief="flat",              # Flat, modern style
            cursor="hand2"              # Hand cursor on hover
        )
        self.policy_button.place(relx=0.5, rely=0.9, relwidth=0.2, relheight=0.06)
        self.policy_button.config(command=lambda: self.use_policy())

        # reset 
        self.reset_button = tk.Button(
            self.table_frame,
            text="Reset",
            bg="grey",               # Modern teal
            fg="white",                 # White text
            font=("Minecraftia", 12, "bold"),
            relief="flat",              # Flat, modern style
            cursor="hand2"              # Hand cursor on hover
        )
        self.reset_button.place(relx=0.725, rely=0.825, relwidth=0.2, relheight=0.06)
        self.reset_button.config(command=lambda: self.reset_winnings())

        # Stimulation
        self.simulate_button = tk.Button(
            self.table_frame,
            text="Q* (50 iters)",
            bg="purple",
            fg="white",
            font=("Minecraftia", 12, "bold"),
            relief="flat",
            cursor="hand2"
        )
        self.simulate_button.place(relx=0.725, rely=0.9, relwidth=0.2, relheight=0.06)
        self.simulate_button.config(command=self.run_qstar_simulation)
    
    def reset_winnings(self):
        """  Reset Winnings """
        
        self.winnings = []
        self.money = 64
        self.draw_dealer_distribution()
        self.table_canvas.itemconfigure("money-text", text=f"{self.money}")

    def run_qstar_simulation(self):
        """Runs K episodes using the selected Q* policy."""
        self.hit_button.config(state="disabled")
        self.stick_button.config(state="disabled")
        self.policy_button.config(state="disabled")
        self.simulate_button.config(state="disabled")

        selected = self.option_var.get()
        self.logger(f"\n[SIMULATION] Running 50 games with policy: {selected}\n")

        for i in range(50):
            self.engine._new_game()
            self.obs = self.engine.obs
            done = False

            while not done:
                action = self.q.get(str(self.obs), random.choice([0, 1]))
                self.obs, reward, terminated, truncated, _ = self.engine.step(action)
                done = terminated or truncated

            # Final dealer reveal step for accurate result
            self.engine.refresh()
            player_sum = self.obs[0]
            dealer_sum = sum(self.engine.dealer_hand)

            # over-riding the reward
            if dealer_sum == player_sum:
                reward = 0
            elif dealer_sum > player_sum:
                reward = -1
            else:
                reward = 1

            self.money += reward

            # update PG
            policy = self.update_balance_pg('Balance_PG')

            if selected == 'Balance_PG':
                print('Updating Balance PG...')
                self.q = generate_policy(self.balance_pg, self.money)
                self.grid_plots('Balance_PG', policy)
                self.root.update()
            
            self.winnings.append(reward)
            self.logger(f"Game {i+1}: Result -> {self.status_mapper.get(reward, 'Unknown')}\n")

        self.draw_dealer_distribution()
        self.table_canvas.itemconfigure("money-text", text=f"{self.money}")

        # Re-enable buttons
        self.hit_button.config(state="normal")
        self.stick_button.config(state="normal")
        self.policy_button.config(state="normal")
        self.simulate_button.config(state="normal")

        self.logger(f"\n[SIMULATION COMPLETE] Q* ran for 50 games.\n")
        self.logger(f"{'--'}"*50 + '\n')


    def use_policy(self):
        """ Function used to use the selected policy """

        # extract the state information from the game 
        action = self.q.get(str(self.obs), random.choice([0,1]))

        selected = self.option_var.get()

        action_mapper = {1: 'hit', 0: 'stick'}
        self.logger(f'{selected}\'s policy says to: {action_mapper.get(action)}\n')

        self.handle_action(action)

        return True
    
    def update_balance_pg(self, selected):
        """ Function used to update balance pg"""

        self.balance_pg = BalancePG(4,2,self.money)
        self.balance_pg.load_state_dict(torch.load('./checkpoints/Balance_PG.pth'))

        # generate plots 
        self.balance_pg.generate_q_table(usable_ace= True,starting_pos=12)
        _, policy = create_grids(self.balance_pg, usable_ace=True)

        return policy
    
    def update_option(self):
        """ Updated selections """
        selected = self.option_var.get()

        self.option = selected  # update internal policy variable
        self.logger(f"[INFO] Selected policy: {self.option}\n")

        if selected == 'Balance_PG':
            
            # generate policy 
            self.policy = self.update_balance_pg('Balance_PG')
            self.grid_plots(selected, self.policy)
            self.q = generate_policy(self.balance_pg, self.money)

        else:

            # update plots 
            self.policy = np.load(f'./checkpoints/{selected}.npy')
            self.grid_plots(selected, self.policy)

            # load optimized policy         
            with open(f'./policies/{selected}.json', 'r') as f:
                self.q = json.load(f)

    def grid_plots(self, title, policy_grid):
        fig, ax = plt.subplots(figsize=(4, 2.5))  # Smaller and wider

        # Set figure and axis background to black
        fig.patch.set_facecolor("black")
        ax.set_facecolor("black")

        ax = sns.heatmap(
            policy_grid,
            linewidth=0,
            annot=True,
            cmap="Accent_r",
            cbar=False,
            ax=ax,
            annot_kws={"size": 8}
        )

        ax.set_title(f"Policy: {title}", fontsize=10)
        ax.set_xlabel("Player sum", fontsize=9)
        ax.set_ylabel("Dealer showing", fontsize=9)
        ax.set_xticklabels(range(12, 22), fontsize=8)
        ax.set_yticklabels(["A"] + list(range(2, 11)), fontsize=8)

        # Tighter layout and no figure padding
        fig.tight_layout(pad=0.7)

        # Optional: transparent background (depends on visual preference)
        fig.patch.set_facecolor("none")
        ax.set_facecolor("none")

        # Optional: custom legend
        legend_elements = [
            Patch(facecolor="lightgreen", edgecolor="black", label="Hit"),
            Patch(facecolor="grey", edgecolor="black", label="Stick"),
        ]
        ax.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=7)

        matplotlib.pyplot.close()

        self.show_plot_in_frame(fig)

    def show_plot_in_frame(self, fig):
        # Remove previous canvas
        if hasattr(self, "current_canvas") and self.current_canvas:
            self.current_canvas.get_tk_widget().destroy()

        # Show new figure in the dedicated plot frame
        self.current_canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        self.current_canvas.draw()
        self.current_canvas.get_tk_widget().pack(fill="both", expand=True)

    
    def draw_game_state(self, event):
        """ This function is used to draw the game state at launch"""
        player_sum, dealer_card, usable_ace = self.obs
        info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_card}\n"
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
            info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_card}\n"
            self.create_text(canvas_width, canvas_height, info_text)
            self.draw_dealer_distribution()
            
        else:
            self.create_text(canvas_width, canvas_height, info_text)

        self.display_cards()
        self.table_canvas.itemconfigure("money-text", text=f"{self.money}")

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
        self.engine.refresh()

        self.obs = obs
        player_sum, dealer_card = obs[0], obs[1]

        # Display player's current state
        info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_card}\n"
        self.logger(info_text)
        self.refresh_layout(info_text)

        # If the game is over due to busting
        if player_sum > 21:
            self.show_endgame_screen('💸💸 You Lost')
            self.logger(f"Game Over — BUST! (Reward: {reward})\n")
            self.logger(f"{'--'}"*50 + '\n')

            self.winnings.append(reward)
            self.money -= 1

            return True
            
        # If terminated, show dealer's full hand one card at a time (with delay)
        elif terminated:
            self.hit_button.config(state="disabled")
            self.stick_button.config(state="disabled")
            self.policy_button.config(state="disabled")
            self.simulate_button.config(state="disabled")
            
            self.logger("\nDealer's Hand Revealed:\n")
            self.update_arrow('dealer')
            
            # not sure why we need this... but the gym env and the game logic is not working properly at times?.. hardcoding this fix for now zzz
            self.engine.step(0)
            self.engine.refresh()

            print(self.engine.dealer_hand)
            revealed_cards = []
            for idx, card in enumerate(self.engine.dealer_hand):
                revealed_cards.append(card)

                # Update canvas with new dealer info
                dealer_hand_text = ", ".join(str(c) for c in revealed_cards)
                info_text = f"Player cards: {self.engine.player_hand} | Player Sum: {player_sum}\nDealer Hand: {dealer_hand_text} | Dealer Sum: {np.sum(revealed_cards)}\n"
                self.refresh_layout(info_text)
                self.dealer_reveal(revealed_cards)
                self.logger(f"{card}\n")

                self.engine.step(0)
                self.engine.refresh()
                self.root.update()
                time.sleep(1)
                
            # Show game result
            dealer_sum = np.sum(revealed_cards)
            dealer_sum = np.sum(revealed_cards)

            # override the reward from env... its a bit buggy

            if dealer_sum > 21:
                reward = 1  # Dealer busts, player wins
            elif dealer_sum == player_sum:
                reward = 0  # Draw
            elif dealer_sum < player_sum:
                reward = 1  # Player wins
            else:
                reward = -1  # Dealer wins

            result_text = self.status_mapper.get(reward, 'Push (draw)')
            self.money += reward

            self.winnings.append(reward)
            self.logger(f'Dealer Sum: {np.sum(revealed_cards)}\n')
            self.logger(f"\nGame Over — {result_text} (Reward: {reward})\n")
            self.logger(f"{'--'}"*50 + '\n')
            
            self.show_endgame_screen(result_text)

            return True

    def draw_dealer_distribution(self):
        # Clear old canvas if it exists
        if hasattr(self, 'dealer_chart_canvas'):
            self.dealer_chart_canvas.get_tk_widget().destroy()
            self.dealer_chart_canvas = None

        # Compute win/loss/draw stats
        wins = self.winnings.count(1)
        losses = self.winnings.count(-1)
        draws = self.winnings.count(0)
        total = len(self.winnings)

        if total > 0:
            win_rate = wins / total * 100
            loss_rate = losses / total * 100
            draw_rate = draws / total * 100
        else:
            win_rate = loss_rate = draw_rate = 0

        # Add win/loss/draw text at top-right
        summary_text = (
            f"Win: {win_rate:.1f}%  "
            f"Loss: {loss_rate:.1f}%  "
            f"Draw: {draw_rate:.1f}%"
        )

        # Create the figure and plot
        fig, ax = plt.subplots(figsize=(5, 3))
        x = np.arange(len(self.winnings))
        mode = self.plot_mode.get()

        if mode == "Cumulative":
            y = np.cumsum(self.winnings)
            ax.set_title("Cumulative Winnings", fontsize=10)
            ax.axhline(
                0,
                color="#ff5555",              # soft red
                linestyle="--",
                linewidth=1.5,
                label="Break-even"
            )
            ax.plot(x, y, label="Cumulative Winnings", color="#00eaff",            
                linewidth=2.5,
                marker="o",
                markersize=5,
                markerfacecolor="white")
            
        elif mode == "Rolling Avg":
            ax.set_title("Rolling Average (10)", fontsize=10)
            y = pd.Series(self.winnings).rolling(window=10).mean()
            ax.plot(x, y, label="Rolling Avg (10)", color="#00eaff",            
                linewidth=2.5,
                marker="o",
                markersize=5,
                markerfacecolor="white")
            
            ax.axhline(
                0,
                color="#ff5555",              # soft red
                linestyle="--",
                linewidth=1.5,
                label="Break-even"
            )

        elif mode == "Summary Bars":
            # Compute stats
            wins = self.winnings.count(1)
            losses = self.winnings.count(-1)
            draws = self.winnings.count(0)
            total = len(self.winnings)

            counts = [wins, losses, draws]
            labels = ["Win", "Loss", "Draw"]
            colors = ["green", "red", "gray"]

            ax.bar(labels, counts, color=colors)

            ax.set_title("Game Outcome Distribution", fontsize=10)
            ax.set_ylabel("Number of Games", fontsize=9)

        # Aesthetic updates
        ax.set_facecolor("#2b2b3d")
        ax.set_xlabel("Round", fontsize=8)
        ax.set_ylabel("Winnings", fontsize=8)
        ax.grid(color="#444444", linestyle="--", linewidth=0.5)
        ax.legend(facecolor="#2b2b3d", edgecolor="gray", 
                  labelcolor="white", loc="upper left",
                  fontsize=8)
        
        ax.text(
            0.98, 0.95, summary_text,
            transform=ax.transAxes,
            fontsize=9,
            color="white",
            ha="right", va="top",
            bbox=dict(facecolor="#333333", alpha=0.6, edgecolor="none", boxstyle="round,pad=0.4")
        )
        ax.text(
            0.01, 0.02, f"Games Played: {total}",
            transform=ax.transAxes,
            fontsize=9,
            color="white",
            ha="left", va="bottom",
            bbox=dict(facecolor="#333333", alpha=0.6, edgecolor="none", boxstyle="round,pad=0.4")
        )

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


        # Arrow 
        self.table_canvas.create_image(event.width*0.9, 
                                       event.height*0.6, 
                                       image=self.arrow_image, 
                                       tags="arrow")

        # Observation display
        self.draw_game_state(event)
        self.draw_dealer_distribution()

        # Redraw the coin image
        self.coin_image_id = self.table_canvas.create_image(
            event.width - 120, 20,  # top-right corner padding
            anchor="nw",
            image=self.coin_image,
            tags="money-coin"
        )

        # Redraw the money text next to the coin
        self.money_text_id = self.table_canvas.create_text(
            event.width - 60, 30,
            anchor="nw",
            text=f"{self.money}",
            font=("Helvetica", 18, "bold"),
            fill="yellow",
            tags="money-text"
        )



if __name__ == "__main__":
    root = tk.Tk()
    app = BlackjackUI(root)
    root.mainloop()
    
