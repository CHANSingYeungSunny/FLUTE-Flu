import json, os
R = r"c:\Users\Asus\Desktop\FYP code\MLFlu"
reg = json.load(open(os.path.join(R, "results", "v3_clean", "runs",
                                  "complete_specs_amended.json"), encoding="utf-8"))
specs = reg["specs"]
print("total specs:", len(specs))
rows = [s for s in specs if s.get("wave") == 2 and s.get("submittable")
        and s.get("executable_binding")]
rows.sort(key=lambda s: s["order"])
print("wave2 submittable+executable rows:", len(rows))
for s in rows:
    print(json.dumps({
        "order": s["order"], "run_key": s["run_key"], "model": s["model"],
        "arm": s["arm"], "horizon": s["horizon"], "seed": s.get("seed"),
        "wave": s.get("wave"), "control": s.get("control"),
        "parent_model": s.get("parent_model"),
        "amended_action": s.get("amended_action"),
    }, ensure_ascii=False))
