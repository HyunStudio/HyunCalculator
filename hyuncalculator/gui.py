"""Desktop GUI: zero web/network access; Tkinter with optional embedded Matplotlib.

The 19 legacy ML/DL/RL functions retain their original UI implementation.
"""
from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from . import __version__, legacy_ml
from .scientific import calculate
from .graphing import sample_curves
from .operations import GROUPS


LABELS = {
    'ko': {
        'title': f'HyunCalculator {__version__} | 통합 공학·금융·AI 계산기',
        'scientific': '공학용', 'graphing': '그래프', 'financial': '금융',
        'quant': '금융공학', 'programmer': '프로그래머', 'ml': 'ML', 'dl': 'DL', 'rl': 'RL',
        'language': '언어', 'calc': '계산하기', 'copy': '결과 복사', 'clear': '지우기',
        'memory_add': 'M+', 'memory_recall': 'MR', 'memory_clear': 'MC',
        'input': '수식', 'result': '결과', 'history': '계산 내역',
        'angle': '삼각함수 각도', 'plot': '그래프 그리기', 'export': 'PNG 저장',
        'functions': '함수 (줄바꿈 또는 ; 구분, 최대 8개)',
        'xmin': 'X 최솟값', 'xmax': 'X 최댓값', 'samples': '샘플 수',
        'footnote': '수익률/이자율/변동성은 소수(예: 5%=0.05)로 입력 · 금융 기능은 교육·검증용',
    },
    'en': {
        'title': f'HyunCalculator {__version__} | Scientific · Financial · AI',
        'scientific': 'Scientific', 'graphing': 'Graphing', 'financial': 'Financial',
        'quant': 'Quant', 'programmer': 'Programmer', 'ml': 'ML', 'dl': 'DL', 'rl': 'RL',
        'language': 'Language', 'calc': 'Calculate', 'copy': 'Copy result', 'clear': 'Clear',
        'memory_add': 'M+', 'memory_recall': 'MR', 'memory_clear': 'MC',
        'input': 'Expression', 'result': 'Result', 'history': 'History',
        'angle': 'Trigonometric unit', 'plot': 'Plot', 'export': 'Save PNG',
        'functions': 'Functions (newline or ;, up to 8)',
        'xmin': 'X minimum', 'xmax': 'X maximum', 'samples': 'Samples',
        'footnote': 'Rates, returns and volatility use decimals (e.g. 5%=0.05) · Educational use only',
    },
}


