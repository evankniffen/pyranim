"""
gippity-generated code that removes the nimbers and fixes a selection bug
"""

import tkinter as tk
from tkinter import simpledialog, messagebox

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

        # ===== TOP BAR =====
        top_frame = tk.Frame(root)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.player_label = tk.Label(top_frame, text="", font=("Helvetica", 14, "bold"))
        self.player_label.pack(side=tk.LEFT, padx=10)

        new_game_btn = tk.Button(top_frame, text="New Game", command=self.new_game)
        new_game_btn.pack(side=tk.RIGHT, padx=10)

        # ===== MAIN AREA: CANVAS + SIDEBAR =====
        main_frame = tk.Frame(root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Canvas for drawing pyramid (left)
        self.canvas = tk.Canvas(main_frame, width=800, height=600, bg="white")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Sidebar for Dyck path (right)
        sidebar = tk.Frame(main_frame, width=260, relief=tk.RAISED, bd=2)
        sidebar.pack(side=tk.RIGHT, fill=tk.Y)

        sidebar_title = tk.Label(
            sidebar,
            text="Dyck Path (current state)",
            font=("Helvetica", 12, "bold"),
            justify=tk.CENTER,
        )
        sidebar_title.pack(pady=5)

        # Visual Dyck path canvas
        self.dyck_canvas = tk.Canvas(
            sidebar,
            width=220,
            height=220,
            bg="white",
            highlightthickness=1,
            highlightbackground="black",
        )
        self.dyck_canvas.pack(pady=5, padx=5)

        # Text display for Dyck word + permutation
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

        # Bind clicks on the canvas
        self.canvas.bind("<Button-1>", self.on_click)

        # Game state
        self.n_tiers = 0
        # (row, col) -> dict(row,col,x,y,id,present)
        self.chips = {}
        # 0 = Alice (blue), 1 = Bob (red)
        self.current_player = 0

        self.new_game()

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

        self.init_chips()
        self.update_player_label()
        self.update_dyck_from_board()

    def init_chips(self):
        n = self.n_tiers
        width = int(self.canvas.cget("width"))
        height = int(self.canvas.cget("height"))
        center_x = width // 2
        base_y = height - 80

        # row 0 = bottom, row n-1 = top
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
        """
        Count how many present chips are directly above chip (row, col).

        In this indexing:
        - (row + 1, col - 1) is above-left
        - (row + 1, col) is above-right
        """
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
        """
        A chip is removable iff fewer than 2 chips are above it.
        """
        return self.count_chips_above(rc) < 2

    # ==============================
    #         CLICK HANDLER
    # ==============================

    def on_click(self, event):
        clicked_rc = self.find_chip_at(event.x, event.y)
        if clicked_rc is None:
            self.status_label.config(text="stop that chud")
            return

        chip = self.chips[clicked_rc]
        if not chip["present"]:
            self.status_label.config(text="stop that chud")
            return

        if not self.is_removable(clicked_rc):
            self.status_label.config(text="stop that chud")
            return

        # Valid move
        self.status_label.config(text="")
        to_remove = self.compute_supported_chain(clicked_rc)
        self.apply_removal(to_remove)

        # Update Dyck path and permutation after the move
        self.update_dyck_from_board()

        # Check for game over
        if not any(ch["present"] for ch in self.chips.values()):
            winner = "Alice" if self.current_player == 0 else "Bob"
            color = "blue" if self.current_player == 0 else "red"
            messagebox.showinfo("Game Over", f"{winner} ({color}) wins!")
            self.canvas.unbind("<Button-1>")
            self.root.after(100, lambda: self.canvas.bind("<Button-1>", self.on_click))
            return

        # Switch players
        self.current_player = 1 - self.current_player
        self.update_player_label()

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
        """
        Given a chosen chip (row, col), return the set of all chips that must be
        removed: the chosen chip plus every chip above that is supported directly
        or indirectly by something already in the removal set.

        Indexing: row 0 = bottom.
        A chip at (row, col) with row > 0 is supported by
        (row - 1, col) and (row - 1, col + 1), if those exist.
        """
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
    #        DYCK / PERM
    # ==============================

    def update_dyck_from_board(self):
        """
        Compute the board's Dyck word via board_to_dyck_word and show:
          - Dyck word
          - 132-avoiding permutation from Krattenthaler's bijection
          - Visual NE-path in the square.
        """
        dw = board_to_dyck_word(self.chips, self.n_tiers)
        if not dw:
            self.dyck_display.config(
                text="Board empty\nDyck word: \nPermutation: "
            )
            self.dyck_canvas.delete("all")
            return

        try:
            ud = dyck_word_to_UD(dw)
            perm = dyck_word_to_132_avoiding_permutation(dw)
            perm_str = format_permutation(perm)

            self.dyck_display.config(
                text=(
                    f"Dyck Word: {ud}\n"
                    f"Permutation: {perm_str}"
                )
            )
            self.draw_dyck_path(dw)
        except Exception as e:
            self.dyck_display.config(
                text=f"Error computing Dyck path / permutation:\n{e}"
            )
            self.dyck_canvas.delete("all")

    def draw_dyck_path(self, dw):
        """
        Draw the Dyck path on self.dyck_canvas as a North/East path
        from (0,0) to (N,N), where 1 -> North and 0 -> East.
        """
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

        # Draw light grid + diagonal y = x
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