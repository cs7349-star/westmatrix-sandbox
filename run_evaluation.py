import csv,json
from pathlib import Path

def n(x): return (x or "").strip().lower()
def yn(x): return n(x)=="yes"

def evaluate(row):
    c=n(row["expected_change_type"])==n(row["ai_change_type"])
    m=n(row["expected_control"])==n(row["ai_control"])
    i=n(row["expected_impact"])==n(row["ai_impact"])
    h=yn(row["expected_human_review"])==yn(row["ai_human_review"])
    exp=n(row["expected_change_type"])!="no_change"
    ai=n(row["ai_change_type"])!="no_change"
    fp=(not exp) and ai
    miss=exp and (not ai)
    score=sum([c,m,i,h])/4
    return {"case_id":row["case_id"],"change_type_correct":c,"control_mapping_correct":m,"impact_correct":i,"human_review_correct":h,"false_positive":fp,"missed_change":miss,"case_accuracy":round(score,4),"overall_status":"Pass" if score>=0.75 else ("Warning" if score>=0.5 else "Fail")}

def metrics(rs):
    k=len(rs)
    return {
      "total_scenarios":k,
      "overall_accuracy":round(sum(r["case_accuracy"] for r in rs)/k,4),
      "false_positive_rate":round(sum(r["false_positive"] for r in rs)/k,4),
      "missed_change_rate":round(sum(r["missed_change"] for r in rs)/k,4),
      "control_mapping_accuracy":round(sum(r["control_mapping_correct"] for r in rs)/k,4),
      "human_review_accuracy":round(sum(r["human_review_correct"] for r in rs)/k,4),
      "pass_count":sum(r["overall_status"]=="Pass" for r in rs),
      "warning_count":sum(r["overall_status"]=="Warning" for r in rs),
      "fail_count":sum(r["overall_status"]=="Fail" for r in rs)
    }

rows=list(csv.DictReader(open("data/test_scenarios.csv",encoding="utf-8")))
rs=[evaluate(r) for r in rows]
Path("output").mkdir(exist_ok=True)
with open("output/evaluation_results.csv","w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=rs[0].keys()); w.writeheader(); w.writerows(rs)
m=metrics(rs)
Path("output/performance_metrics.json").write_text(json.dumps(m,indent=2),encoding="utf-8")
print(json.dumps(m,indent=2))
