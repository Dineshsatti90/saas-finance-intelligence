import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';

const root=path.dirname(fileURLToPath(import.meta.url));
const inputs=JSON.parse(await fs.readFile(path.join(root,'reports/model_inputs.json'),'utf8'));
const scenarios=JSON.parse(await fs.readFile(path.join(root,'reports/scenarios.json'),'utf8'));
const out=path.join(root,'outputs/saas-finance'); await fs.mkdir(out,{recursive:true});
const wb=Workbook.create();
const names=['Summary','Assumptions','Forecast','AI Pricing','ARR and Staffing','Actuals','Checks'];
const sheets=Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const fmt='#,##0.0,,"m";(#,##0.0,,"m");"–"';
const normal='#,##0;(#,##0);"–"';
function val(s,cell,v){s.getRange(cell).values=[[v]];}
function form(s,cell,v){s.getRange(cell).formulas=[[v]];s.getRange(cell).format.font.color=v.includes('!')?'#167347':'#172033';}
function label(s,cell,v){val(s,cell,v);}
function header(s,range){s.getRange(range).format={fill:'#243B5A',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:26};}
for(const [name,s] of Object.entries(sheets)){
 s.showGridLines=false;
 s.getRange('C2:K45').format={font:{name:'Arial',size:10,color:'#172033'},rowHeight:22,verticalAlignment:'center'};
 s.getRange('A1:B45').format.columnWidth=3;
 s.getRange('C2:C45').format.columnWidth=42;
 s.getRange('D2:G45').format.columnWidth=18;
 label(s,'C2',name==='Summary'?'SaaS financial planning':name);
 s.getRange('C2').format.font={name:'Arial',size:15,bold:true,color:'#172033'};
 if(!['Actuals','Assumptions'].includes(name)){
  label(s,'C4','Case selected:');form(s,'D4',"=Assumptions!E4");
  s.getRange('D4').format.font.color='#167347';
 }
}
sheets.Summary.tabColor='#243B5A';sheets.Assumptions.tabColor='#52729A';sheets.Actuals.tabColor='#E8D5BA';

const a=sheets.Actuals;
label(a,'C4',`Salesforce · year ended ${inputs.period_end} · USD`);
const rawMetrics=[['Revenue','revenue'],['Cost of revenue','cost_of_revenue'],['Gross profit','gross_profit'],
 ['Operating income','operating_income'],['Operating cash flow','operating_cash_flow'],['Capital expenditure','capex'],
 ['Cash and equivalents','cash'],['Research and development','research_development'],['Sales and marketing','sales_marketing'],['General and administrative','general_admin']];
a.getRange('C5:G5').values=[['Reported metric','USD','XBRL tag','Filed','Filing URL']];header(a,'C5:G5');
for(let i=0;i<rawMetrics.length;i++){
 const [name,key]=rawMetrics[i],r=6+i,source=inputs.sources[key];
 label(a,`C${r}`,name);val(a,`D${r}`,inputs.actuals[key]??null);
 val(a,`E${r}`,source?.tag??'Unavailable');val(a,`F${r}`,source?.filed??'');val(a,`G${r}`,source?.url??'');
}
a.getRange('D6:D15').setNumberFormat(fmt);a.getRange('D6:D15').format.font.color='#2457BC';
a.getRange('E5:E15').format.columnWidth=62;a.getRange('F5:F15').format.columnWidth=16;a.getRange('G5:G15').format.columnWidth=110;
label(a,'C18',`Source vintage cutoff: ${inputs.asof}`);
label(a,'C20','Full source population is stored in DuckDB and CSV exports.');

