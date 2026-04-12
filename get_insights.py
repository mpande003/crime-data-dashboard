import pandas as pd
import glob
import json

insights = {}

for f in glob.glob("*.csv"):
    df = pd.read_csv(f)
    name = f
    num_cols = df.select_dtypes(include='number').columns.tolist()
    cat_cols = df.select_dtypes(exclude='number').columns.tolist()
    
    # drop ID and similar non-metric num cols
    metrics = [c for c in num_cols if c not in ['id', 'year', 'state_code', 'district_code']]
    
    stats = {}
    if 'state_name' in df.columns and len(metrics) > 0:
        top_state = df.groupby('state_name')[metrics[0]].sum().idxmax()
        stats['top_state'] = top_state
    
    if len(metrics) > 0:
        stats['total_metric_1'] = df[metrics[0]].sum()
        
    insights[name] = {
        'rows': len(df),
        'cols': df.shape[1],
        'num_metrics': len(metrics),
        'cat_cols': cat_cols,
        'stats': stats,
        'missing_vals': int(df.isnull().sum().sum()),
        'years': df['year'].unique().tolist() if 'year' in df.columns else []
    }

print(json.dumps(insights, indent=2))