class ScientificTab:
    def __init__(self, parent, lang):
        self.lang = lang
        self.frame = ttk.Frame(parent, padding=18)
        self.frame.columnconfigure(0, weight=1)
        self.expression = tk.StringVar(value='sin(pi/6) + sqrt(16)')
        self.unit = tk.StringVar(value='RAD')
        self.last_result = None
        self.memory = 0.
        self.history_entries = []
        self.prompt = ttk.Label(self.frame, font=('Malgun Gothic', 13, 'bold'))
        self.prompt.grid(row=0, column=0, sticky='w')
        self.input = ttk.Entry(self.frame, textvariable=self.expression, font=('Consolas', 18))
        self.input.grid(row=1, column=0, sticky='ew', pady=(6,12))
        self.input.bind('<Return>', lambda _event: self.compute())
        commands = ttk.Frame(self.frame); commands.grid(row=2, column=0, sticky='w', pady=(0,12))
        self.calc = ttk.Button(commands, command=self.compute); self.calc.pack(side='left', padx=(0,8))
        self.copy_button = ttk.Button(commands, command=self.copy); self.copy_button.pack(side='left', padx=(0,8))
        self.clear = ttk.Button(commands, command=self.reset); self.clear.pack(side='left', padx=(0,8))
        ttk.Button(commands, text='M+', command=self.mplus).pack(side='left', padx=(0,8))
        ttk.Button(commands, text='MR', command=self.mrecall).pack(side='left', padx=(0,8))
        ttk.Button(commands, text='MC', command=self.mclear).pack(side='left', padx=(0,8))
        ttk.Combobox(commands, textvariable=self.unit, state='readonly', values=('RAD','DEG'), width=6).pack(side='left')
        self.result_heading = ttk.Label(self.frame, font=('Malgun Gothic', 12, 'bold'))
        self.result_heading.grid(row=3, column=0, sticky='w')
        self.result_text = tk.StringVar(value='')
        ttk.Label(self.frame, textvariable=self.result_text, font=('Consolas', 20),
                  background='#EDF3FA', padding=12).grid(row=4, column=0, sticky='ew', pady=(6,12))
        self.history_heading = ttk.Label(self.frame, font=('Malgun Gothic', 12, 'bold'))
        self.history_heading.grid(row=5, column=0, sticky='w')
        history_frame = ttk.Frame(self.frame); history_frame.grid(row=6, column=0, sticky='nsew', pady=(6,8))
        history_frame.columnconfigure(0, weight=1); history_frame.rowconfigure(0, weight=1)
        self.history = tk.Listbox(history_frame, font=('Consolas', 12), height=10)
        self.history.grid(row=0, column=0, sticky='nsew')
        scrollbar = ttk.Scrollbar(history_frame, orient='vertical', command=self.history.yview)
        scrollbar.grid(row=0, column=1, sticky='ns'); self.history.configure(yscrollcommand=scrollbar.set)
        self.history.bind('<Double-Button-1>', self.recall_history)
        self.frame.rowconfigure(6, weight=1)
        ttk.Label(self.frame, text='sin, cos, tan, asin, log, ln, log2, sqrt, root, factorial, comb, perm, pi, e, Ans, ^',
                  font=('Consolas', 11), wraplength=1120).grid(row=7, column=0, sticky='w')
        self.refresh_language()

    def refresh_language(self):
        l = LABELS[self.lang()]
        self.prompt.configure(text=l['input']); self.result_heading.configure(text=l['result'])
        self.history_heading.configure(text=l['history'])
        self.calc.configure(text=l['calc']); self.copy_button.configure(text=l['copy']); self.clear.configure(text=l['clear'])

    def compute(self):
        try:
            value = calculate(self.expression.get(), degrees=self.unit.get() == 'DEG',
                              variables={'Ans': self.last_result if self.last_result is not None else 0})
            self.last_result = value
            displayed = str(value) if isinstance(value, int) else f'{value:.12g}' if isinstance(value, (float, complex)) else str(value)
            self.result_text.set(displayed)
            self.history_entries.append((self.expression.get(), displayed))
            self.history.insert('end', f'{self.expression.get()} = {displayed}')
            self.history.yview_moveto(1)
        except (ValueError, TypeError, ArithmeticError, OverflowError) as exc:
            self.result_text.set(f'Error: {exc}')

    def copy(self):
        if not self.result_text.get() or self.result_text.get().startswith('Error:'):
            return
        self.frame.clipboard_clear(); self.frame.clipboard_append(self.result_text.get())

    def reset(self):
        self.expression.set(''); self.result_text.set('')

    def mplus(self):
        if self.last_result is not None and not isinstance(self.last_result, complex):
            self.memory += float(self.last_result)

    def mrecall(self):
        self.expression.set(self.expression.get()+repr(self.memory))

    def mclear(self):
        self.memory = 0.

    def recall_history(self, _event):
        selection = self.history.curselection()
        if selection:
            self.expression.set(self.history_entries[selection[0]][0])