const assumptions=sheets.Assumptions;
label(assumptions,'C4','Case: 1 Base, 2 Downside');val(assumptions,'D4',1);
assumptions.getRange('D4').format={fill:'#FFF0C2',font:{color:'#2457BC'}};
assumptions.getRange('D4').dataValidation={rule:{type:'whole',operator:'between',formula1:1,formula2:2}};
form(assumptions,'E4','=CHOOSE(D4,"Base","Downside")');
label(assumptions,'C5','Forward rates are illustrative assumptions, not guidance.');
const year=Number(inputs.period_end.slice(0,4));
for(const [i,c] of ['E','F','G'].entries()) val(assumptions,`${c}6`,`${year+i+1}-01-31`);
header(assumptions,'C6:G6');
const drivers=[
 [8,'Revenue growth',inputs.planning_assumptions.base_growth,inputs.planning_assumptions.downside_growth],
 [12,'Cost of revenue / revenue',inputs.planning_assumptions.base_cogs_ratio,inputs.planning_assumptions.downside_cogs_ratio],
 [16,'Operating expense growth',inputs.planning_assumptions.base_opex_growth,inputs.planning_assumptions.downside_opex_growth],
 [20,'Operating cash flow / revenue',inputs.actuals.operating_cash_flow/inputs.actuals.revenue,inputs.actuals.operating_cash_flow/inputs.actuals.revenue-.03],
 [24,'Capital expenditure / revenue',inputs.actuals.capex/inputs.actuals.revenue,inputs.actuals.capex/inputs.actuals.revenue],
];
for(const [r,name,base,down] of drivers){
 label(assumptions,`C${r}`,name+' · active');label(assumptions,`C${r+1}`,'Base');label(assumptions,`C${r+2}`,'Downside');
 for(const c of ['E','F','G']){
  val(assumptions,`${c}${r+1}`,base);val(assumptions,`${c}${r+2}`,down);
  form(assumptions,`${c}${r}`,`=IF(CHOOSE($D$4,${c}${r+1},${c}${r+2})="","n.a.",CHOOSE($D$4,${c}${r+1},${c}${r+2}))`);
 }
 assumptions.getRange(`C${r}:G${r}`).format.fill='#EAF0F7';
 assumptions.getRange(`E${r}:G${r+2}`).setNumberFormat('0.0%');
 assumptions.getRange(`E${r+1}:G${r+2}`).format.font.color='#2457BC';
}

const f=sheets.Forecast;
label(f,'C5','USD millions · forecast cash excludes financing and acquisitions');
label(f,'D6',inputs.period_end+' A');
for(const [i,c] of ['E','F','G'].entries()) label(f,`${c}6`,`${year+i+1}-01-31 F`);
header(f,'C6:G6');
const labels={8:'Revenue',9:'Revenue growth',10:'Cost of revenue / revenue',11:'Cost of revenue',12:'Gross profit',13:'Gross margin',15:'Opening operating expense base',16:'Operating expense growth',17:'Operating expenses',18:'Operating income',20:'Operating cash flow / revenue',21:'Operating cash flow',22:'Capital expenditure / revenue',23:'Capital expenditure',24:'Free cash flow',26:'Opening cash and equivalents',27:'Cash before financing and acquisitions'};
for(const [r,name] of Object.entries(labels)) label(f,`C${r}`,name);
const hist={8:'Actuals!D6',10:'Actuals!D7/Actuals!D6',11:'Actuals!D7',12:'Actuals!D8',13:'D12/D8',17:'D8-D11-D18',18:'Actuals!D9',20:'Actuals!D10/Actuals!D6',21:'Actuals!D10',22:'Actuals!D11/Actuals!D6',23:'Actuals!D11',24:'D21-D23',27:'Actuals!D12'};
for(const [r,v] of Object.entries(hist)) form(f,`D${r}`,'='+v);
for(const [i,c] of ['E','F','G'].entries()){
 const prev=['D','E','F'][i];
 const formulas={9:`Assumptions!${c}8`,10:`Assumptions!${c}12`,16:`Assumptions!${c}16`,20:`Assumptions!${c}20`,22:`Assumptions!${c}24`,
 8:`IF(AND(ISNUMBER(${prev}8),ISNUMBER(${c}9)),${prev}8*(1+${c}9),"n.a.")`,
 11:`IF(AND(ISNUMBER(${c}8),ISNUMBER(${c}10)),${c}8*${c}10,"n.a.")`,
 12:`IF(AND(ISNUMBER(${c}8),ISNUMBER(${c}11)),${c}8-${c}11,"n.a.")`,
 13:`IF(AND(ISNUMBER(${c}12),ISNUMBER(${c}8)),IF(${c}8=0,"n.a.",${c}12/${c}8),"n.a.")`,
 15:`${prev}17`,17:`IF(AND(ISNUMBER(${c}15),ISNUMBER(${c}16)),${c}15*(1+${c}16),"n.a.")`,
 18:`IF(AND(ISNUMBER(${c}12),ISNUMBER(${c}17)),${c}12-${c}17,"n.a.")`,
 21:`IF(AND(ISNUMBER(${c}8),ISNUMBER(${c}20)),${c}8*${c}20,"n.a.")`,
 23:`IF(AND(ISNUMBER(${c}8),ISNUMBER(${c}22)),${c}8*${c}22,"n.a.")`,
 24:`IF(AND(ISNUMBER(${c}21),ISNUMBER(${c}23)),${c}21-${c}23,"n.a.")`,
 26:`${prev}27`,27:`IF(AND(ISNUMBER(${c}26),ISNUMBER(${c}24)),${c}26+${c}24,"n.a.")`};
 for(const [r,v] of Object.entries(formulas)) form(f,`${c}${r}`,'='+v);
}
f.getRange('D8:G27').setNumberFormat(fmt);
for(const r of [9,10,13,16,20,22]){f.getRange(`D${r}:G${r}`).setNumberFormat('0.0%');f.getRange(`C${r}:G${r}`).format.font.italic=true;}
for(const r of [8,12,18,24,27]){f.getRange(`C${r}:G${r}`).format.borders={bottom:{style:'thin',color:'#B7C5D5'}};f.getRange(`C${r}:G${r}`).format.font.bold=true;}

