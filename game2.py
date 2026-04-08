import json
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog

from dyckPaths import (
    board_to_dyck_word,
    dyck_word_to_UD,
)
from permutations import (
    dyck_word_to_132_avoiding_permutation,
    format_permutation,
)


class PyramidNimGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Pyranim")

        self.radius = 20
        self.h_spacing = 50
        self.v_spacing = 45

        # Loaded from JSON: maps integer-encoded Dyck words to nimbers
        self.nimber_data = {}

        # Toggle state
        self.show_nimber_var = tk.BooleanVar(value=False)
        self.show_strategy_var = tk.BooleanVar(value=False)

        # Undo history
        self.history = []

        # ===== TOP BAR =====
        top_frame = tk.Frame(root)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.player_label = tk.Label(top_frame, text="", font=("Helvetica", 14, "bold"))
        self.player_label.pack(side=tk.LEFT, padx=10)

        undo_btn = tk.Button(top_frame, text="Undo", command=self.undo_move)
        undo_btn.pack(side=tk.RIGHT, padx=5)

        strategy_btn = tk.Checkbutton(
            top_frame,
            text="Show Strategy",
            variable=self.show_strategy_var,
            command=self.update_dyck_from_board,
        )
        strategy_btn.pack(side=tk.RIGHT, padx=5)

        nimber_btn = tk.Checkbutton(
            top_frame,
            text="Show Nimber",
            variable=self.show_nimber_var,
            command=self.update_dyck_from_board,
        )
        nimber_btn.pack(side=tk.RIGHT, padx=5)

        new_game_btn = tk.Button(top_frame, text="New Game", command=self.new_game)
        new_game_btn.pack(side=tk.RIGHT, padx=10)

        # ===== MAIN AREA =====
        main_frame = tk.Frame(root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, width=1000, height=900, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(main_frame, width=260, relief=tk.RAISED, bd=2)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        sidebar_title = tk.Label(
            sidebar,
            text="Dyck Path (current state)",
            font=("Helvetica", 12, "bold"),
            justify=tk.CENTER,
        )
        sidebar_title.pack(pady=5)

        self.dyck_canvas = tk.Canvas(
            sidebar,
            width=220,
            height=220,
            bg="white",
            highlightthickness=1,
            highlightbackground="black",
        )
        self.dyck_canvas.pack(pady=5, padx=5)

        self.dyck_display = tk.Label(
            sidebar,
            text="",
            justify=tk.LEFT,
            font=("Courier New", 9),
            anchor="nw",
        )
        self.dyck_display.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

        # ===== STATUS BAR =====
        self.status_label = tk.Label(root, text="", font=("Helvetica", 12))
        self.status_label.pack(side=tk.BOTTOM, pady=5)

        self.canvas.bind("<Button-1>", self.on_click)

        # Game state
        self.n_tiers = 0
        self.chips = {}
        self.current_player = 0

        self.load_nimber_json()
        self.new_game()

    # ==============================
    #      JSON / NIMBER LOOKUP
    # ==============================

    def load_nimber_json(self):
        filename = filedialog.askopenfilename(
            title="Select nimber JSON file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if not filename:
            self.nimber_data = {}
            self.status_label.config(text="No nimber JSON loaded")
            return

        try:
            with open(filename, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            self.nimber_data = {int(k): int(v) for k, v in raw_data.items()}
            self.status_label.config(text=f"Loaded nimber JSON: {filename}")

        except Exception as e:
            self.nimber_data = {}
            messagebox.showerror("JSON Load Error", f"Could not load JSON file:\n{e}")

    def dyck_word_to_int_key(self, dw):
        key = 0
        for i in range(len(dw)):
            key += dw[i] * (2 ** i)
        return key

    def lookup_nimber(self, dw):
        if not dw:
            return 0

        key = self.dyck_word_to_int_key(dw)
        return self.nimber_data.get(key, None)

    # ==============================
    #      GAME SETUP / DRAWING
    # ==============================

    def new_game(self):
        n = simpledialog.askinteger(
            "New Game",
            "Enter number of tiers (n):",
            minvalue=1,
            maxvalue=15,
        )
        if n is None:
            if self.n_tiers == 0:
                n = 3
            else:
                return

        self.n_tiers = n
        self.current_player = 0
        self.chips.clear()
        self.canvas.delete("all")
        self.status_label.config(text="")
        self.history.clear()

        self.init_chips()
        self.update_player_label()
        self.update_dyck_from_board()

    def init_chips(self):
        n = self.n_tiers
        width = int(self.canvas.cget("width"))
        height = int(self.canvas.cget("height"))
        center_x = width // 2
        base_y = height - 80

        for row in range(n):
            row_len = n - row
            total_width = (row_len - 1) * self.h_spacing
            start_x = center_x - total_width / 2
            y = base_y - row * self.v_spacing

            for col in range(row_len):
                x = start_x + col * self.h_spacing
                chip_id = self.canvas.create_oval(
                    x - self.radius,
                    y - self.radius,
                    x + self.radius,
                    y + self.radius,
                    fill="white",
                    outline="black",
                    width=2,
                )
                self.chips[(row, col)] = {
                    "row": row,
                    "col": col,
                    "x": x,
                    "y": y,
                    "id": chip_id,
                    "present": True,
                }

    def update_player_label(self):
        if self.current_player == 0:
            self.player_label.config(text="Current Player: Alice (blue)", fg="blue")
        else:
            self.player_label.config(text="Current Player: Bob (red)", fg="red")

    # ==============================
    #       MOVE VALIDATION
    # ==============================

    def count_chips_above(self, rc):
        row, col = rc
        count = 0

        above_left = (row + 1, col - 1)
        above_right = (row + 1, col)

        if above_left in self.chips and self.chips[above_left]["present"]:
            count += 1
        if above_right in self.chips and self.chips[above_right]["present"]:
            count += 1

        return count

    def is_removable(self, rc):
        return self.count_chips_above(rc) < 2

    # ==============================
    #         UNDO SUPPORT
    # ==============================

    def capture_state(self):
        return {
            "current_player": self.current_player,
            "present": {
                rc: chip["present"] for rc, chip in self.chips.items()
            },
        }

    def restore_state(self, snapshot):
        self.current_player = snapshot["current_player"]

        for rc, present in snapshot["present"].items():
            chip = self.chips[rc]
            chip["present"] = present
            if present:
                self.canvas.itemconfig(
                    chip["id"],
                    fill="white",
                    outline="black",
                    width=2,
                )
            else:
                self.canvas.itemconfig(
                    chip["id"],
                    fill=self.canvas.cget("bg"),
                    outline="",
                )

        self.update_player_label()
        self.status_label.config(text="")
        self.update_dyck_from_board()

    def undo_move(self):
        if not self.history:
            self.status_label.config(text="Nothing to undo")
            return

        snapshot = self.history.pop()
        self.restore_state(snapshot)

    # ==============================
    #         CLICK HANDLER
    # ==============================

    def on_click(self, event):
        clicked_rc = self.find_chip_at(event.x, event.y)
        if clicked_rc is None:
            self.status_label.config(text="Cannot remove that.")
            return

        chip = self.chips[clicked_rc]
        if not chip["present"]:
            self.status_label.config(text="Cannot remove that.")
            return

        if not self.is_removable(clicked_rc):
            self.status_label.config(text="Cannot remove that.")
            return

        self.history.append(self.capture_state())

        self.status_label.config(text="")
        to_remove = self.compute_supported_chain(clicked_rc)
        self.apply_removal(to_remove)

        if not any(ch["present"] for ch in self.chips.values()):
            self.update_dyck_from_board()
            winner = "Alice" if self.current_player == 0 else "Bob"
            color = "blue" if self.current_player == 0 else "red"
            messagebox.showinfo("Game Over", f"{winner} ({color}) wins!")
            return

        self.current_player = 1 - self.current_player
        self.update_player_label()
        self.update_dyck_from_board()

    def find_chip_at(self, x, y):
        for (row, col), chip in self.chips.items():
            if not chip["present"]:
                continue
            dx = x - chip["x"]
            dy = y - chip["y"]
            if dx * dx + dy * dy <= self.radius * self.radius:
                return (row, col)
        return None

    # ==============================
    #      SUPPORT / REMOVAL
    # ==============================

    def compute_supported_chain(self, start_rc):
        to_remove = {start_rc}

        changed = True
        while changed:
            changed = False
            for (row, col), chip in self.chips.items():
                if not chip["present"]:
                    continue
                if (row, col) in to_remove:
                    continue
                if row == 0:
                    continue

                below1 = (row - 1, col)
                below2 = (row - 1, col + 1)

                if below1 in to_remove or below2 in to_remove:
                    to_remove.add((row, col))
                    changed = True

        return to_remove

    def apply_removal(self, to_remove):
        for rc in to_remove:
            chip = self.chips[rc]
            if chip["present"]:
                chip["present"] = False
                self.canvas.itemconfig(
                    chip["id"],
                    fill=self.canvas.cget("bg"),
                    outline="",
                )

    # ==============================
    #       STRATEGY ANALYSIS
    # ==============================

    def get_removable_moves(self):
        moves = []
        for rc, chip in self.chips.items():
            if chip["present"] and self.is_removable(rc):
                moves.append(rc)
        return moves

    def board_snapshot_present(self):
        return {rc: chip["present"] for rc, chip in self.chips.items()}

    def board_to_ascii_from_present(self, present_map):
        lines = []
        border = "*" * (2 * self.n_tiers + 3)
        lines.append(border)

        for i in range(self.n_tiers):
            row = self.n_tiers - i - 1
            line = "* "
            line += " " * row
            for col in range(self.n_tiers - row):
                line += "0 " if present_map.get((row, col), False) else "- "
            line += " " * row
            line += "*"
            lines.append(line)

        lines.append(border)
        return "\n".join(lines)

    def simulate_move(self, start_rc):
        present_before = self.board_snapshot_present()

        to_remove = self.compute_supported_chain(start_rc)
        for rc in to_remove:
            self.chips[rc]["present"] = False

        present_after = self.board_snapshot_present()
        dw = board_to_dyck_word(self.chips, self.n_tiers)
        nimber = self.lookup_nimber(dw)
        ud = dyck_word_to_UD(dw) if dw else ""

        for rc, present in present_before.items():
            self.chips[rc]["present"] = present

        return {
            "move": start_rc,
            "to_remove": to_remove,
            "present_after": present_after,
            "dw": dw,
            "ud": ud,
            "nimber": nimber,
        }

    def print_strategy(self, current_dw, current_nimber):
        print("\n=== Strategy for current state ===")
        print("Current Dyck path:", dyck_word_to_UD(current_dw) if current_dw else "(empty)")
        print("Current nimber: *" + str(current_nimber))

        next_states = []
        for move in self.get_removable_moves():
            result = self.simulate_move(move)
            next_states.append(result)

        if not next_states:
            print("No legal moves.")
            print("==============================\n")
            return

        print("Next states:")
        for result in next_states:
            print(
                f"move {result['move']} -> {result['ud']} | nimber = *{result['nimber']}"
            )

        winning_moves = [result for result in next_states if result["nimber"] == 0]

        if winning_moves:
            print("Winning moves:")
            for result in winning_moves:
                print(f"move {result['move']} -> {result['ud']} | nimber = *0")
                print(self.board_to_ascii_from_present(result["present_after"]))
                print()
        else:
            print("Winning moves: none")

        print("==============================\n")

    # ==============================
    #        DYCK / PERM / NIMBER
    # ==============================

    def update_dyck_from_board(self):
        dw = board_to_dyck_word(self.chips, self.n_tiers)

        if not dw:
            lines = [
                "Board empty",
                "Dyck word: ",
                "Permutation: ",
            ]
            if self.show_nimber_var.get():
                lines.append("Nimber: 0")
            self.dyck_display.config(text="\n".join(lines))
            self.dyck_canvas.delete("all")

            if self.show_strategy_var.get():
                self.print_strategy([], 0)
            return

        try:
            ud = dyck_word_to_UD(dw)
            perm = dyck_word_to_132_avoiding_permutation(dw)
            perm_str = format_permutation(perm)
            nimber = self.lookup_nimber(dw)

            lines = [
                f"Dyck Word: {ud}",
                f"Permutation: {perm_str}",
            ]

            if self.show_nimber_var.get():
                lines.append(f"Nimber: {nimber}")

            self.dyck_display.config(text="\n".join(lines))
            self.draw_dyck_path(dw)

            if self.show_strategy_var.get():
                self.print_strategy(dw, nimber)

        except Exception as e:
            self.dyck_display.config(
                text=f"Error computing Dyck path / permutation / nimber:\n{e}"
            )
            self.dyck_canvas.delete("all")

    def draw_dyck_path(self, dw):
        canvas = self.dyck_canvas
        canvas.delete("all")
        if not dw:
            return

        N = sum(dw)
        if N <= 0:
            return

        width = int(canvas.cget("width"))
        height = int(canvas.cget("height"))
        size = min(width, height)
        margin = 20
        inner = size - 2 * margin

        for i in range(N + 1):
            x = margin + inner * i / N
            canvas.create_line(x, margin, x, margin + inner, fill="#dddddd")
            y = margin + inner * i / N
            canvas.create_line(margin, y, margin + inner, y, fill="#dddddd")

        x0 = margin
        y0 = margin + inner
        x1 = margin + inner
        y1 = margin
        canvas.create_line(x0, y0, x1, y1, fill="gray", dash=(3, 3))

        x = 0
        y = 0
        points = []

        px = margin + inner * x / N
        py = margin + inner * (N - y) / N
        points.append((px, py))

        for step in dw:
            if step == 1:
                y += 1
            else:
                x += 1
            px = margin + inner * x / N
            py = margin + inner * (N - y) / N
            points.append((px, py))

        flat = []
        for (px, py) in points:
            flat.extend([px, py])

        canvas.create_line(*flat, width=2, fill="black")


if __name__ == "__main__":
    root = tk.Tk()
    app = PyramidNimGUI(root)
    root.mainloop()
