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
from .appearance import (AppearancePreferences, load_preferences, save_preferences,
                         apply_appearance)


LABELS = {
    'ko': {
        'title': f'HyunCalculator {__version__} | 통합 공학·금융·AI 계산기',
        'scientific': '공학용', 'graphing': '그래프', 'financial': '금융',
        'quant': '금융공학', 'programmer': '프로그래머', 'codegen': '코드 생성', 'about': '제작자·후원', 'ml': 'ML', 'dl': 'DL', 'rl': 'RL',
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
        'quant': 'Quant', 'programmer': 'Programmer', 'codegen': 'Code Generator', 'about': 'About', 'ml': 'ML', 'dl': 'DL', 'rl': 'RL',
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
                  style='Result.TLabel', padding=12).grid(row=4, column=0, sticky='ew', pady=(6,12))
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
        self._palette=None
        self.refresh_language()
        self.plot()

    def refresh_language(self):
        l=LABELS[self.lang()]
        self.prompt.configure(text=l['functions'])
        for name,widget in self.label_widgets: widget.configure(text=l[name])
        self.button.configure(text=l['plot']); self.export.configure(text=l['export'])

    def apply_palette(self, palette):
        """Keep chart axes, tick marks and legends readable in each theme."""
        self._palette=palette
        self.figure.patch.set_facecolor(palette['surface'])
        self.ax.set_facecolor(palette['field'])
        self.ax.tick_params(axis='both',colors=palette['foreground'])
        self.ax.xaxis.label.set_color(palette['foreground'])
        self.ax.yaxis.label.set_color(palette['foreground'])
        for spine in self.ax.spines.values():
            spine.set_color(palette['border'])
        self.ax.grid(True,color=palette['grid'],alpha=0.35)
        legend=self.ax.get_legend()
        if legend is not None:
            legend.get_frame().set_facecolor(palette['surface'])
            legend.get_frame().set_edgecolor(palette['border'])
            for item in legend.get_texts():
                item.set_color(palette['foreground'])
        self.canvas.draw_idle()

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
            if self._palette is not None:
                self.apply_palette(self._palette)
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


def run_gui(initial_language: str='ko', *, start_mainloop: bool=True,
            appearance_path=None):
    """Launch bilingual desktop app. Optional no-loop mode is for GUI smoke tests."""
    root=tk.Tk()
    root.geometry('1550x900')
    root.minsize(1100,690)
    style=ttk.Style(root)
    if 'clam' in style.theme_names(): style.theme_use('clam')
    language={'code': initial_language if initial_language in ('ko','en') else 'ko'}
    def get_language(): return language['code']

    prefs=load_preferences(appearance_path)
    top=ttk.Frame(root,padding=(12,10))
    top.pack(fill='x')
    title=ttk.Label(top,font=('Malgun Gothic',16,'bold'))
    title.pack(side='left',padx=(0,12))
    switch=tk.StringVar(value='한국어' if language['code']=='ko' else 'English')
    language_selector=ttk.Combobox(top,textvariable=switch,values=('한국어','English'),
                                   state='readonly',width=9,font=('Malgun Gothic',12))
    language_selector.pack(side='right',padx=(5,7))
    language_label=ttk.Label(top,font=('Malgun Gothic',12))
    language_label.pack(side='right')
    theme_choice=tk.StringVar(value=prefs.theme)
    theme_selector=ttk.Combobox(top,textvariable=theme_choice,
                                values=('dark','light','high-contrast'),
                                state='readonly',width=14)
    theme_selector.pack(side='right',padx=(6,12))
    theme_label=ttk.Label(top)
    theme_label.pack(side='right')
    size_choice=tk.StringVar(value=f'{round(prefs.font_scale*100)}%')
    size_selector=ttk.Combobox(top,textvariable=size_choice,
                               values=('100%','125%','150%','175%'),
                               state='readonly',width=7)
    size_selector.pack(side='right',padx=(6,12))
    size_label=ttk.Label(top)
    size_label.pack(side='right')

    notebook=ttk.Notebook(root)
    notebook.pack(fill='both',expand=True,padx=12,pady=(0,7))
    pages=[]
    def add(code,widget):
        notebook.add(widget.frame,text=LABELS[language['code']].get(code.lower(),code))
        pages.append((code,widget))
    add('Scientific',ScientificTab(notebook,get_language))
    add('Graphing',GraphingTab(notebook,get_language))
    for code,operations in GROUPS.items():
        add(code,legacy_ml.CalculatorTab(notebook,operations,get_language))
    add('Codegen',CodeGeneratorTab(notebook,get_language))
    add('About',AboutTab(notebook,get_language))
    footer=ttk.Label(root,font=('Malgun Gothic',11))
    footer.pack(fill='x',padx=16,pady=(0,8))

    def refresh(_event=None):
        language['code']='en' if switch.get()=='English' else 'ko'
        l=LABELS[language['code']]
        root.title(l['title'])
        title.configure(text='HyunCalculator')
        language_label.configure(text=l['language'])
        theme_label.configure(text='테마' if language['code']=='ko' else 'Theme')
        size_label.configure(text='글꼴' if language['code']=='ko' else 'Text size')
        footer.configure(text=l['footnote']+' · Ctrl +/- 글꼴 확대/축소' if language['code']=='ko'
                          else l['footnote']+' · Ctrl +/- text size')
        for code,widget in pages:
            widget.refresh_language()
            notebook.tab(widget.frame,text=l.get(code.lower(),code))
    language_selector.bind('<<ComboboxSelected>>',refresh)

    def apply_preferences(*_events, persist=True):
        try:
            requested_scale=float(size_choice.get().rstrip('%'))/100
        except (ValueError, TypeError):
            requested_scale=1.25
        updated=AppearancePreferences.parse({'theme':theme_choice.get(),
                                             'font_scale':requested_scale})
        theme_choice.set(updated.theme)
        size_choice.set(f'{round(updated.font_scale*100)}%')
        palette=apply_appearance(root,style,updated)
        for _code,widget in pages:
            if hasattr(widget,'apply_palette'):
                widget.apply_palette(palette)
        root.hyuncalculator_preferences=updated
        if persist:
            try:
                save_preferences(updated, appearance_path)
            except OSError as exc:
                footer.configure(text=f'Appearance not saved: {exc}')
        return updated

    def zoom(direction):
        choices=(100,125,150,175)
        current=int(size_choice.get().rstrip('%'))
        idx=min(range(len(choices)), key=lambda k:abs(choices[k]-current))
        size_choice.set(f'{choices[max(0,min(len(choices)-1,idx+direction))]}%')
        apply_preferences()
        return 'break'

    def toggle_contrast(_event=None):
        theme_choice.set('dark' if theme_choice.get()=='high-contrast' else 'high-contrast')
        apply_preferences()
        return 'break'

    theme_selector.bind('<<ComboboxSelected>>',apply_preferences)
    size_selector.bind('<<ComboboxSelected>>',apply_preferences)
    for seq in ('<Control-plus>','<Control-equal>','<Control-KP_Add>'):
        root.bind_all(seq,lambda _e:zoom(1))
    for seq in ('<Control-minus>','<Control-KP_Subtract>'):
        root.bind_all(seq,lambda _e:zoom(-1))
    root.bind_all('<Control-0>',lambda _e: (size_choice.set('100%'),apply_preferences(),'break')[-1])
    root.bind_all('<Alt-Shift-h>',toggle_contrast)

    def cycle_tab(direction):
        current=notebook.index('current')
        notebook.select((current+direction)%notebook.index('end'))
        return 'break'

    root.bind_all('<Control-Next>',lambda _event:cycle_tab(1))
    root.bind_all('<Control-Prior>',lambda _event:cycle_tab(-1))
    root.hyuncalculator_cycle_tab=cycle_tab

    # Public GUI inspection handles for display smoke tests, not a network API.
    root.hyuncalculator_theme_choice=theme_choice
    root.hyuncalculator_size_choice=size_choice
    root.hyuncalculator_apply_preferences=apply_preferences
    refresh()
    apply_preferences(persist=False)
    if start_mainloop:
        root.mainloop()
    return root


class CodeGeneratorTab:
    """Formula registry browser + safe source preview/export (no code execution)."""
    def __init__(self, parent, language_getter):
        from .codegen import catalog, get_formula, generate, GenerationOptions, GenerationError, LANGUAGES
        self._catalog=catalog()
        self._get_formula=get_formula
        self._generate=generate
        self._options_type=GenerationOptions
        self._generation_error=GenerationError
        self.language_getter=language_getter
        self.frame=ttk.Frame(parent,padding=16)
        self.frame.columnconfigure(0,weight=1)
        self.frame.rowconfigure(8,weight=1)
        self.title=ttk.Label(self.frame,font=('Malgun Gothic',15,'bold'))
        self.title.grid(row=0,column=0,sticky='w')
        self.description=ttk.Label(self.frame,font=('Malgun Gothic',11))
        self.description.grid(row=1,column=0,sticky='w',pady=(0,12))
        top=ttk.Frame(self.frame);top.grid(row=2,column=0,sticky='ew',pady=(0,9))
        self.formula_items=[f'{f.id}  {f.title_en}' + ('  [Python only]' if len(f.supported_languages)==1 else '') for f in self._catalog]
        self.selected=tk.StringVar(value=self.formula_items[0])
        ttk.Label(top,text='Formula / 수식',font=('Malgun Gothic',11,'bold')).pack(side='left',padx=(0,8))
        selector=ttk.Combobox(top,textvariable=self.selected,values=self.formula_items,
                              width=65,state='readonly',font=('Malgun Gothic',11))
        selector.pack(side='left',fill='x',expand=True)
        selector.bind('<<ComboboxSelected>>',lambda _e:self._selection_changed())
        options=ttk.Frame(self.frame)
        options.grid(row=3,column=0,sticky='ew',pady=(0,9))
        self.target=tk.StringVar(value='Python')
        self.structure=tk.StringVar(value='function')
        self.loop=tk.StringVar(value='auto')
        self.imports=tk.StringVar(value='auto')
        self.variant=tk.StringVar(value='periodic')
        # Compact 3+2 grid prevents overflow at 175% text scale.
        option_items=[
            ('Language / 언어',self.target,LANGUAGES,13),
            ('Structure / 구조',self.structure,('function','class'),10),
            ('Iteration / 반복',self.loop,('auto','for','while'),9),
            ('Imports',self.imports,('auto','standard'),10),
            ('FV variant',self.variant,('periodic','continuous'),13),
        ]
        for i,(label,var,values,width) in enumerate(option_items):
            box=ttk.Frame(options)
            box.grid(row=i//3,column=i%3,sticky='w',padx=(0,18),pady=(0,8))
            ttk.Label(box,text=label).pack(anchor='w')
            ttk.Combobox(box,textvariable=var,values=values,state='readonly',
                         width=width).pack(anchor='w',pady=(4,0))
        fn_row=ttk.Frame(self.frame)
        fn_row.grid(row=4,column=0,sticky='ew',pady=(0,9))
        name_row=ttk.Frame(fn_row)
        name_row.pack(fill='x',pady=(0,6))
        ttk.Label(name_row,text='Function name / 함수명').pack(side='left',padx=(0,8))
        self.fn=tk.StringVar(value='fv')
        self.class_name=tk.StringVar(value='GeneratedCalculator')
        self.renames=tk.StringVar(value='')
        ttk.Entry(name_row,textvariable=self.fn,width=30,
                  font=('Consolas',12)).pack(side='left',padx=(0,10))
        action_row=ttk.Frame(fn_row)
        action_row.pack(fill='x')
        self.generate_btn=ttk.Button(action_row,command=self.preview)
        self.generate_btn.pack(side='left',padx=(0,8))
        self.copy_btn=ttk.Button(action_row,command=self.copy)
        self.copy_btn.pack(side='left',padx=(0,8))
        self.save_btn=ttk.Button(action_row,command=self.save)
        self.save_btn.pack(side='left',padx=(0,8))
        self.bundle_btn=ttk.Button(action_row,command=self.save_bundle)
        self.bundle_btn.pack(side='left',padx=(0,8))
        row=ttk.Frame(self.frame)
        row.grid(row=5,column=0,sticky='ew',pady=(0,8))
        class_row=ttk.Frame(row)
        class_row.pack(fill='x',pady=(0,6))
        ttk.Label(class_row,text='Class / 클래스명').pack(side='left',padx=(0,8))
        ttk.Entry(class_row,textvariable=self.class_name,width=25).pack(side='left')
        rename_row=ttk.Frame(row)
        rename_row.pack(fill='x')
        ttk.Label(rename_row,
                  text='Rename variables / 변수명 (e.g. pv=principal,rate=r)'
                  ).pack(side='left',padx=(0,8))
        ttk.Entry(rename_row,textvariable=self.renames,width=32
                  ).pack(side='left',fill='x',expand=True)

        self.formula_label=ttk.Label(self.frame,font=('Consolas',11))
        self.formula_label.grid(row=6,column=0,sticky='w',pady=(0,5))
        self.status=tk.StringVar(value='')
        ttk.Label(self.frame,textvariable=self.status,font=('Malgun Gothic',11),wraplength=1250).grid(row=7,column=0,sticky='w',pady=(0,6))
        preview_frame=ttk.Frame(self.frame)
        preview_frame.grid(row=8,column=0,sticky='nsew')
        preview_frame.columnconfigure(0,weight=1)
        preview_frame.rowconfigure(0,weight=1)
        self.code=tk.Text(preview_frame,wrap='none',font=('Consolas',13),height=22,
                          background='#102034',foreground='#E5F3FF',insertbackground='white',
                          relief='flat',padx=16,pady=12)
        self.code.grid(row=0,column=0,sticky='nsew')
        scrollbar=ttk.Scrollbar(preview_frame,orient='vertical',command=self.code.yview)
        scrollbar.grid(row=0,column=1,sticky='ns');self.code.configure(yscrollcommand=scrollbar.set)
        hscroll=ttk.Scrollbar(preview_frame,orient='horizontal',command=self.code.xview)
        hscroll.grid(row=1,column=0,sticky='ew');self.code.configure(xscrollcommand=hscroll.set)
        self.last_code=None;self.last_options=None
        self.target.trace_add('write', lambda *_: self._availability_changed())
        self._selection_changed()
        self.refresh_language()

    def _selection_changed(self):
        f=self._get_formula(self.selected.get().split()[0])
        self.fn.set({'fin_irr':'calculate_irr', 'qf_target':'target_portfolio'}.get(f.function, f.function.removeprefix('fin_').removeprefix('qf_')))
        self.renames.set('')
        self.loop.set('auto')
        self.variant.set('periodic')
        self.formula_label.configure(text=f'{f.id}: {f.formula}')
        self.last_code=None;self.last_options=None
        self.code.delete('1.0','end')
        self.copy_btn.configure(state='disabled')
        self.save_btn.configure(state='disabled');self.bundle_btn.configure(state='disabled')
        self._availability_changed()

    def _availability_changed(self):
        f=self._get_formula(self.selected.get().split()[0])
        language=self.target.get()
        available=language in f.supported_languages
        self.generate_btn.configure(state='normal' if available else 'disabled')
        self.copy_btn.configure(state='disabled')
        self.save_btn.configure(state='disabled');self.bundle_btn.configure(state='disabled')
        self.last_code=None;self.last_options=None
        self.code.delete('1.0','end')
        if available:
            self.status.set(f'{f.id}: {language} code generation available (not verified in-app).')
        else:
            self.status.set(f'{f.id}: {language} adapter is planned, not yet implemented. Available: {", ".join(f.supported_languages)}')

    def refresh_language(self):
        korean=self.language_getter()=='ko'
        self.title.configure(text='수학식 → 코드 생성 | Formula to Code' if korean else 'Formula to Code Generator')
        self.description.configure(text=('33개 수식 × 14개 언어 코드 생성 · 모든 코드의 실행 검증 완료를 의미하지 않음' if korean else
                                          '33 formulas × 14 languages · source generated, runtime verification pending'))
        self.generate_btn.configure(text='코드 생성' if korean else 'Generate')
        self.copy_btn.configure(text='복사' if korean else 'Copy')
        self.save_btn.configure(text='파일 저장' if korean else 'Save file')
        self.bundle_btn.configure(text='프로젝트 ZIP' if korean else 'Project ZIP')

    def preview(self):
        from .codegen.emitter import EXTENSIONS
        f=self._get_formula(self.selected.get().split()[0])
        try:
            mappings=[]
            if self.renames.get().strip():
                for part in self.renames.get().split(','):
                    if '=' not in part:raise self._generation_error('Use original_name=new_name, separated by commas')
                    source,destination=(x.strip() for x in part.split('=',1))
                    mappings.append((source,destination))
            opts=self._options_type(language=self.target.get(),structure=self.structure.get(),
                                iteration=self.loop.get(),imports=self.imports.get(),
                                variant=self.variant.get(),function_name=self.fn.get(),
                                class_name=self.class_name.get(),variable_names=tuple(mappings))
            code=self._generate(f.id,opts)
        except self._generation_error as exc:
            self.status.set(f'Unavailable / 미지원: {exc}')
            self.last_code=None;self.last_options=None
            self.copy_btn.configure(state='disabled');self.save_btn.configure(state='disabled');self.bundle_btn.configure(state='disabled')
            return
        self.last_code=code;self.last_options=opts
        self.code.delete('1.0','end');self.code.insert('1.0',code)
        self.status.set(f'Generated {len(code)} chars · {f.id} · {opts.language} · Compilation and numeric verification not performed in-app.')
        self.copy_btn.configure(state='normal');self.save_btn.configure(state='normal');self.bundle_btn.configure(state='normal')

    def copy(self):
        if self.last_code is not None:
            self.frame.clipboard_clear();self.frame.clipboard_append(self.last_code)

    def save_bundle(self):
        # Regenerate from current controls so stale previews can never be bundled.
        self.preview()
        if self.last_code is None or self.last_options is None:
            return
        from .codegen.bundle import bundle_bytes
        formula_id=self.selected.get().split()[0]
        target=filedialog.asksaveasfilename(title='Export standalone project ZIP',
                                             initialfile=f'{formula_id}_{self.target.get()}.zip',
                                             defaultextension='.zip',
                                             filetypes=[('ZIP archives','*.zip'),('All files','*.*')])
        if not target:
            return
        try:
            from pathlib import Path
            Path(target).write_bytes(bundle_bytes(formula_id,self.last_options))
            self.status.set('Project ZIP saved · source + examples + integrity tests. Numerical certification is not included.')
        except (OSError,self._generation_error) as exc:
            messagebox.showerror('ZIP export failed',str(exc))

    def save(self):
        if self.last_code is None:return
        from .codegen.emitter import EXTENSIONS
        extension=EXTENSIONS[self.target.get()]
        fn=self.fn.get()
        filename='GeneratedCalculator.java' if self.target.get()=='Java' else f'{fn}.{extension}'
        path=filedialog.asksaveasfilename(title='Export generated source',initialfile=filename,
                                           defaultextension=f'.{extension}',filetypes=[('Source code',f'*.{extension}'),('All files','*.*')])
        if path:
            try:
                with open(path,'w',encoding='utf-8') as out:out.write(self.last_code)
                self.status.set('Source saved locally. Run toolchain tests before using it in production.')
            except OSError as exc:
                messagebox.showerror('Export failed',str(exc))


class AboutTab:
    """Author details and a NON-ACTIVE sponsorship placeholder while pending review."""
    def __init__(self,parent,language_getter):
        self.language_getter=language_getter
        self.frame=ttk.Frame(parent,padding=32)
        self.frame.columnconfigure(0,weight=1)
        self.heading=ttk.Label(self.frame,font=('Malgun Gothic',18,'bold'))
        self.heading.grid(row=0,column=0,sticky='w',pady=(0,16))
        self.author=ttk.Label(self.frame,font=('Malgun Gothic',14))
        self.author.grid(row=1,column=0,sticky='w',pady=7)
        self.contact=ttk.Label(self.frame,font=('Consolas',13))
        self.contact.grid(row=2,column=0,sticky='w',pady=7)
        self.github=ttk.Label(self.frame,text='GitHub: https://github.com/HyunStudio/HyunCalculator',font=('Consolas',12))
        self.github.grid(row=3,column=0,sticky='w',pady=7)
        self.sponsors=ttk.Label(self.frame,font=('Malgun Gothic',13),wraplength=950)
        self.sponsors.grid(row=4,column=0,sticky='w',pady=(24,8))
        self.explain=ttk.Label(self.frame,font=('Malgun Gothic',11),wraplength=950)
        self.explain.grid(row=5,column=0,sticky='w',pady=6)
        self.refresh_language()

    def refresh_language(self):
        ko=self.language_getter()=='ko'
        self.heading.configure(text='제작자 및 후원 | About & Support' if ko else 'About & Support')
        self.author.configure(text='제작자: 황현기 (HyunGi Hwang)  |  HyunStudio' if ko else
                                    'Created by HyunGi Hwang (황현기)  |  HyunStudio')
        self.contact.configure(text='Contact: hyungi2344@gmail.com')
        self.sponsors.configure(text=('GitHub Sponsors: 승인 대기 (Pending) · 후원 결제 기능 비활성화' if ko else
                                      'GitHub Sponsors: pending approval · donations unavailable'))
        self.explain.configure(text=('GitHub Sponsors 프로필이 승인된 뒤에만 공식 후원 링크를 검증하여 활성화합니다. 현재는 후원 결제를 요청하지 않습니다.' if ko else
                                     'The official sponsorship link will only be enabled after the profile is approved and verified. No payment link is active.'))
