# SD-008 Fraud Intelligence dashboard

The dashboard is a read-only Streamlit layer over D2 analyst-facing exports. It never loads latent simulator state or row-level `Y_true` values.

## Run

```powershell
python -m pip install -r requirements.txt
cd deliverables/D2_Synthetic_Dataset_Generator
python -m sd008_gen.generate --config config/scenario_v0.yaml --out ../../outputs --profile BASELINE --seed 20261101
cd ../..
$env:SD008_DATA_DIR = "outputs"
streamlit run dashboard/app.py
```

The sidebar accepts either a generated `run_<seed>_<hash>` directory or its parent. Use a 150K BASELINE export for normal interaction; the interface aggregates charts and paginates the explorer rather than transmitting all rows to the browser. STRESS runs are supported but should be stored locally.

## Scope and limits

Scenario Lab and Simulation Quality read the versioned aggregate evidence under `docs/qa/evidence/`. Those internal QA statistics are clearly separated from analyst-facing records. This is a synthetic educational workspace, not a production fraud system or external banking validation.
