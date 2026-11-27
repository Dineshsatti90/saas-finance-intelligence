from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def test_public_finance_demo_without_database():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    assert app.metric[0].value == "$41.52bn"
    next(x for x in app.selectbox if x.label == "Company").select("SNOW").run()
    assert not app.exception


def test_pricing_changes_and_zero_adoption():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    next(x for x in app.slider if x.label == "Assumed adoption").set_value(0.0).run()
    assert not app.exception
    assert any("No adopting accounts" in x.value for x in app.info)
    next(x for x in app.slider if x.label == "Assumed adoption").set_value(0.2).run()
    next(x for x in app.number_input if x.label == "Requests per adopting account per month").set_value(
        4000
    ).run()
    assert not app.exception
    assert (
        next(x for x in app.metric if x.label == "Add-on monthly contribution break-even").value == "$37.00"
    )


def test_independent_adoption_controls_change_the_right_policy():
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    next(x for x in app.selectbox if x.label == "Flat add-on adoption loss").select(0.2).run()
    assert not app.exception
    assert next(x for x in app.metric if x.label == "Stressed flat contribution").value == "$4,400"
    assert next(x for x in app.metric if x.label == "Stressed metered contribution").value == "$8,000"
    next(x for x in app.selectbox if x.label == "Metered adoption loss").select(0.2).run()
    assert next(x for x in app.metric if x.label == "Stressed metered contribution").value == "$4,400"