const p=sheets['AI Pricing'];label(p,'C5','Monthly USD · all inputs are assumptions; fill amber cells');
const plabels={7:'Eligible accounts',8:'Adoption rate',9:'Requests per adopting account',10:'Input tokens per request',11:'Output tokens per request',12:'Input USD per million tokens',13:'Output USD per million tokens',14:'Subscription add-on USD / month',15:'Usage price USD / request',16:'Incremental fixed monthly cost',18:'Adopting accounts',19:'Total monthly requests',20:'Inference cost USD / request',21:'Total monthly inference cost'};
for(const [r,name] of Object.entries(plabels)) label(p,`C${r}`,name);
p.getRange('D7:D16').format={fill:'#FFF0C2',font:{color:'#2457BC'}};
p.getRange('D7:D16').dataValidation={rule:{type:'decimal',operator:'greaterThanOrEqual',formula1:0}};
p.getRange('D8').dataValidation={rule:{type:'decimal',operator:'between',formula1:0,formula2:1}};
p.getRange('D8').setNumberFormat('0.0%');p.getRange('D12:D15').setNumberFormat('0.0000');
form(p,'D18','=IF(COUNT(D7:D8)=2,D7*D8,"n.a.")');
form(p,'D19','=IF(AND(ISNUMBER(D18),ISNUMBER(D9)),D18*D9,"n.a.")');
form(p,'D20','=IF(COUNT(D10:D13)=4,(D10*D12+D11*D13)/1000000,"n.a.")');
form(p,'D21','=IF(AND(ISNUMBER(D19),ISNUMBER(D20)),D19*D20,"n.a.")');
p.getRange('C24:G24').values=[['Pricing option','Incremental revenue','Inference cost','Contribution','Gross margin']];header(p,'C24:G24');
for(const [i,name] of ['Bundled','Subscription add-on','Usage-based'].entries()){
 const r=25+i; label(p,`C${r}`,name);
 const calc=i===0?'0':i===1?'$D$18*$D$14':'$D$19*$D$15';
 form(p,`D${r}`,`=IF(COUNT($D$7:$D$16)=10,${calc},"n.a.")`);
 form(p,`E${r}`,'=D21');
 form(p,`F${r}`,`=IF(AND(ISNUMBER(D${r}),ISNUMBER(E${r}),ISNUMBER($D$16)),D${r}-E${r}-$D$16,"n.a.")`);
 form(p,`G${r}`,`=IF(ISNUMBER(D${r}),IF(D${r}=0,"n.a.",(D${r}-E${r})/D${r}),"n.a.")`);
}
p.getRange('G25:G27').setNumberFormat('0.0%');p.getRange('D25:F27').setNumberFormat(normal);
label(p,'C30','Bundled feature revenue excludes retention and cross-sell benefits.');

