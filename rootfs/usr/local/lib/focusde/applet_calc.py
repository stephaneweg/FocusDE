#!/usr/bin/env python3
# Focus DE - applet Calculatrice (widget embarquable dans panel_host).
import gi, ast, operator, sys
import os; sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import focus_theme
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow,
       ast.USub: operator.neg, ast.UAdd: operator.pos}

def safe_eval(expr):
    def ev(n):
        if isinstance(n, ast.Constant): return n.value
        if isinstance(n, ast.BinOp): return OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp): return OPS[type(n.op)](ev(n.operand))
        raise ValueError("invalide")
    return ev(ast.parse(expr.replace("×", "*").replace("÷", "/"), mode="eval").body)

EXPAND = False
CSS = """
.calc-card { background: @surface@; border-radius: 16px; border: 1px solid @border@; padding: 8px; }
.calc-disp { font-size: 22px; color: @ink@; padding: 6px 10px; background: @bg@; border-radius: 10px; }
.calc-card button { background: @bg@; color: @ink@; border-radius: 10px; border: 1px solid @border@;
                    margin: 2px; padding: 8px 0; font-size: 16px; }
.calc-card button:hover { background: @accent@; }
.calc-card button.op { background: @accent@; color: @accent_ink@; }
.calc-card button.op:hover { background: @accent_strong@; }
.calc-card button.eq { background: @accent_strong@; color: @accent_ink@; font-weight: bold; }
"""

class CalcWidget(Gtk.Box):
    def __init__(self, ctx=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        card.get_style_context().add_class("calc-card")
        self.disp = Gtk.Entry(); self.disp.set_text("0"); self.disp.set_editable(False)
        self.disp.set_alignment(1.0); self.disp.get_style_context().add_class("calc-disp")
        card.pack_start(self.disp, False, False, 0)
        grid = Gtk.Grid(); grid.set_column_homogeneous(True); grid.set_row_homogeneous(True)
        card.pack_start(grid, True, True, 0)
        rows = [["C", "←", "%", "÷"], ["7", "8", "9", "×"], ["4", "5", "6", "-"],
                ["1", "2", "3", "+"], ["0", ".", "=", ""]]
        for r, row in enumerate(rows):
            for c, lab in enumerate(row):
                if not lab: continue
                b = Gtk.Button(label=lab)
                if lab in "÷×-+%": b.get_style_context().add_class("op")
                if lab == "=": b.get_style_context().add_class("eq")
                b.connect("clicked", self.press, lab)
                grid.attach(b, c, r, 2 if lab == "0" else 1, 1)
        self.pack_start(card, True, True, 0); self.cleared = True

    def press(self, _b, lab):
        cur = self.disp.get_text()
        if lab == "C": self.disp.set_text("0"); self.cleared = True; return
        if lab == "←": self.disp.set_text(cur[:-1] or "0"); return
        if lab == "=":
            try: r = safe_eval(cur)
            except Exception: self.disp.set_text("Erreur"); self.cleared = True; return
            if isinstance(r, float) and r.is_integer(): r = int(r)
            self.disp.set_text(str(r)); self.cleared = True; return
        if lab == "%":
            try:
                r = safe_eval(cur) / 100.0
                self.disp.set_text(str(int(r) if r.is_integer() else r))
            except Exception: self.disp.set_text("Erreur")
            self.cleared = True; return
        if self.cleared and lab not in "÷×-+": cur = ""; self.cleared = False
        elif self.cleared: self.cleared = False
        if cur in ("0", "Erreur") and lab not in "÷×-+.": cur = ""
        self.disp.set_text(cur + lab)

def make(ctx=None): return CalcWidget(ctx)

if __name__ == "__main__":
    GLib.set_prgname("focus-applet-calc")
    pal = focus_theme.for_activity(focus_theme.focused_ws_name())
    prov = Gtk.CssProvider(); prov.load_from_data(focus_theme.css("window{background:@bg@;}" + CSS, pal))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    w = Gtk.Window(); w.add(make()); w.connect("destroy", Gtk.main_quit); w.show_all(); Gtk.main()
