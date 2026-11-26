"""Public finance dashboard runs directly from the committed report extracts."""

from pathlib import Path
import json

import pandas as pd
import streamlit as st

from planning import pricing, scenario

ROOT = Path(__file__).resolve().parent


def read_json(name: str) -> dict:
    return json.loads((ROOT / "reports" / name).read_text(encoding="utf-8-sig"))


def main() -> None:
    st.set_page_config(page_title="SaaS Finance Intelligence", layout="wide")
    st.title("SaaS financial planning & AI product economics")
    st.caption(
        "Reported SEC financials | point-in-time annual forecasts | separate illustrative operating assumptions"
    )
    frame = pd.read_csv(ROOT / "reports/peer_metrics.csv", parse_dates=["period_end"]).sort_values(
        ["ticker", "period_end"]
    )
    ticker = st.sidebar.selectbox(
        "Company", sorted(frame.ticker.unique()), index=sorted(frame.ticker.unique()).index("CRM")
    )
    st.sidebar.write(
        "This demo uses committed public financial extracts. No warehouse or API key is required."
    )
    st.sidebar.link_button(
        "Source & methodology", "https://github.com/Dineshsatti90/saas-finance-intelligence"
    )
    company = frame[frame.ticker == ticker]
    latest = company.iloc[-1]
    one, two, three = st.columns(3)
    one.metric("Reported annual revenue", f"${latest.revenue / 1e9:,.2f}bn")
    two.metric(
        "Operating margin",
        f"{latest.operating_margin:.1%}" if pd.notna(latest.operating_margin) else "Unavailable",
    )
    three.metric("Fiscal year ended", str(latest.period_end.date()))
    tabs = st.tabs(
        ["Reported financials", "Forecast evidence", "Illustrative AI pricing", "Decision & AI record"]
    )
    with tabs[0]:
        st.subheader("Revenue and operating income, USD")
        st.line_chart(company.set_index("period_end")[["revenue", "operating_income"]])
        st.dataframe(company, hide_index=True, width="stretch")
        st.caption("Fiscal year ends differ across peers. Revenue is GAAP revenue, not ARR.")
        st.download_button(
            "Download editable Excel model",
            (ROOT / "outputs/saas-finance/saas_financial_planning.xlsx").read_bytes(),
            "saas_financial_planning.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with tabs[1]:
        study = read_json("driver_backtest_summary.json")
        st.subheader("Same-target annual forecast comparison")
        comparison = pd.DataFrame(study["methods"]).T.reset_index(names="method")
        st.dataframe(comparison, hide_index=True, width="stretch")
        st.bar_chart(comparison.set_index("method")["wape"], horizontal=True)
        st.info(study["recommendation"])
        st.caption(
            "40 paired targets; expanding-window training uses only labels public at the origin. Fixed ridge penalty; no test-set tuning."
        )
        case = st.selectbox("Salesforce forward financial case", ["base", "downside"])
        result = scenario(read_json("model_inputs.json"), case)
        st.dataframe([result], hide_index=True, width="stretch")
        st.warning(
            "Cash is a limited pre-financing accumulation, not a projected cash balance. It excludes acquisitions, investments, financing, repurchases and FX."
        )
    with tabs[2]:
        st.subheader("IllustrativeCo — fictional operating case")
        st.caption(
            "Inputs are assumed, not disclosed company customer/ARR/AI bills. Token rates are scenario inputs, not current provider quotations."
        )
        source = json.loads((ROOT / "inputs/illustrative_case.json").read_text(encoding="utf-8"))["pricing"]
        left, right = st.columns(2)
        with left:
            customers = st.number_input("Eligible accounts", min_value=1, value=source["customers"], step=100)
            adoption = st.slider("Assumed adoption", 0.0, 1.0, source["adoption"])
            requests = st.number_input(
                "Requests per adopting account per month", min_value=1, value=source["requests"]
            )
            tokens_in = st.number_input("Input tokens per request", min_value=0, value=source["input_tokens"])
            rate_in = st.number_input(
                "Input USD per million tokens", min_value=0.0, value=float(source["input_rate"])
            )
        with right:
            tokens_out = st.number_input(
                "Output tokens per request", min_value=0, value=source["output_tokens"]
            )
            rate_out = st.number_input(
                "Output USD per million tokens", min_value=0.0, value=float(source["output_rate"])
            )
            subscription = st.number_input(
                "Monthly add-on price, USD", min_value=0.0, value=source["subscription"] * 1.0
            )
            usage_price = st.number_input(
                "Usage price, USD per request", min_value=0.0, value=source["usage_price"], format="%.4f"
            )
            fixed = st.number_input(
                "Incremental fixed monthly cost, USD", min_value=0.0, value=float(source["fixed_cost"])
            )
        outcomes = pd.DataFrame(
            pricing(
                customers,
                adoption,
                requests,
                tokens_in,
                tokens_out,
                rate_in,
                rate_out,
                subscription,
                usage_price,
                fixed,
            )
        )
        st.dataframe(outcomes, hide_index=True, width="stretch")
        st.bar_chart(outcomes.set_index("strategy")["contribution"], horizontal=True)
        active = customers * adoption
        if active:
            break_even = (outcomes.iloc[0].inference_cost + fixed) / active
            st.metric("Add-on monthly contribution break-even", f"${break_even:.2f}")
        else:
            st.info("No adopting accounts: break-even price per adopter is unavailable; fixed costs remain.")
    with tabs[3]:
        st.markdown((ROOT / "reports/pricing_decision.md").read_text(encoding="utf-8"))
        with st.expander("Recorded, verified local-model output"):
            st.json(read_json("ai_commentary.json"))
        with st.expander("AI contract evaluation, including failures"):
            report = read_json("ai_evaluation.json")
            st.json({k: v for k, v in report.items() if k != "results"})
        st.caption("These are saved model runs. The public dashboard does not expose a paid model endpoint.")


if __name__ == "__main__":
    main()
