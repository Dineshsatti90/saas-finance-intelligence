"""Point-in-time annual normalization, out-of-sample planning and factual bridges."""
from pathlib import Path
from datetime import date
import argparse
import csv
import json
import duckdb
from fetch import PEERS
ROOT=Path(__file__).resolve().parent

TAGS={
 'revenue':['RevenueFromContractWithCustomerExcludingAssessedTax','Revenues','SalesRevenueNet'],
 'cost_of_revenue':['CostOfRevenue','CostOfGoodsAndServicesSold','CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization'],
 'gross_profit':['GrossProfit'],
 'operating_income':['OperatingIncomeLoss'],
 'research_development':['ResearchAndDevelopmentExpense'],
 'sales_marketing':['SellingAndMarketingExpense'],
 'general_admin':['GeneralAndAdministrativeExpense'],
 'operating_cash_flow':['NetCashProvidedByUsedInOperatingActivities'],
 'capex':['PaymentsToAcquirePropertyPlantAndEquipment'],
 'cash':['CashAndCashEquivalentsAtCarryingValue'],
}

def filing_url(cik,accn):
 return f'https://www.sec.gov/Archives/edgar/data/{cik}/{accn.replace("-","")}/{accn}-index.html'

def annual_facts(ticker,asof='2026-11-26'):
 data=json.loads((ROOT/'data/raw'/(ticker+'.json')).read_text(encoding='utf-8'))
 gaap=data.get('facts',{}).get('us-gaap',{})
 records=[]
 for metric,tags in TAGS.items():
  candidates=[]
  for priority,tag in enumerate(tags):
   for f in gaap.get(tag,{}).get('units',{}).get('USD',[]):
    if f.get('form')!='10-K' or f.get('filed','9999')>asof or 'end' not in f: continue
    duration=(date.fromisoformat(f['end'])-date.fromisoformat(f['start'])).days if f.get('start') else None
    if metric=='cash':
     if duration is not None: continue
    elif duration is None or not 300<=duration<=380: continue
    if f['end']<'2015-01-01': continue
    candidates.append({**f,'tag':tag,'priority':priority})
  by_end={}
  for f in candidates: by_end.setdefault(f['end'],[]).append(f)
  for end,options in by_end.items():
   # Latest available filing vintage, then preferred accounting tag; never mix USD/shares.
   selected=sorted(options,key=lambda x:(-date.fromisoformat(x['filed']).toordinal(),x['priority'],x['accn']))[0]
   records.append({'ticker':ticker,'metric':metric,'period_end':end,'value':selected['val'],
    'filed':selected['filed'],'accn':selected['accn'],'tag':selected['tag'],
    'source_url':filing_url(PEERS[ticker],selected['accn']),'asof':asof})
 return records

def write_csv(path,rows):
 if not rows: return
 with path.open('w',newline='',encoding='utf-8') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)

def build(asof='2026-11-26'):
 (ROOT/'warehouse').mkdir(exist_ok=True); (ROOT/'reports').mkdir(exist_ok=True)
 db=duckdb.connect(str(ROOT/'warehouse/finance.duckdb'))
 counts={}
 for name in ['sub','num','tag','pre']:
  path=(ROOT/'data/raw'/(name+'.txt')).as_posix().replace("'","''")
  db.execute(f"create or replace table sec_{name} as select * from read_csv('{path}',delim='\t',header=true,all_varchar=true,quote='',strict_mode=true)")
  counts[name]=db.execute(f'select count(*) from sec_{name}').fetchone()[0]
 if counts['num']<1000000: raise ValueError('Expected full million-plus numeric population')
 raw_facts=0
 for ticker in PEERS:
  data=json.loads((ROOT/'data/raw'/(ticker+'.json')).read_text())
  raw_facts+=sum(len(values) for concept in data['facts'].values() for fact in concept.values() for values in fact.get('units',{}).values())
 counts['company_facts_observations']=raw_facts
 # Profile the full population rather than merely downloading unused large files.
 coverage=db.execute('''select s.form,count(distinct n.adsh) as filings,count(*) as numeric_records,
 count(distinct s.cik) as filers,count(distinct n.tag) as distinct_tags
 from sec_num n join sec_sub s on n.adsh=s.adsh group by 1 order by numeric_records desc''').df()
 coverage.to_csv(ROOT/'reports/population_coverage.csv',index=False)
 db.execute('''create or replace table population_annual_revenue as
 select s.cik,s.name,s.form,s.filed,n.adsh,n.tag,n.ddate,n.value
 from sec_num n join sec_sub s on n.adsh=s.adsh
 where s.form='10-K' and n.qtrs='4' and n.uom='USD' and coalesce(n.coreg,'')=''
 and n.tag in ('RevenueFromContractWithCustomerExcludingAssessedTax','Revenues','SalesRevenueNet')''')
 path=(ROOT/'reports/population_annual_revenue.csv').as_posix()
 db.execute(f"copy population_annual_revenue to '{path}' (header)")
 records=[r for ticker in PEERS for r in annual_facts(ticker,asof)]
 write_csv(ROOT/'reports/annual_facts.csv',records)
 path=(ROOT/'reports/annual_facts.csv').as_posix()
 db.execute(f"create or replace table annual_facts as select * from read_csv('{path}',header=true)")
 # Revenue and matching financial-year-end metrics. Different peer fiscal calendars stay explicit.
 db.execute('''create or replace table annual_financials as
 select ticker,period_end,
 max(value) filter(where metric='revenue') as revenue,
 max(value) filter(where metric='cost_of_revenue') as cost_of_revenue,
 max(value) filter(where metric='gross_profit') as gross_profit,
 max(value) filter(where metric='operating_income') as operating_income,
 max(value) filter(where metric='operating_cash_flow') as operating_cash_flow,
 max(value) filter(where metric='capex') as capex,
 max(value) filter(where metric='cash') as cash
 from annual_facts group by 1,2 having max(value) filter(where metric='revenue') is not null''')
 db.execute('''create or replace table peer_metrics as
 select *, revenue/lag(revenue) over(partition by ticker order by period_end)-1 as revenue_growth,
 coalesce(gross_profit,revenue-cost_of_revenue)/revenue as gross_margin,
 operating_income/revenue as operating_margin,
 (operating_cash_flow-capex)/revenue as fcf_margin
 from annual_financials''')
 for table in ['annual_financials','peer_metrics']:
  path=(ROOT/'reports'/(table+'.csv')).as_posix()
  db.execute(f"copy (select * from {table} order by ticker,period_end) to '{path}' (header)")
 db.close()
 (ROOT/'reports/row_counts.json').write_text(json.dumps(counts,indent=2))
 backtest(asof)
 create_model_inputs(asof)
 print(json.dumps(counts,indent=2))