const arr=sheets['ARR and Staffing'];label(arr,'C5','Inputs unavailable in public data; fill assumptions to activate');
for(const [i,c] of ['E','F','G'].entries()) label(arr,`${c}6`,`${year+i+1}-01-31 F`);header(arr,'C6:G6');
const arlabels={7:'Opening ARR',8:'New ARR',9:'Expansion ARR',10:'Contraction ARR (positive)',11:'Churn ARR (positive)',12:'Closing ARR',14:'Average recognized run rate proxy',19:'Opening paid FTE',20:'Hires (FTE)',21:'Exits (FTE, positive)',22:'Closing paid FTE',23:'Annual loaded cost / paid FTE',24:'Payroll expense proxy'};
for(const [r,name] of Object.entries(arlabels)) label(arr,`C${r}`,name);
for(const [i,c] of ['E','F','G'].entries()){
 const prev=['D','E','F'][i];
 for(const range of [`${c}8:${c}11`,`${c}20:${c}21`,`${c}23`]) arr.getRange(range).format={fill:'#FFF0C2',font:{color:'#2457BC'}};
 for(const range of [`${c}8:${c}11`,`${c}20:${c}21`,`${c}23`]) arr.getRange(range).dataValidation={rule:{type:'decimal',operator:'greaterThanOrEqual',formula1:0}};
 if(i===0){arr.getRange(`${c}7`).format.fill='#FFF0C2';arr.getRange(`${c}19`).format.fill='#FFF0C2';}
 else {form(arr,`${c}7`,`=IF(ISNUMBER(${prev}12),${prev}12,"n.a.")`);form(arr,`${c}19`,`=IF(ISNUMBER(${prev}22),${prev}22,"n.a.")`);}
 form(arr,`${c}12`,`=IF(COUNT(${c}7:${c}11)=5,${c}7+${c}8+${c}9-${c}10-${c}11,"n.a.")`);
 form(arr,`${c}14`,`=IF(AND(ISNUMBER(${c}7),ISNUMBER(${c}12)),(${c}7+${c}12)/2,"n.a.")`);
 form(arr,`${c}22`,`=IF(COUNT(${c}19:${c}21)=3,${c}19+${c}20-${c}21,"n.a.")`);
 form(arr,`${c}24`,`=IF(AND(ISNUMBER(${c}19),ISNUMBER(${c}22),ISNUMBER(${c}23)),(${c}19+${c}22)/2*${c}23,"n.a.")`);
}
arr.getRange('E7:G14').setNumberFormat(fmt);arr.getRange('E19:G22').setNumberFormat('0.0');arr.getRange('E23:G24').setNumberFormat(normal);
label(arr,'C27','ARR proxy uses average opening/closing run rate; not GAAP revenue.');
label(arr,'C29','Payroll assumes hires/exits spread evenly; no monthly proration.');
label(arr,'C31','These optional schedules do not overwrite reported financials.');

const s=sheets.Summary;label(s,'C5','Salesforce · USD millions · A actual / F forecast');
for(const c of ['D','E','F','G']) form(s,`${c}6`,`=Forecast!${c}6`);header(s,'C6:G6');
for(const [r,name,fr] of [[8,'Revenue',8],[10,'Operating income',18],[12,'Free cash flow',24],[14,'Cash before financing and acquisitions',27]]){
 label(s,`C${r}`,name);for(const c of ['D','E','F','G']) form(s,`${c}${r}`,`=Forecast!${c}${fr}`);
}
s.getRange('D8:G14').setNumberFormat(fmt);s.getRange('D8:G14').format.font.color='#172033';
label(s,'C17','Historical financials are SEC actuals. Forecast rates are assumptions.');
label(s,'C19','AI costs, ARR and staffing inputs require separate operating data.');
s.getRange('C22:E22').values=[['Period','Revenue USD','Op. income USD']];header(s,'C22:E22');
for(const [i,c] of ['D','E','F','G'].entries()){
 const r=23+i;form(s,`C${r}`,`=Forecast!${c}6`);form(s,`D${r}`,`=Forecast!${c}8`);form(s,`E${r}`,`=Forecast!${c}18`);
}
s.getRange('D23:E26').setNumberFormat(fmt);s.getRange('D23:E26').format.font.color='#172033';
const chart=s.charts.add('bar',s.getRange('C22:E26'));chart.title='Revenue and operating income (USD millions)';chart.setPosition('I6','R23');
chart.titleTextStyle.typeface='Arial';chart.titleTextStyle.fontSize=12;
chart.yAxis={numberFormatCode:'0,,"m"',numberFormatSourceLinked:false,textStyle:{typeface:'Arial'}};

