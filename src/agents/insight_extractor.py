import pandas as pd
import numpy as np
from typing import List
from ..models import Insight


def extract_basic_insights(df: pd.DataFrame, max_insights: int = 6) -> List[Insight]:
    insights = []
    # Numeric column summaries
    for col in df.select_dtypes(include=[np.number]).columns:
        ser = df[col].dropna()
        if ser.empty:
            continue
        summary = f"Mean {ser.mean():.2f}, median {ser.median():.2f}, std {ser.std():.2f}."
        details = {
            "count": int(ser.count()),
            "min": float(ser.min()),
            "max": float(ser.max()),
        }
        insights.append(Insight(title=f"Numeric: {col}", summary=summary, details=details))
        if len(insights) >= max_insights:
            return insights

    # Categorical/text summaries (top values)
    for col in df.select_dtypes(include=[object]).columns:
        ser = df[col].dropna().astype(str)
        if ser.empty:
            continue
        top = ser.value_counts().nlargest(3)
        summary = f"Top values: {', '.join([f'{v} ({n})' for v, n in top.items()])}."
        insights.append(Insight(title=f"Categorical: {col}", summary=summary, details={"top": top.to_dict()}))
        if len(insights) >= max_insights:
            return insights

    return insights
