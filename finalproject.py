import random
import tkinter as tk
from tkinter import messagebox, Toplevel

# --- DECK AND PATTERNS ---
SUITS_UNICODE = {'Hearts': '♥', 'Diamonds': '♦', 'Clubs': '♣', 'Spades': '♠'}
VALUES = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
FULL_DECK = [(str(v), s) for v in VALUES for s in SUITS_UNICODE.keys()]

patterns = {
    "All Even Numbers": lambda hand: all(v in ['2', '4', '6', '8', '10'] for v, s in hand),
    "All Odd Numbers": lambda hand: all(v in ['A', '3', '5', '7', '9'] for v, s in hand),
    "Sum of Values > 25": lambda hand: sum(int(v) if v.isdigit() else (11 if v == 'A' else 10) for v, s in hand) > 25,
    "Two Reds and Two Blacks": lambda hand: sum(1 for v, s in hand if s in ['Hearts', 'Diamonds']) == 2,
    "All Different Suits": lambda hand: len(set(s for v, s in hand)) == 4,
    "Contains an Ace": lambda hand: any(v == 'A' for v, s in hand),
    "At Least Two Picture Cards": lambda hand: sum(1 for v, s in hand if v in ['J', 'Q', 'K']) >= 2,
}

# --- GLOBAL VARIABLES ---
score_history = []
player_hand = []
dealer_hand = []
reselection_attempts = 0

# --- CARD FORMATTING ---
def format_card(card, use_unicode=True):
    value, suit = card
    if use_unicode:
        return f"{value} {SUITS_UNICODE[suit]}"
    return f"{value}-{suit[0]}" # Simple format for non-unicode consoles

def format_hand(hand, use_unicode=True):
    return ", ".join(format_card(c, use_unicode) for c in hand)

# --- GAME LOGIC ---
def start_new_round(dealer_labels, player_labels, hint_label, result_label, choose_button):
    global dealer_hand, player_hand, reselection_attempts
    random.shuffle(FULL_DECK)
    dealer_hand = FULL_DECK[:4]
    player_hand = []
    reselection_attempts = 0 # Reset counter for the new round

    # Safe print for debugging purposes
    print(f"--- NEW ROUND ---")
    print(f"Secret Dealer Hand: {format_hand(dealer_hand, use_unicode=False)}")

    hint_label.config(text="Hint will appear here.")
    result_label.config(text="")
    for i in range(4):
        dealer_labels[i].config(text="[Hidden]")
        player_labels[i].config(text=f"[Card {i+1}]")
    choose_button.config(state="normal")

def get_hint(pattern_name, hint_label):
    if not player_hand:
        messagebox.showwarning("Choose Hand First", "You must choose your hand before getting a hint.")
        return
    if pattern_name == "Select a Pattern":
        messagebox.showwarning("Invalid Request", "Please select a pattern to get a hint for.")
        return

    pattern_func = patterns.get(pattern_name)
    if not pattern_func: return

    result = pattern_func(dealer_hand)
    if result:
        hint_label.config(text=f"Hint: The dealer's hand DOES match the '{pattern_name}' pattern.")
    else:
        hint_label.config(text=f"Hint: The dealer's hand DOES NOT match the '{pattern_name}' pattern.")

def play_game(pattern_name, result_label, score_label, dealer_labels):
    if not player_hand:
        messagebox.showwarning("Invalid Request", "Please choose your hand and make a pattern guess.")
        return
    if pattern_name == "Select a Pattern":
        messagebox.showwarning("No Pattern Selected", "Please select a pattern before playing.")
        return

    for i, card in enumerate(dealer_hand):
        dealer_labels[i].config(text=format_card(card))

    if patterns.get(pattern_name)(dealer_hand):
        result_label.config(text="You guessed correctly! You Win!", fg="#008000")
        score_history.append("Win")
    else:
        result_label.config(text=f"Sorry, that's not right. The hand was: {format_hand(dealer_hand)}", fg="#d00000")
        score_history.append("Loss")
    
    wins = score_history.count('Win')
    losses = score_history.count('Loss')
    score_label.config(text=f"Score: Wins - {wins}, Losses - {losses}")