const check=sheets.Checks;check.getRange('C6:G6').values=[['Reconciliation','Actual','Year 1','Year 2','Year 3']];header(check,'C6:G6');
label(check,'C8','Gross profit: revenue less costs');label(check,'C10','Operating income: gross profit less opex');label(check,'C12','Free cash flow: OCF less capex');
for(const c of ['D','E','F','G']){
 form(check,`${c}8`,`=Forecast!${c}8-Forecast!${c}11-Forecast!${c}12`);
 form(check,`${c}10`,`=Forecast!${c}12-Forecast!${c}17-Forecast!${c}18`);
 form(check,`${c}12`,`=Forecast!${c}21-Forecast!${c}23-Forecast!${c}24`);
}
check.getRange('D8:G12').setNumberFormat('0.00');check.getRange('D8:G12').format.font.color='#172033';
check.getRange('D8:G12').conditionalFormats.addCustom('ABS(D8)>0.01',{fill:'#FDE7E7',font:{color:'#B42318',bold:true}});
label(check,'C16','Missing ARR/AI inputs remain n.a.; no historical inputs invented.');

wb.recalculate();
// Verify active-case and later-period recalculation, restore every changed input.
const initial=f.getRange('E8').values[0][0];
assumptions.getRange('D4').values=[[2]];wb.recalculate();
const downside=f.getRange('E8').values[0][0];
if(Math.abs(downside-scenarios[1].revenue)>.01) throw new Error('Downside formula mismatch');
assumptions.getRange('D4').values=[[1]];const later=assumptions.getRange('G9').values[0][0];assumptions.getRange('G9').values=[[.2]];wb.recalculate();
if(f.getRange('G8').values[0][0]===f.getRange('F8').values[0][0]*1.1) throw new Error('Later-period driver did not update');
assumptions.getRange('G9').values=[[later]];wb.recalculate();
if(Math.abs(f.getRange('E8').values[0][0]-initial)>.01) throw new Error('Base restoration failed');
if(Math.abs(initial-scenarios[0].revenue)>.01) throw new Error('Python/Excel forecast mismatch');
if(p.getRange('D25').values[0][0]!=='n.a.') throw new Error('Missing pricing input was treated as zero');
// A missing unselected case must not contaminate the active case.
const saved=assumptions.getRange('E10').values[0][0];assumptions.getRange('E10').values=[[null]];wb.recalculate();
if(f.getRange('E8').values[0][0]!==initial) throw new Error('Unselected blank contaminated base');
assumptions.getRange('D4').values=[[2]];wb.recalculate();
if(f.getRange('E8').values[0][0]!=='n.a.') throw new Error('Selected blank not exposed');
assumptions.getRange('E10').values=[[saved]];assumptions.getRange('D4').values=[[1]];wb.recalculate();
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},summary:'Formula error scan'});
await fs.writeFile(path.join(out,'verification.json'),JSON.stringify({base_revenue:initial,downside_revenue:downside,
 checks:check.getRange('D8:G12').values,formula_scan:errors.ndjson,engine:'artifact-tool; native Excel not exercised'},null,2));
for(const name of names){
 const preview=await wb.render({sheetName:name,range:name==='Summary'?'C2:R27':name==='Actuals'?'C2:F20':'C2:G32',scale:1,format:'png'});
 await fs.writeFile(path.join(out,name.replaceAll(' ','_')+'.png'),new Uint8Array(await preview.arrayBuffer()));
}
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(out,'saas_financial_planning.xlsx'));
console.log(JSON.stringify({output:path.join(out,'saas_financial_planning.xlsx'),base_revenue:initial,downside_revenue:downside,formula_errors:errors.ndjson}));
