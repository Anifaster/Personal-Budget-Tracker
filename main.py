from datetime import date
from pathlib import Path
from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, RoundedRectangle
from models import TransactionType, parse_date
from ledger import Ledger
from storage import JsonStorage
from calculations import balance, total, totals_by_category, monthly_summary, filter_transactions, list_categories

BG=(.055,.085,.14,1); PANEL=(.10,.15,.23,1); WHITE=(.94,.96,1,1); TEAL=(.12,.65,.56,1); RED=(1,.40,.43,1)
Window.clearcolor=BG
Window.softinput_mode='below_target'

def stack(**kw):
    return BoxLayout(orientation='vertical', spacing=dp(9), **kw)
def label(text, height=32, size=15, color=WHITE):
    w=Label(text=str(text), size_hint_y=None, height=dp(height), font_size=dp(size), color=color, halign='left', valign='middle')
    w.bind(size=lambda obj,val: setattr(obj,'text_size',val))
    return w
def button(text, cb, color=PANEL):
    b=Button(text=text, size_hint_y=None,height=dp(46),background_normal='',background_color=color,color=WHITE,font_size=dp(15)); b.bind(on_release=cb); return b
def field(hint, value=''):
    return TextInput(text=value,hint_text=hint,multiline=False,size_hint_y=None,height=dp(45),padding=[dp(10),dp(11)],font_size=dp(16))
def money(n): return f'KRW {n:,.2f}'

