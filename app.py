from pathlib import Path
import json
import duckdb
import streamlit as st
from planning import pricing,commentary
ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='SaaS Finance Intelligence',layout='wide')
st.title('SaaS Finance Intelligence')
st.caption('Real SEC financials · explicit filing dates · forecasts and AI economics labeled separately')
if not (ROOT/'reports/model_inputs.json').exists(): st.info('Run fetch.py, model.py and planning.py first.'); st.stop()

@st.cache_data
def peers():
 with duckdb.connect(str(ROOT/'warehouse/finance.duckdb'),read_only=True) as db:
  return db.execute('select * from peer_metrics order by ticker,period_end').df()

df=peers(); ticker=st.sidebar.selectbox('Company',sorted(df.ticker.unique())); company=df[df.ticker==ticker]
latest=company.iloc[-1]; a,b,c=st.columns(3)
a.metric('Latest reported annual revenue',f"${latest.revenue/1e9:,.2f}bn")
b.metric('Operating margin',f"{latest.operating_margin:.1%}" if latest.operating_margin==latest.operating_margin else 'Unavailable')
c.metric('Fiscal year ended',str(latest.period_end.date()))
tabs=st.tabs(['Reported financials','Forecast evaluation','AI profitability assumptions','Source-linked commentary'])
with tabs[0]:
 st.line_chart(company.set_index('period_end')[['revenue','operating_income']])
 st.dataframe(company,hide_index=True)
 st.caption('Fiscal calendars differ. Annual revenue is GAAP revenue and must not be labeled ARR.')
with tabs[1]:
 st.json(json.loads((ROOT/'reports/backtest_summary.json').read_text()))
 st.caption('Historical rolling origins use only then-public filings. External forecast comparison; no internal company budget is claimed.')
 st.subheader('Salesforce planning cases'); st.dataframe(json.loads((ROOT/'reports/scenarios.json').read_text()))
 st.warning('Forward growth, cost and spending rates are illustrative assumptions, not company guidance. Cash shown is before financing and acquisitions.')
with tabs[2]:
 st.warning('All inputs below are user assumptions. Public filings do not disclose customer-level AI inference economics.')
 customers=st.number_input('Eligible accounts (assumption)',min_value=0,value=0,step=100)
 adoption=st.slider('Assumed adoption',0.,1.,.2)
 requests=st.number_input('Monthly requests per adopting account',min_value=0,value=0)
 x,y=st.columns(2)
 with x:
  tokens_in=st.number_input('Input tokens per request',min_value=0,value=0)
  rate_in=st.number_input('Input price, USD per million tokens',min_value=0.,value=0.)
  subscription=st.number_input('Monthly add-on price, USD',min_value=0.,value=0.)
 with y:
  tokens_out=st.number_input('Output tokens per request',min_value=0,value=0)
  rate_out=st.number_input('Output price, USD per million tokens',min_value=0.,value=0.)
  usage_price=st.number_input('Usage price, USD per request',min_value=0.,value=0.,format='%.4f')
 fixed=st.number_input('Incremental fixed monthly cost, USD',min_value=0.,value=0.)
 if customers and requests and tokens_in+tokens_out and rate_in+rate_out:
  st.dataframe(pricing(customers,adoption,requests,tokens_in,tokens_out,rate_in,rate_out,subscription,usage_price,fixed))
 else: st.info('Enter accounts, usage, tokens and rates to calculate pricing outcomes. Zero defaults are not real observations.')
with tabs[3]:
 packet=json.loads((ROOT/'reports/variance_evidence.json').read_text()); st.json(packet)
 if st.button('Generate verified AI observations'):
  try: st.json(commentary(packet))
  except Exception as e: st.error(str(e))
 with st.expander('Decision memo'): st.markdown((ROOT/'reports/decision_memo.md').read_text(encoding='utf-8'))
 st.download_button('Download financial facts and filing citations',(ROOT/'reports/annual_facts.csv').read_bytes(),'annual_facts.csv')