def backtest(asof):
 rows=[]
 for ticker in PEERS:
  final=[r for r in annual_facts(ticker,asof) if r['metric']=='revenue']
  final.sort(key=lambda x:x['period_end'])
  # At each origin, use only filings that were public on that date.
  for prior,target in zip(final,final[1:]):
   # Original publication date for the prior year, not a future restatement.
   all_data=json.loads((ROOT/'data/raw'/(ticker+'.json')).read_text())['facts']['us-gaap']
   filings=[x for tag in TAGS['revenue'] for x in all_data.get(tag,{}).get('units',{}).get('USD',[])
    if x.get('form')=='10-K' and x.get('end')==prior['period_end'] and x.get('start')
    and 300<=(date.fromisoformat(x['end'])-date.fromisoformat(x['start'])).days<=380]
   if not filings: continue
   origin=min(x['filed'] for x in filings)
   history=sorted([r for r in annual_facts(ticker,origin) if r['metric']=='revenue' and r['period_end']<=prior['period_end']],key=lambda x:x['period_end'])
   if len(history)<3 or target['period_end']<=origin: continue
   recent=history[-3:]+[target]
   if any(not 300<=(date.fromisoformat(b['period_end'])-date.fromisoformat(a['period_end'])).days<=380 for a,b in zip(recent,recent[1:])): continue
   # No future values in growth rate: prior two reported annual changes, median via average of two.
   last=history[-1]['value']; growths=[history[-1]['value']/history[-2]['value']-1,history[-2]['value']/history[-3]['value']-1]
   growth=max(-.5,min(1.,sum(growths)/2))
   for name,prediction in [('flat_revenue',last),('trailing_growth',last*(1+growth))]:
    rows.append({'ticker':ticker,'origin_filed':origin,'target_period_end':target['period_end'],
     'method':name,'forecast':prediction,'actual':target['value'],
     'absolute_error':abs(prediction-target['value']),'absolute_percentage_error':abs(prediction-target['value'])/target['value']})
 write_csv(ROOT/'reports/backtest.csv',rows)
 summary={}
 for method in ['flat_revenue','trailing_growth']:
  r=[x for x in rows if x['method']==method]
  summary[method]={'observations':len(r),'mape':sum(x['absolute_percentage_error'] for x in r)/len(r),
   'wape':sum(x['absolute_error'] for x in r)/sum(x['actual'] for x in r)} if r else {'observations':0}
 (ROOT/'reports/backtest_summary.json').write_text(json.dumps(summary,indent=2))

def create_model_inputs(asof):
 records=annual_facts('CRM',asof)
 by_end={}
 for r in records: by_end.setdefault(r['period_end'],{})[r['metric']]=r
 valid=[(end,m) for end,m in by_end.items() if all(k in m for k in ['revenue','operating_income','operating_cash_flow','capex','cash']) and ('cost_of_revenue' in m or 'gross_profit' in m)]
 end,m=max(valid,key=lambda x:x[0]); revenue=m['revenue']['value']
 cogs=m['cost_of_revenue']['value'] if 'cost_of_revenue' in m else revenue-m['gross_profit']['value']
 # Historical actuals remain actuals. AI/customer/ARR inputs deliberately unavailable.
 inputs={'company':'Salesforce','ticker':'CRM','asof':asof,'period_end':end,'currency':'USD',
  'actuals':{k:v['value'] for k,v in m.items()},'cost_of_revenue':cogs,
  'sources':{k:{'url':v['source_url'],'tag':v['tag'],'filed':v['filed'],'period_end':v['period_end']} for k,v in m.items()},
  'planning_assumptions':{'base_growth':.10,'downside_growth':.04,'base_cogs_ratio':cogs/revenue,
   'downside_cogs_ratio':min(.99,cogs/revenue+.02),'base_opex_growth':.08,'downside_opex_growth':.06},
  'unavailable_actuals':['ARR','new ARR','expansion ARR','churn ARR','customer count','AI inference cost','internal budget','paid FTE']}
 (ROOT/'reports/model_inputs.json').write_text(json.dumps(inputs,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('--asof',default='2026-11-26'); a=p.parse_args(); build(a.asof)
