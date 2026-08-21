import run_evaluation as r
def test_normalize(): assert r.n(" High ")=="high"
def test_yes(): assert r.yn("Yes") is True
def test_no(): assert r.yn("No") is False
def test_metrics_accuracy():
    rs=[{"case_accuracy":1.0,"false_positive":False,"missed_change":False,"control_mapping_correct":True,"human_review_correct":True,"overall_status":"Pass"}]
    assert r.metrics(rs)["overall_accuracy"]==1.0
def test_false_positive():
    row={"case_id":"X","expected_change_type":"no_change","ai_change_type":"addition","expected_control":"None","ai_control":"Policy","expected_impact":"Low","ai_impact":"Medium","expected_human_review":"No","ai_human_review":"Yes"}
    assert r.evaluate(row)["false_positive"] is True