# --- CARD SELECTION WINDOW with new logic ---
def open_card_selector(root, player_labels, choose_button):
    global reselection_attempts # Use the global counter

    selector_win = Toplevel(root)
    selector_win.title("Select 4 Cards")
    selector_win.configure(bg="#f0f0f0")
    selector_win.grab_set()

    tk.Label(selector_win, text="Please check exactly 4 cards.", font=("Arial", 10), bg="#f0f0f0").pack(pady=5)
    
    card_frame = tk.Frame(selector_win, bg="#f0f0f0", padx=10, pady=10)
    card_frame.pack()
    
    check_vars = {}
    check_buttons = {}

    def on_check():
        selected_cards = [card for card, var in check_vars.items() if var.get() == 1]
        if len(selected_cards) >= 4:
            for card, button in check_buttons.items():
                if check_vars[card].get() == 0:
                    button.config(state="disabled")
        else:
            for button in check_buttons.values():
                button.config(state="normal")

    for i, card in enumerate(FULL_DECK):
        var = tk.IntVar()
        check_vars[card] = var
        chk = tk.Checkbutton(card_frame, text=format_card(card), variable=var,
                              onvalue=1, offvalue=0, command=on_check,
                              bg="#f0f0f0", activebackground="#d0d0d0")
        chk.grid(row=i % 13, column=i // 13, sticky="w", padx=10)
        check_buttons[card] = chk

    def confirm_selection():
        global player_hand, reselection_attempts

        selected_cards = [card for card, var in check_vars.items() if var.get() == 1]
        if len(selected_cards) != 4:
            messagebox.showerror("Selection Error", "You must select exactly 4 cards.")
            return
        
        player_hand = selected_cards
        
        # Update main window display to show the player's choice
        for i, card in enumerate(player_hand):
            player_labels[i].config(text=format_card(card))
        
        # --- NEW LOGIC: Check for matches with the dealer's hand ---
        matches = set(player_hand) & set(dealer_hand)
        
        if len(matches) > 0:
            # Matches were found, so lock in the hand and close the window
            messagebox.showinfo("Match Found!", f"{len(matches)} of your cards matched the dealer's hand: {format_hand(list(matches))}")
            choose_button.config(state="disabled") # Lock the "Choose Your Cards" button
            selector_win.destroy()
        else:
            # No matches found, check attempts and allow re-selection
            reselection_attempts += 1
            if reselection_attempts >= 3:
                messagebox.showwarning("No Matches", "No cards matched and you are out of re-selection attempts. Your hand is now locked.")
                choose_button.config(state="disabled")
                selector_win.destroy()
            else:
                remaining = 3 - reselection_attempts
                messagebox.showwarning("No Matches", f"No cards matched the dealer's hand. Please try again. You have {remaining} attempt(s) left.")
                # Reset the selection window UI for another try
                for var in check_vars.values():
                    var.set(0)
                for btn in check_buttons.values():
                    btn.config(state="normal")

    confirm_btn = tk.Button(selector_win, text="Confirm Hand", command=confirm_selection)
    confirm_btn.pack(pady=10)

# --- MAIN GUI (UNCHANGED) ---
def main():
    root = tk.Tk()
    root.title("Art Dealer - A Game of Deduction")
    root.geometry("700x550")
    root.configure(bg="#f0f0f0")

    dealer_frame = tk.Frame(root, pady=10, bg="#d9d9d9")
    dealer_frame.pack(fill="x", padx=10, pady=5)
    player_frame = tk.Frame(root, pady=10, bg="#f0f0f0")
    player_frame.pack(fill="x", padx=10, pady=5)
    controls_frame = tk.Frame(root, pady=20, bg="#d9d9d9")
    controls_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(dealer_frame, text="Art Dealer's Hand", font=("Arial", 14, "bold"), bg="#d9d9d9").pack()
    dealer_cards_ui = tk.Frame(dealer_frame, bg="#d9d9d9", pady=5)
    dealer_cards_ui.pack()
    dealer_labels = [tk.Label(dealer_cards_ui, text="[Hidden]", font=("Courier", 12, "bold"), bg="#ffffff", relief="groove", width=10) for _ in range(4)]
    for label in dealer_labels:
        label.pack(side="left", padx=5)

    tk.Label(player_frame, text="Your Hand", font=("Arial", 14, "bold"), bg="#f0f0f0").pack()
    player_cards_ui = tk.Frame(player_frame, bg="#f0f0f0", pady=5)
    player_cards_ui.pack()
    player_labels = [tk.Label(player_cards_ui, text="[Card 1]", font=("Courier", 12), bg="#ffffff", relief="groove", width=10) for _ in range(4)]
    for label in player_labels:
        label.pack(side="left", padx=5)

    choose_cards_button = tk.Button(player_frame, text="Choose Your Cards", font=("Arial", 12), command=lambda: open_card_selector(root, player_labels, choose_cards_button))
    choose_cards_button.pack(pady=10)
    
    pattern_var = tk.StringVar(value="Select a Pattern")
    pattern_menu = tk.OptionMenu(controls_frame, pattern_var, *patterns.keys())
    pattern_menu.config(font=("Arial", 11), width=25)
    pattern_menu.pack(pady=5)
    
    hint_label = tk.Label(controls_frame, text="Hint will appear here.", font=("Arial", 12, "italic"), fg="#00008b", bg="#d9d9d9")
    hint_label.pack(pady=5)

    result_label = tk.Label(controls_frame, text="", font=("Arial", 14, "bold"), bg="#d9d9d9")
    result_label.pack(pady=5)

    score_label = tk.Label(controls_frame, text="Score: Wins - 0, Losses - 0", font=("Arial", 10), fg="#333333", bg="#d9d9d9")
    score_label.pack()

    buttons_frame = tk.Frame(controls_frame, bg="#d9d9d9", pady=10)
    buttons_frame.pack()
    
    tk.Button(buttons_frame, text="Get Hint", font=("Arial", 12), command=lambda: get_hint(pattern_var.get(), hint_label)).pack(side="left", padx=5)
    tk.Button(buttons_frame, text="Play Game", font=("Arial", 12, "bold"), command=lambda: play_game(pattern_var.get(), result_label, score_label, dealer_labels)).pack(side="left", padx=5)
    tk.Button(buttons_frame, text="New Round", font=("Arial", 12), command=lambda: start_new_round(dealer_labels, player_labels, hint_label, result_label, choose_cards_button)).pack(side="left", padx=5)
    tk.Button(buttons_frame, text="Exit", font=("Arial", 12), command=root.quit).pack(side="left", padx=5)

    start_new_round(dealer_labels, player_labels, hint_label, result_label, choose_cards_button)
    root.mainloop()

if __name__ == "__main__":
    main()