class BudgetApp(App):
    title='Personal Budget Tracker'
    def build(self):
        self.store=JsonStorage(Path(self.user_data_dir)/'budget_data.json')
        self.blocked=False
        try: self.ledger=Ledger(self.store.load())
        except Exception as e:
            self.ledger=Ledger(); self.blocked=True; self.load_error=str(e)
        self.rootbox=stack(padding=dp(14))
        self.rootbox.add_widget(label('PERSONAL BUDGET',36,22))
        self.body=stack(); self.rootbox.add_widget(self.body)
        nav=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(5))
        for name, fn in [('Home',self.home),('Add',self.form),('History',self.history),('Stats',self.stats)]: nav.add_widget(button(name,lambda _,f=fn:f()))
        self.rootbox.add_widget(nav)
        self.home()
        return self.rootbox
    def page(self,title):
        self.body.clear_widgets(); self.body.add_widget(label(title,35,23))
        scroll=ScrollView(do_scroll_x=False); content=stack(size_hint_y=None,padding=[0,0,0,dp(12)]); content.bind(minimum_height=content.setter('height')); scroll.add_widget(content); self.body.add_widget(scroll); return content
    def notice(self,msg):
        b=stack(padding=dp(12)); l=Label(text=str(msg),halign='center',valign='middle'); l.bind(size=lambda o,v:setattr(o,'text_size',v)); b.add_widget(l); p=Popup(title='Budget Tracker',content=b,size_hint=(.9,.52)); b.add_widget(button('OK',lambda _:p.dismiss(),TEAL)); p.open()
    def commit(self,candidate):
        if self.blocked: raise ValueError('Storage could not be loaded. Existing file is protected; do not overwrite it.')
        self.store.save(candidate.transactions); self.ledger=candidate
    def home(self):
        c=self.page('Overview'); tx=self.ledger.transactions
        if self.blocked: c.add_widget(label('Data load failed. Saving disabled.',55,14,RED)); c.add_widget(button('Error details',lambda _:self.notice(self.load_error)))
        c.add_widget(label('ALL-TIME BALANCE',28,13)); c.add_widget(label(money(balance(tx)),55,27,TEAL if balance(tx)>=0 else RED))
        c.add_widget(label('Income   '+money(total(tx,TransactionType.INCOME)),44,17,TEAL)); c.add_widget(label('Expenses   '+money(total(tx,TransactionType.EXPENSE)),44,17,RED))
        c.add_widget(button('+ New transaction',lambda _:self.form(),TEAL)); c.add_widget(label('Recent transactions',38,19))
        for t in reversed(tx[-5:]): c.add_widget(label(f'{t.category}  |  {money(t.signed_amount)}\n{t.date}',59,15))
        if not tx: c.add_widget(label('No transactions yet. Add your first one.',56))
    def form(self,t=None):
        c=self.page('Edit transaction' if t else 'New transaction'); typ=Spinner(text=t.type.value if t else 'expense',values=('expense','income'),size_hint_y=None,height=dp(45)); c.add_widget(label('Type')); c.add_widget(typ)
        amount=field('e.g. 150000',str(t.amount) if t else ''); cat=field('e.g. Food, Rent, Salary',t.category if t else ''); d=field('YYYY-MM-DD',str(t.date) if t else date.today().isoformat()); desc=field('Optional note',t.description if t else '')
        for title,w in [('Amount (KRW; no commas)',amount),('Category',cat),('Date',d),('Description',desc)]: c.add_widget(label(title)); c.add_widget(w)
        def save(_):
            try:
                candidate=Ledger(self.ledger.transactions)
                if t: candidate.remove(t.id)
                candidate.add(TransactionType(typ.text),amount.text,cat.text,parse_date(d.text),desc.text)
                self.commit(candidate); self.home()
            except Exception as e: self.notice(e)
        c.add_widget(button('Save transaction',save,TEAL)); c.add_widget(button('Cancel',lambda _:self.home()))
    def history(self):
        c=self.page('Transactions'); kind=Spinner(text='All types',values=('All types','income','expense'),size_hint_y=None,height=dp(43)); category=Spinner(text='All categories',values=['All categories']+list_categories(self.ledger.transactions),size_hint_y=None,height=dp(43)); start=field('From YYYY-MM-DD (optional)'); end=field('To YYYY-MM-DD (optional)')
        for w in (kind,category,start,end): c.add_widget(w)
        records=stack(size_hint_y=None); records.bind(minimum_height=records.setter('height'))
        def refresh(*_):
            try:
                a=parse_date(start.text) if start.text.strip() else None; b=parse_date(end.text) if end.text.strip() else None
                if a and b and a>b: raise ValueError('Start date must not follow end date.')
                tx=filter_transactions(self.ledger.transactions,category=None if category.text=='All categories' else category.text,tx_type=None if kind.text=='All types' else TransactionType(kind.text),start=a,end=b)
            except Exception as e: self.notice(e); return
            records.clear_widgets(); records.add_widget(label(f'{len(tx)} records | Net {money(balance(tx))}',45,14))
            for t in reversed(tx):
                records.add_widget(label(f'{t.category} | {money(t.signed_amount)}\n{t.date}  {t.description}',62,15,TEAL if t.type is TransactionType.INCOME else WHITE))
                row=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(6)); row.add_widget(button('Edit',lambda _,x=t:self.form(x))); row.add_widget(button('Delete',lambda _,x=t:self.delete(x))); records.add_widget(row)
        c.add_widget(button('Apply filters',refresh,TEAL)); c.add_widget(records); refresh()
    def delete(self,t):
        content=stack(padding=dp(10)); content.add_widget(label('Delete this transaction?',45)); p=Popup(title='Confirm deletion',content=content,size_hint=(.9,.32))
        def yes(_):
            try:
                candidate=Ledger(self.ledger.transactions); candidate.remove(t.id); self.commit(candidate); p.dismiss(); self.history()
            except Exception as e: p.dismiss(); self.notice(e)
        content.add_widget(button('Delete',yes,RED)); content.add_widget(button('Cancel',lambda _:p.dismiss())); p.open()
    def stats(self):
        c=self.page('Spending insights'); tx=self.ledger.transactions; c.add_widget(label('Expenses by category',40,19)); cats=totals_by_category(tx,TransactionType.EXPENSE); maxval=max(cats.values(),default=1)
        for name,v in cats.items():
            c.add_widget(label(f'{name}  |  {money(v)}',30)); c.add_widget(ProgressBar(max=100,value=float(v/maxval*100),size_hint_y=None,height=dp(16)))
        if not cats: c.add_widget(label('No expenses recorded.'))
        c.add_widget(label('Monthly summary',44,19))
        for month,m in reversed(list(monthly_summary(tx).items())): c.add_widget(label(f'{month}\nIncome: {money(m.income)}\nExpenses: {money(m.expenses)}\nNet: {money(m.net)}',100,15))
    def on_pause(self): return True

if __name__=='__main__': BudgetApp().run()