class GraphingTab:
    def __init__(self, parent, lang):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        self.lang = lang
        self.frame = ttk.Frame(parent, padding=12)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(3, weight=1)
        self.prompt = ttk.Label(self.frame, font=('Malgun Gothic', 12, 'bold'))
        self.prompt.grid(row=0,column=0,sticky='w')
        self.equations = tk.Text(self.frame, height=3, font=('Consolas', 14))
        self.equations.insert('1.0', 'y=sin(x)\ny=cos(x)\ny=x^2/10')
        self.equations.grid(row=1,column=0,sticky='ew',pady=(6,8))
        controls = ttk.Frame(self.frame); controls.grid(row=2,column=0,sticky='ew',pady=(0,8))
        self.xmin = tk.StringVar(value='-10'); self.xmax = tk.StringVar(value='10')
        self.samples = tk.StringVar(value='1001')
        self.label_widgets=[]
        for name, variable, width in (('xmin',self.xmin,8),('xmax',self.xmax,8),('samples',self.samples,7)):
            lab=ttk.Label(controls); lab.pack(side='left',padx=(6,3)); self.label_widgets.append((name,lab))
            ttk.Entry(controls,textvariable=variable,width=width,font=('Consolas',12)).pack(side='left',padx=(0,8))
        self.unit=tk.StringVar(value='RAD')
        ttk.Combobox(controls, textvariable=self.unit, values=('RAD','DEG'), state='readonly', width=5).pack(side='left',padx=(0,8))
        self.button=ttk.Button(controls,command=self.plot); self.button.pack(side='left',padx=(0,8))
        self.export=ttk.Button(controls,command=self.save_png); self.export.pack(side='left')
        self.figure=Figure(figsize=(10,5.5),dpi=100)
        self.ax=self.figure.add_subplot(111)
        self.canvas=FigureCanvasTkAgg(self.figure,master=self.frame)
        self.canvas.get_tk_widget().grid(row=3,column=0,sticky='nsew')
        toolbar_frame=ttk.Frame(self.frame)
        toolbar_frame.grid(row=4,column=0,sticky='w')
        self.toolbar=NavigationToolbar2Tk(self.canvas, toolbar_frame, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.pack(side='left')
        self.status=tk.StringVar(value='')
        ttk.Label(self.frame,textvariable=self.status,font=('Malgun Gothic',11)).grid(row=5,column=0,sticky='w')
        self.plotted=False
        self.refresh_language()
        self.plot()

    def refresh_language(self):
        l=LABELS[self.lang()]
        self.prompt.configure(text=l['functions'])
        for name,widget in self.label_widgets: widget.configure(text=l[name])
        self.button.configure(text=l['plot']); self.export.configure(text=l['export'])

    def plot(self):
        try:
            curves=sample_curves(self.equations.get('1.0','end-1c'),float(self.xmin.get()),
                                 float(self.xmax.get()),int(self.samples.get()),
                                 degrees=self.unit.get()=='DEG')
            self.ax.clear()
            for label,x,y in curves: self.ax.plot(x,y,label=label,linewidth=1.9)
            self.ax.axhline(0,color='#777777',linewidth=.65)
            self.ax.axvline(0,color='#777777',linewidth=.65)
            self.ax.grid(True,alpha=.3)
            self.ax.set_xlabel('x'); self.ax.set_ylabel('y'); self.ax.legend(loc='best')
            self.figure.tight_layout(); self.canvas.draw()
            self.status.set(f'{len(curves)} curve(s) · {len(curves[0][1])} samples')
            self.plotted=True
        except (ValueError, ArithmeticError, OverflowError) as exc:
            self.status.set(f'Error: {exc}')

    def save_png(self):
        if not self.plotted:
            messagebox.showinfo('HyunCalculator','Draw a graph first.'); return
        path=filedialog.asksaveasfilename(title='Export graph',defaultextension='.png',
                                         filetypes=[('PNG image','*.png')])
        if path:
            self.figure.savefig(path,dpi=160)


def run_gui(initial_language: str='ko'):
    root=tk.Tk()
    root.geometry('1380x900')
    root.minsize(1020,740)
    style=ttk.Style(root)
    if 'clam' in style.theme_names(): style.theme_use('clam')
    style.configure('TButton',font=('Malgun Gothic',12),padding=(10,7))
    style.configure('TNotebook.Tab',font=('Malgun Gothic',12,'bold'),padding=(16,8))
    language={'code': initial_language}
    def get_language(): return language['code']
    top=ttk.Frame(root,padding=(12,8)); top.pack(fill='x')
    title=ttk.Label(top,font=('Malgun Gothic',15,'bold'))
    title.pack(side='left')
    switch=tk.StringVar(value='한국어' if initial_language=='ko' else 'English')
    ttk.Combobox(top,textvariable=switch,values=('한국어','English'),state='readonly',width=10,
                 font=('Malgun Gothic',12)).pack(side='right',padx=(4,8))
    language_label=ttk.Label(top,font=('Malgun Gothic',12));language_label.pack(side='right')
    notebook=ttk.Notebook(root)
    notebook.pack(fill='both',expand=True,padx=12,pady=(0,6))
    pages=[]
    def add(code,widget):
        notebook.add(widget.frame,text=LABELS[initial_language].get(code.lower(),code))
        pages.append((code,widget))
    add('Scientific',ScientificTab(notebook,get_language))
    add('Graphing',GraphingTab(notebook,get_language))
    for code,operations in GROUPS.items():
        add(code,legacy_ml.CalculatorTab(notebook,operations,get_language))
    footer=ttk.Label(root,font=('Malgun Gothic',10));footer.pack(fill='x',padx=16,pady=(0,7))
    def refresh(_event=None):
        language['code']='en' if switch.get()=='English' else 'ko'
        l=LABELS[language['code']]
        root.title(l['title']);title.configure(text=l['title'])
        language_label.configure(text=l['language']);footer.configure(text=l['footnote'])
        for code,widget in pages:
            widget.refresh_language()
            notebook.tab(widget.frame,text=l.get(code.lower(),code))
    # the language ComboBox is the last child of top? bind explicitly via named widget
    selector=next(child for child in top.winfo_children() if isinstance(child,ttk.Combobox))
    selector.bind('<<ComboboxSelected>>',refresh)
    refresh()
    root.mainloop()
